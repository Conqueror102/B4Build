"""Create-all for SQLite + default local user (no auth)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from .repositories.users import UserRepository
from .session import get_session


async def create_all_sqlite_schema(model_base: type[DeclarativeBase], engine: AsyncEngine) -> None:
    """Only for tests / sqlite :memory: — production Postgres uses Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(model_base.metadata.create_all)


async def ensure_default_user_exists(user_id: uuid.UUID, email: str) -> None:
    async with get_session() as session:
        repo = UserRepository(session)
        await repo.ensure_user_exists(user_id, email)
