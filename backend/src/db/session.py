"""Async SQLAlchemy engine + session factory + FastAPI dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..database_url import (
    merge_postgres_ssl_with_rds_ca_bundle,
    normalize_database_url_for_async_engine,
)
from ..logging_config import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str, *, rds_ca_bundle_path: str | None = None) -> None:
    """Initialize the global async engine and session factory.

    Normalizes PostgreSQL URLs for the asyncpg driver and RDS TLS without relying on
    fragile regex over the connection string. When ``rds_ca_bundle_path`` points at the
    AWS RDS CA bundle, asyncpg verifies the server chain (required for RDS on ECS).
    """
    global _engine, _session_factory

    url, connect_args = normalize_database_url_for_async_engine(database_url)
    connect_args = merge_postgres_ssl_with_rds_ca_bundle(connect_args, rds_ca_bundle_path)
    is_sqlite = url.startswith("sqlite")

    if is_sqlite:
        engine = create_async_engine(url, future=True)
    else:
        eng_kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "pool_size": 3,
            "max_overflow": 5,
            "pool_recycle": 1800,
            "pool_timeout": 30,
            "future": True,
        }
        if connect_args:
            eng_kwargs["connect_args"] = connect_args
        engine = create_async_engine(url, **eng_kwargs)

    _engine = engine
    _session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    logger.info("db_engine_initialized", dialect=engine.dialect.name)


async def dispose_engine() -> None:
    """Dispose the engine and reset module-level globals."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call init_engine() first.")
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context-managed session: commit on success, rollback on error."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an ``AsyncSession``."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
