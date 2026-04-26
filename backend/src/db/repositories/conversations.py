"""Conversation turns repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ConversationTurn


class ConversationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_turn(
        self,
        *,
        plan_id: uuid.UUID,
        role: str,
        content: str,
        intent: str | None = None,
        affected_phases: list | None = None,
    ) -> ConversationTurn:
        max_stmt = select(func.max(ConversationTurn.turn_idx)).where(
            ConversationTurn.plan_id == plan_id
        )
        max_idx = (await self.session.execute(max_stmt)).scalar()
        next_idx = 0 if max_idx is None else max_idx + 1
        turn = ConversationTurn(
            plan_id=plan_id,
            turn_idx=next_idx,
            role=role,
            content=content,
            intent=intent,
            affected_phases=affected_phases,
        )
        self.session.add(turn)
        await self.session.flush()
        return turn

    async def list_turns_for_plan(self, plan_id: uuid.UUID) -> list[ConversationTurn]:
        stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.plan_id == plan_id)
            .order_by(ConversationTurn.turn_idx.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
