"""GET .../export.pdf and legacy .../pdf - download a plan as PDF (ReportLab)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from .. import store
from ..db.repositories.plans import PlansRepository
from ..db.session import get_session
from ..services.pdf import render_plan_pdf

router = APIRouter(prefix="/api", tags=["export"])


async def _get_plan_for_export(plan_id: str):
    from ..schemas.plan import FullPlan

    try:
        pid = uuid.UUID(plan_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="invalid plan id") from e

    async with get_session() as session:
        repo = PlansRepository(session)
        fp = await repo.get_latest_full_plan(pid)
    if fp is not None:
        return fp
    plan = store.get(plan_id) or store.get(str(pid))
    if plan is None:
        raise HTTPException(status_code=404, detail=f"plan not found: {plan_id}")
    if not isinstance(plan, FullPlan):
        return FullPlan.model_validate(plan)
    return plan


@router.get("/plan/{plan_id}/export.pdf")
@router.get("/plans/{plan_id}/pdf", include_in_schema=False)
@router.get("/plan/{plan_id}/export")
async def export_plan_pdf(plan_id: str) -> Response:
    """Return ``FullPlan`` as a PDF (binary ``application/pdf``)."""
    from ..schemas.plan import FullPlan

    p = await _get_plan_for_export(plan_id)
    if not isinstance(p, FullPlan):
        p = FullPlan.model_validate(p)
    pdf_bytes = render_plan_pdf(p)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="plan-{plan_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )
