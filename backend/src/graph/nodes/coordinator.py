"""Coordinator node - decides what to do next.

The coordinator is the brain of the graph: it inspects the running
``AdvisorState`` and either (a) sets ``current_phase`` to the next missing
phase or (b) signals that the phase loop is complete so the graph can route
to ``red_team`` and ``synthesizer``.

To keep things simple in Phase 1, routing is deterministic Python (no LLM
call). The ``conversation_handler`` and clarifying-question logic is what
actually invokes the LLM.
"""

from __future__ import annotations

from typing import Any

from ...logging_config import get_logger
from ...prompts import PHASE_ORDER
from ..phase_ids import normalize_phase_list, to_canonical_phase_id
from ..state import AdvisorState

logger = get_logger(__name__)


def _next_missing_phase(state: AdvisorState) -> str | None:
    """Return the next phase id that has not produced output yet."""
    outputs = state.get("phase_outputs", {}) or {}
    meta = state.get("metadata", {}) or {}
    effective_order = normalize_phase_list(meta.get("active_phase_order") or PHASE_ORDER, default_order=PHASE_ORDER)
    if not effective_order:
        effective_order = list(PHASE_ORDER)

    for phase_id in effective_order:
        if phase_id not in outputs:
            return phase_id
    return None


def _intake_complete(state: AdvisorState) -> bool:
    """Heuristic: do we have enough context to start running phases?"""
    answers = state.get("clarifying_answers") or {}
    idea = state.get("idea", "")
    return bool(answers) or len(idea) > 80


async def coordinator_node(state: AdvisorState) -> dict[str, Any]:
    """Set ``current_phase`` based on what's missing or what's dirty."""
    request_id = state.get("metadata", {}).get("request_id", "unknown")

    # Only check intake completion if we don't have a plan yet
    # If final_plan exists OR we have phase outputs, skip the clarify gate
    # This prevents re-asking clarifying questions when the user is iterating on an existing plan
    has_plan = state.get("final_plan") is not None
    has_phases = bool(state.get("phase_outputs", {}))
    
    if not has_plan and not has_phases and not _intake_complete(state):
        logger.info("coordinator.routing", request_id=request_id, decision="clarify")
        return {"current_phase": "clarify"}

    # If final_plan exists, we are in Phase 4 (Iteration Layer)
    if has_plan:
        # Check if the user just sent a message that hasn't been classified yet
        # We know it hasn't been classified if the latest intent isn't handled.
        # Actually, if we just arrived here from API chat, current_phase is None,
        # and there's a new user message. Let's look at `metadata.intent_classification`.

        dirty = state.get("dirty_phases", [])
        if dirty:
            nxt_raw = dirty[0]
            nxt = to_canonical_phase_id(nxt_raw) or nxt_raw

            # Intercept phase_4/phase_5 to run researcher first
            last_researched = state.get("metadata", {}).get("last_researched_phase")
            if nxt in ("phase_4", "phase_5") and last_researched != nxt:
                logger.info("coordinator.routing", request_id=request_id, decision="research", phase=nxt)
                meta = dict(state.get("metadata", {}) or {})
                meta["last_researched_phase"] = nxt
                return {"current_phase": "research", "metadata": meta}

            # If normalization failed, drop it instead of routing to an unknown phase.
            if nxt not in PHASE_ORDER:
                logger.warning("coordinator.dirty_phase_unknown", request_id=request_id, phase=nxt_raw)
                return {"dirty_phases": dirty[1:], "current_phase": None}

            logger.info("coordinator.routing", request_id=request_id, decision="rerun_dirty", phase=nxt)
            return {"current_phase": nxt, "dirty_phases": dirty[1:]}  # Pop the first

        intent_metadata = state.get("metadata", {}).get("intent_classification")
        if not intent_metadata:
            # New message arrived, no intent yet. Route to conversation_handler to classify.
            logger.info("coordinator.routing", request_id=request_id, decision="iterate")
            return {"current_phase": "iterate"}

        intent_str = intent_metadata.get("intent")

        # If it's just a chat or challenge, we don't resynthesize, we reply.
        if intent_str in ("challenge", "chat", "clarify_response", "deep_dive"):
            # If the responder already ran, intent_metadata will be cleared or we need a way to stop.
            # Actually, the responder node should clear the intent_metadata or we need a handled flag.
            if intent_metadata.get("handled"):
                logger.info("coordinator.routing", request_id=request_id, decision="chat_done")
                return {"current_phase": None}

            logger.info("coordinator.routing", request_id=request_id, decision="respond", intent=intent_str)
            return {"current_phase": "respond"}

        # If we have intent_metadata and no dirty phases, we finished re-running the phases!
        # Now we need to route to synthesizer to rebuild the final plan
        # but only if it was an edit/what_if and it hasn't been synthesized yet.
        # We can mark it handled by having synthesizer set `intent_metadata["handled"] = True`.
        if intent_metadata.get("handled"):
            logger.info("coordinator.routing", request_id=request_id, decision="iteration_done")
            return {"current_phase": None}

        logger.info("coordinator.routing", request_id=request_id, decision="resynthesize")
        return {"current_phase": "resynthesize"}

    nxt = _next_missing_phase(state)
    if nxt is None:
        logger.info("coordinator.routing", request_id=request_id, decision="phases_done")
        return {"current_phase": None}

    # Intercept phase_4/phase_5 to run researcher first
    last_researched = state.get("metadata", {}).get("last_researched_phase")
    if nxt in ("phase_4", "phase_5") and last_researched != nxt:
        logger.info("coordinator.routing", request_id=request_id, decision="research", phase=nxt)
        meta = dict(state.get("metadata", {}) or {})
        meta["last_researched_phase"] = nxt
        return {"current_phase": "research", "metadata": meta}

    logger.info("coordinator.routing", request_id=request_id, decision="run_phase", phase=nxt)
    return {"current_phase": nxt}


def coordinator_route(state: AdvisorState) -> str:
    """Edge function that picks the next node name."""
    cp = state.get("current_phase")
    if cp in ("clarify", "iterate"):
        return "conversation_handler"
    if cp == "respond":
        return "chat_responder"
    if cp == "research":
        return "researcher"
    if cp is None:
        return "red_team"
    if cp == "resynthesize":
        return "synthesizer"
    return "phase_worker"
