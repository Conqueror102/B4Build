"""Daily OpenAI spend tracking + cap enforcement."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DailySpend


class SpendRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_today_spend(self) -> Decimal:
        today = date.today()
        stmt = select(DailySpend.total_cost_usd).where(DailySpend.spend_date == today)
        result = await self.session.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal("0")

    async def record_call(self, cost_usd: Decimal) -> None:
        today = date.today()
        dialect = self.session.bind.dialect.name if self.session.bind else ""
        if dialect == "postgresql":
            stmt = pg_insert(DailySpend).values(
                spend_date=today,
                total_cost_usd=cost_usd,
                request_count=1,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["spend_date"],
                set_={
                    "total_cost_usd": DailySpend.total_cost_usd + cost_usd,
                    "request_count": DailySpend.request_count + 1,
                },
            )
            await self.session.execute(stmt)
        elif dialect == "sqlite":
            stmt = sqlite_insert(DailySpend).values(
                spend_date=today,
                total_cost_usd=cost_usd,
                request_count=1,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["spend_date"],
                set_={
                    "total_cost_usd": DailySpend.total_cost_usd + cost_usd,
                    "request_count": DailySpend.request_count + 1,
                },
            )
            await self.session.execute(stmt)
        else:
            existing = await self.session.execute(
                select(DailySpend).where(DailySpend.spend_date == today)
            )
            row = existing.scalar_one_or_none()
            if row is None:
                self.session.add(
                    DailySpend(
                        spend_date=today,
                        total_cost_usd=cost_usd,
                        request_count=1,
                    )
                )
            else:
                row.total_cost_usd = (row.total_cost_usd or Decimal("0")) + cost_usd
                row.request_count = (row.request_count or 0) + 1

    async def is_under_cap(self, cap_usd: Decimal) -> bool:
        spend = await self.get_today_spend()
        return spend < cap_usd
