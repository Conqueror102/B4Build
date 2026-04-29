"""POST /api/chat - run the advisor graph and stream SSE (Postgres + LangGraph checkpointer)."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .. import store
from ..db.bootstrap import ensure_default_user_exists
from ..db.repositories.agent_outputs import AgentOutputsRepository
from ..db.repositories.conversations import ConversationsRepository
from ..db.repositories.plans import PlansRepository
from ..db.repositories.spend import SpendRepository
from ..db.session import get_session
from ..graph import build_graph
from ..llm import usage_context
from ..logging_config import get_logger
from ..prompts import PHASE_REGISTRY
from ..schemas.chat import ChatRequest
from ..schemas.plan import FullPlan
from ..services.checkpointing import get_checkpointer
from ..services.rate_limit import user_chat_limiter
from ..settings import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


def _sse(event: str, data: dict[str, Any], phase_id: str | None = None) -> str:
    payload = {"event": event, "phase_id": phase_id, "data": data}
    # Send proper SSE frames so the frontend parser sees `message.event`.
    # (eventsource-parser ignores messages without an `event:` line.)
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


def _serialize_phase_output(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def _title_from_idea(idea: str) -> str:
    first = (idea or "").strip().split("\n", 1)[0].strip()
    return (first[:120] + "…") if len(first) > 120 else (first or "Untitled plan")


def _parse_plan_uuid(s: str | None) -> uuid.UUID | None:
    if s is None or s.strip() == "":
        return None
    t = s.strip()
    if t.startswith("plan_") and "plan_" in t:  # legacy: plan_<12 hex> — not a real UUID; ignore
        return None
    try:
        return uuid.UUID(t)
    except (ValueError, TypeError, AttributeError):
        return None


async def _run_graph_stream(
    req: ChatRequest,
    *,
    plan_u: uuid.UUID,
) -> AsyncIterator[str]:
    request_id = uuid.uuid4().hex
    token = usage_context.set_active_plan_id(plan_u)
    graph = build_graph()

    # Determine which phases are active for this run. Keep canonical ids in the backend.
    from ..graph.phase_ids import normalize_phase_list
    from ..prompts import PHASE_ORDER

    active_phase_order = normalize_phase_list(
        req.active_phase_order or PHASE_ORDER, default_order=PHASE_ORDER
    ) or list(PHASE_ORDER)

    # Send only the updates to the state: the new user message and metadata
    state_update: dict[str, Any] = {
        "messages": [{"role": "user", "content": req.idea}],
        "metadata": {
            "request_id": request_id,
            "plan_id": str(plan_u),
            "active_phase_order": active_phase_order,
        },
    }

    # If the user is starting a brand new plan, we need to initialize `idea` as well.
    # We will check if it's new by looking at whether the checkpointer has state.
    # Actually, we can just pass it; LangGraph will replace it for string types without Annotated.
    state_update["idea"] = req.idea

    if req.clarifying_answers:
        state_update["metadata"]["clarifying_answers"] = req.clarifying_answers

    cp = get_checkpointer()
    run_config: dict[str, Any] = {"configurable": {"thread_id": str(plan_u)}}

    seen_phase_ids: set[str] = set()
    it = (
        graph.astream(state_update, run_config, stream_mode="updates")
        if cp is not None
        else graph.astream(state_update, stream_mode="updates")
    )

    try:
        async for update in it:
            for _node_name, partial in (update or {}).items():
                if not isinstance(partial, dict):
                    continue

                new_outputs = partial.get("phase_outputs")
                if isinstance(new_outputs, dict):
                    for pid, val in new_outputs.items():
                        if pid in seen_phase_ids:
                            continue
                        seen_phase_ids.add(pid)
                        title = PHASE_REGISTRY[pid].title if pid in PHASE_REGISTRY else pid
                        yield _sse("phase_start", {"title": title}, phase_id=pid)
                        yield _sse(
                            "phase_complete",
                            {"title": title, "output": _serialize_phase_output(val)},
                            phase_id=pid,
                        )

                metadata = partial.get("metadata")
                if (
                    _node_name == "conversation_handler"
                    and isinstance(metadata, dict)
                    and "clarifying_questions" in metadata
                ):
                    yield _sse("clarify", {"questions": metadata["clarifying_questions"]})

                red_team = partial.get("red_team")
                if red_team is not None and _node_name == "red_team":
                    yield _sse("red_team", {"critique": _serialize_phase_output(red_team)})

                final_plan = partial.get("final_plan")
                if final_plan is not None and _node_name == "synthesizer":
                    if not isinstance(final_plan, FullPlan):
                        plan_model = FullPlan.model_validate(final_plan)
                    else:
                        plan_model = final_plan
                    actual_id = str(plan_u)
                    plan_model = plan_model.model_copy(update={"plan_id": actual_id})
                    plan_dict = plan_model.model_dump(mode="json")

                    try:
                        async with get_session() as session:
                            plans = PlansRepository(session)

                            # Get previous version to compute diff
                            old_plan = await plans.get_latest_full_plan(plan_u)
                            old_dict = old_plan.model_dump(mode="json") if old_plan else {}

                            from ..services.diff_engine import diff_dicts

                            plan_diff = diff_dicts(old_dict, plan_dict)
                            if plan_diff:
                                yield _sse("diff", {"diff": plan_diff})

                            pver = await plans.add_plan_version(
                                plan_id=plan_u,
                                full_plan_json=plan_dict,
                                red_team_json=plan_model.red_team.model_dump(mode="json"),
                            )
                            await plans.update_status(plan_u, "complete")
                            # Agent outputs are non-critical to version creation; don't fail the whole
                            # persist step if they error.
                            try:
                                agents = AgentOutputsRepository(session)
                                await agents.replace_for_version(
                                    plan_id=plan_u,
                                    plan_version_id=pver.id,
                                    full_plan_json=plan_dict,
                                )
                            except Exception:
                                logger.exception("agent_outputs.persist_failed", plan_id=actual_id)
                            # Update store so subsequent requests hit the cache
                            store.put(plan_model)
                    except Exception:
                        logger.exception("plan.persist_failed")
                    yield _sse("synthesizer", {"plan_id": actual_id})
                    yield _sse("done", {"plan_id": actual_id, "plan": plan_dict})
                    return

                errors = partial.get("errors")
                if errors:
                    last_err = errors[-1]
                    yield _sse("error", {"message": last_err}, phase_id=_node_name)

                # Yield chat_responder responses
                if _node_name == "chat_responder":
                    new_msgs = partial.get("messages", [])
                    if new_msgs:
                        assistant_msg = new_msgs[-1]["content"]

                        # Save assistant response to database
                        try:
                            async with get_session() as session:
                                conv = ConversationsRepository(session)
                                await conv.add_turn(
                                    plan_id=plan_u,
                                    role="assistant",
                                    content=assistant_msg,
                                    intent=None,
                                )
                        except Exception as e:
                            logger.error(
                                "chat.save_assistant_message_failed",
                                plan_id=str(plan_u),
                                error=str(e),
                            )

                        yield _sse("chat_reply", {"message": assistant_msg})
                        yield _sse("done", {"plan_id": str(plan_u), "plan": None})
                        return

    except asyncio.CancelledError:
        # Client disconnected or server is shutting down (e.g. reload). Let the
        # graph/checkpointer unwind as cleanly as possible.
        logger.info("chat.stream_cancelled", request_id=request_id)
        raise
    except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
        # Database connection issues (common with Neon serverless)
        logger.error(
            "chat.db_connection_failed",
            request_id=request_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        yield _sse(
            "error",
            {
                "message": "Database connection lost. Please refresh and try again.",
                "details": "The database connection was closed unexpectedly. This can happen with serverless databases.",
            },
        )
    except Exception as exc:
        logger.exception("chat.stream_failed", request_id=request_id, error=str(exc))
        yield _sse("error", {"message": f"stream failed: {exc}"})
    finally:
        usage_context.reset_active_plan_id(token)


@router.post("/chat", response_model=None)
async def chat(req: ChatRequest, request: Request) -> StreamingResponse | JSONResponse:
    settings = get_settings()
    lim = user_chat_limiter()
    ukey = f"user:{settings.default_local_user_id}"
    if not lim.is_allowed(
        ukey,
        max_events=settings.api_rate_limit_per_user_per_minute,
        window_seconds=60.0,
    ):
        return JSONResponse(
            status_code=429, content={"detail": "rate_limited", "code": "rate_limited"}
        )

    cap = Decimal(str(settings.daily_openai_spend_cap))
    async with get_session() as session:
        sp = SpendRepository(session)
        if not await sp.is_under_cap(cap):
            logger.info("cost_cap_exceeded", cap_usd=str(cap))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Daily OpenAI spend cap reached. Try again tomorrow or raise the cap.",
                    "code": "cost_cap_exceeded",
                },
            )

    plan_parsed = _parse_plan_uuid(req.plan_id)
    plan_u = uuid.uuid4() if plan_parsed is None else plan_parsed

    async with get_session() as session:
        uu = uuid.UUID(settings.default_local_user_id)
        # This is normally done in app startup, but keep this defensive in case
        # the database was reset. In tests (SQLite), UUID typing can differ, so
        # don't fail the whole request if seeding is skipped.
        try:
            await ensure_default_user_exists(uu, email="local-dev@advisor.local")
        except Exception as exc:
            logger.warning("default_user_seed_skipped", error=str(exc))
        plans = PlansRepository(session)
        existing = await plans.get_plan(plan_u)
        if existing is None:
            await plans.create_plan(
                title=_title_from_idea(req.idea),
                idea_summary=req.idea,
                user_id=uu,
                plan_id=plan_u,
            )
        elif existing.user_id is not None and existing.user_id != uu:
            return JSONResponse(status_code=403, content={"detail": "forbidden"})

        conv = ConversationsRepository(session)
        await conv.add_turn(plan_id=plan_u, role="user", content=req.idea, intent="chat")

    async def gen() -> AsyncIterator[bytes]:
        try:
            # Echo the active phase list so the UI can render the right phase tabs/progress.
            from ..graph.phase_ids import normalize_phase_list
            from ..prompts import PHASE_ORDER

            active_phase_order = normalize_phase_list(
                req.active_phase_order or PHASE_ORDER, default_order=PHASE_ORDER
            ) or list(PHASE_ORDER)

            yield _sse(
                "init",
                {"plan_id": str(plan_u), "active_phase_order": active_phase_order},
            ).encode("utf-8")
            await asyncio.sleep(0)
            # /plan/new intentionally aborts after receiving "init" just to get a plan_id.
            # If the client already disconnected, don't start the LangGraph run at all.
            if await request.is_disconnected():
                logger.info("chat.client_disconnected_after_init", plan_id=str(plan_u))
                return
            async for chunk in _run_graph_stream(req, plan_u=plan_u):
                if await request.is_disconnected():
                    logger.info("chat.client_disconnected", plan_id=str(plan_u))
                    raise asyncio.CancelledError
                yield chunk.encode("utf-8")
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            # Stop streaming quietly when the client disconnects.
            return

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
