"""Async SQLAlchemy engine + session factory + FastAPI dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..logging_config import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> None:
    """Initialize the global async engine and session factory.

    Normalizes ``postgresql://`` URLs to use the asyncpg driver, and skips
    pool sizing for SQLite (which uses a single-connection pool).
    
    For AWS RDS: Handles sslmode parameter correctly for asyncpg driver.
    """
    global _engine, _session_factory

    url = database_url
    
    # Normalize to use asyncpg driver
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    
    # Remove sslmode from query string (asyncpg doesn't support it)
    # Instead, use ssl=true which asyncpg understands
    if "?sslmode=" in url or "&sslmode=" in url:
        # Remove sslmode parameter
        import re
        url = re.sub(r'[?&]sslmode=[^&]*', '', url)
        # Add ssl=true if not already present
        if "ssl=" not in url.lower():
            url = f"{url}{'&' if '?' in url else '?'}ssl=true"
    
    is_sqlite = url.startswith("sqlite")
    
    # Ensure SSL is enabled for PostgreSQL if not already specified
    if not is_sqlite and "postgresql" in url:
        u = url.lower()
        if "ssl=" not in u:
            url = f"{url}{'&' if '?' in url else '?'}ssl=true"

    if is_sqlite:
        engine = create_async_engine(url, future=True)
    else:
        engine = create_async_engine(
            url,
            pool_pre_ping=True,  # Verify connections before using (critical for Neon)
            pool_size=3,  # Reduced for Neon
            max_overflow=5,  # Reduced for Neon
            pool_recycle=1800,  # Recycle connections after 30 minutes (Neon closes idle connections)
            pool_timeout=30,  # Wait up to 30s for a connection
            future=True,
        )

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
