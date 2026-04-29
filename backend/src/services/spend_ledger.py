"""Record OpenAI spend: daily_aggregates + per-plan when a plan is active in context."""

from __future__ import annotations

from decimal import Decimal

from ..db.repositories.plans import PlansRepository
from ..db.repositories.spend import SpendRepository
from ..db.session import get_session
from ..llm import usage_context
from ..logging_config import get_logger

logger = get_logger(__name__)


async def record_openai_spend_from_llm(
    cost_usd: float,
) -> None:
    """Called after a successful OpenAI request with estimated actual cost in USD."""
    d = Decimal(str(round(cost_usd, 6)))
    if d <= 0:
        d = Decimal("0")

    plan_id = usage_context.get_active_plan_id()
    try:
        async with get_session() as session:
            spend = SpendRepository(session)
            await spend.record_call(d)
            if plan_id is not None:
                plans = PlansRepository(session)
                await plans.add_cost(plan_id, d)
    except Exception as exc:
        logger.warning(
            "spend.record_failed", error=str(exc), plan_id=str(plan_id) if plan_id else None
        )
