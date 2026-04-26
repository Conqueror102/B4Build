"""GET /api/plan/{id}, GET /api/plans - load plans from Postgres."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .. import store
from ..db.models import Plan
from ..db.repositories.plans import PlansRepository
from ..db.session import get_session
from ..schemas.chat import PlanListResponse, PlanResponse, PlanSummary

router = APIRouter(prefix="/api", tags=["plan"])


def _plan_to_summary(p: Plan) -> PlanSummary:
    return PlanSummary(
        id=str(p.id),
        title=p.title,
        status=p.status,
        total_cost_usd=float(p.total_cost_usd or 0),
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    )


@router.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str) -> PlanResponse:
    """Return the latest version of a plan, or 404 if missing."""
    try:
        pid = uuid.UUID(plan_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="invalid plan id") from e

    # First try to get the full plan from database
    async with get_session() as session:
        repo = PlansRepository(session)
        plan_model = await repo.get_latest_full_plan(pid)
    
    if plan_model is not None:
        return PlanResponse(plan=plan_model)
    
    # Fall back to in-memory store (for plans in progress)
    p = store.get(plan_id)
    if p is None:
        p = store.get(str(pid))
    
    if p is not None:
        return PlanResponse(plan=p)
    
    # If not in store, check if plan exists in DB but just doesn't have a version yet
    # This happens during initial plan creation before any phases complete
    async with get_session() as session:
        repo = PlansRepository(session)
        plan_record = await repo.get_plan(pid)
        
        if plan_record is not None:
            # Return a minimal plan structure indicating it's in progress
            from ..schemas.plan import FullPlan
            minimal_plan = FullPlan(
                plan_id=str(plan_record.id),
                title=plan_record.title,
                idea=plan_record.idea_summary,
                total_cost_usd=float(plan_record.total_cost_usd or 0),
            )
            return PlanResponse(plan=minimal_plan)
    
    raise HTTPException(status_code=404, detail=f"plan not found: {plan_id}")


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    user_id: str | None = Query(
        default=None, description="Stub user id (defaults to local dev user)"
    ),
) -> PlanListResponse:
    from ..settings import get_settings

    s = get_settings()
    uu: uuid.UUID | None = None
    if user_id is not None:
        try:
            uu = uuid.UUID(user_id)
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail="invalid user_id") from e
    else:
        uu = uuid.UUID(s.default_local_user_id)
    async with get_session() as session:
        repo = PlansRepository(session)
        plans = await repo.list_plans_for_user(uu, limit=100)
    return PlanListResponse(plans=[_plan_to_summary(p) for p in plans])


@router.get("/plan/{plan_id}/versions")
async def list_versions(plan_id: str) -> dict[str, Any]:
    """Return a list of versions for a given plan."""
    try:
        pid = uuid.UUID(plan_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="invalid plan id") from e

    async with get_session() as session:
        repo = PlansRepository(session)
        versions = await repo.list_versions(pid)

    return {
        "versions": [
            {
                "id": str(v.id),
                "version_num": v.version_num,
                "notes": v.notes,
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in versions
        ]
    }


@router.get("/plan/{plan_id}/conversation")
async def get_conversation(plan_id: str) -> dict[str, Any]:
    """Return the conversation history for a given plan."""
    try:
        pid = uuid.UUID(plan_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="invalid plan id") from e

    async with get_session() as session:
        from ..db.repositories.conversations import ConversationsRepository
        repo = ConversationsRepository(session)
        turns = await repo.list_turns_for_plan(pid)

    return {
        "messages": [
            {
                "id": str(t.id),
                "role": t.role,
                "content": t.content,
                "intent": t.intent,
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
            for t in turns
        ]
    }
