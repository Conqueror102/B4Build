"""Plans + PlanVersions repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.plan import FullPlan
from ..models import Plan, PlanVersion


class PlansRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_plan(
        self,
        *,
        title: str,
        idea_summary: str,
        user_id: uuid.UUID | None = None,
        plan_id: uuid.UUID | None = None,
    ) -> Plan:
        plan = Plan(
            id=plan_id or uuid.uuid4(),
            title=title,
            idea_summary=idea_summary,
            user_id=user_id,
            status="in_progress",
        )
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_plan(self, plan_id: uuid.UUID) -> Plan | None:
        return await self.session.get(Plan, plan_id)

    async def get_latest_full_plan(self, plan_id: uuid.UUID) -> FullPlan | None:
        plan = await self.get_plan(plan_id)
        if plan is None or plan.current_version_id is None:
            return None
        ver = await self.session.get(PlanVersion, plan.current_version_id)
        if ver is None:
            return None
        return FullPlan.model_validate(ver.full_plan_json)

    async def list_plans_for_user(
        self,
        user_id: uuid.UUID | None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Plan]:
        stmt = select(Plan).order_by(Plan.created_at.desc()).limit(limit).offset(offset)
        if user_id is not None:
            stmt = stmt.where(Plan.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_plan_version(
        self,
        *,
        plan_id: uuid.UUID,
        full_plan_json: dict,
        red_team_json: dict | None = None,
        notes: str | None = None,
    ) -> PlanVersion:
        max_stmt = select(func.max(PlanVersion.version_num)).where(PlanVersion.plan_id == plan_id)
        max_v = (await self.session.execute(max_stmt)).scalar() or 0
        next_v = max_v + 1
        version = PlanVersion(
            plan_id=plan_id,
            version_num=next_v,
            full_plan_json=full_plan_json,
            red_team_json=red_team_json,
            notes=notes,
        )
        self.session.add(version)
        await self.session.flush()

        plan = await self.session.get(Plan, plan_id)
        if plan is not None:
            plan.current_version_id = version.id
            plan.updated_at = datetime.now(UTC)
        return version

    async def list_versions(self, plan_id: uuid.UUID) -> list[PlanVersion]:
        stmt = (
            select(PlanVersion)
            .where(PlanVersion.plan_id == plan_id)
            .order_by(PlanVersion.version_num.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, plan_id: uuid.UUID, status: str) -> None:
        plan = await self.session.get(Plan, plan_id)
        if plan is not None:
            plan.status = status

    async def add_cost(self, plan_id: uuid.UUID, cost_usd: Decimal) -> None:
        plan = await self.session.get(Plan, plan_id)
        if plan is not None:
            plan.total_cost_usd = (plan.total_cost_usd or Decimal("0")) + cost_usd
