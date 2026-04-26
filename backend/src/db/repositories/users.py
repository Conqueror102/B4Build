"""User repository (stub; Clerk in Phase 5)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create_local_dev_user(self, user_id: uuid.UUID, email: str) -> User:
        u = User(id=user_id, email=email, clerk_user_id=None)
        self.session.add(u)
        await self.session.flush()
        return u

    async def ensure_user_exists(self, user_id: uuid.UUID, email: str) -> User:
        row = await self.get(user_id)
        if row is not None:
            return row
        return await self.create_local_dev_user(user_id, email)
