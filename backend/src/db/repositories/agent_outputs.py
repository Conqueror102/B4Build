"""Store per-phase agent outputs (phase_worker results mirror)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentOutput

# FullPlan field name -> graph phase_id
_FIELD_PHASE: tuple[tuple[str, str], ...] = (
    ("pressure_test", "phase_0"),
    ("problem_model_fit", "phase_1"),
    ("architecture", "phase_2"),
    ("build_buy_train", "phase_3"),
    ("infrastructure", "phase_4"),
    ("cost_model", "phase_5"),
    ("security", "phase_6_25"),
    ("observability", "phase_6_5"),
    ("scaling", "phase_7"),
)


class AgentOutputsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_for_version(
        self,
        *,
        plan_id: uuid.UUID,
        plan_version_id: uuid.UUID,
        full_plan_json: dict,
        default_model: str = "gpt-4o-mini",
    ) -> None:
        for field, phase_id in _FIELD_PHASE:
            payload = full_plan_json.get(field)
            if payload is None:
                continue
            self.session.add(
                AgentOutput(
                    plan_id=plan_id,
                    plan_version_id=plan_version_id,
                    phase_id=phase_id,
                    output_json=payload if isinstance(payload, dict) else {"value": payload},
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=Decimal("0"),
                    latency_ms=0,
                    model=default_model,
                )
            )
        await self.session.flush()
