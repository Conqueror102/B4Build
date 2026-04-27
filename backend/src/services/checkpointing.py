"""LangGraph AsyncPostgresSaver (long-lived pool) + app wiring."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ..logging_config import get_logger
from .urls import to_psycopg_conninfo

logger = get_logger(__name__)

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None
_close_hook: Callable[[], Awaitable[None]] | None = None


def get_checkpointer() -> AsyncPostgresSaver | None:
    return _checkpointer


async def init_checkpointer(
    database_url: str, *, min_size: int = 1, max_size: int = 3
) -> None:
    """Build a long-lived checkpointer. Call ``setup`` once; requires Postgres (not SQLite)."""
    global _checkpointer, _pool, _close_hook

    if "sqlite" in database_url or database_url.strip() == "":
        logger.info("checkpointer.skip", reason="no_postgres")
        return

    conninfo = to_psycopg_conninfo(database_url)
    
    # Connection pool configuration
    pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=min_size,
        max_size=max_size,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=False,
        timeout=30.0,  # Connection timeout
        max_idle=300.0,  # Recycle connections idle for 5 minutes
        reconnect_timeout=5.0,  # Retry failed connections
    )
    await pool.open()
    
    # LangGraph setup() often runs migrations with CREATE INDEX CONCURRENTLY,
    # which cannot run inside a transaction. We use a one-off autocommit connection for this.
    # 
    # RDS compatibility: conninfo already includes sslmode in the connection string (e.g., ?sslmode=require).
    # psycopg3 accepts SSL parameters in the conninfo string (libpq format), not as keyword arguments.
    async with await psycopg.AsyncConnection.connect(conninfo, autocommit=True) as setup_conn:
        setup_cp = AsyncPostgresSaver(setup_conn)
        await setup_cp.setup()
        
    cp = AsyncPostgresSaver(conn=pool)
    _checkpointer = cp
    _pool = pool

    async def _close() -> None:
        if _pool is not None:
            await _pool.close()

    _close_hook = _close
    logger.info("checkpointer.initialized", max_size=max_size)


async def close_checkpointer() -> None:
    global _checkpointer, _pool, _close_hook
    if _close_hook is not None:
        await _close_hook()
    _checkpointer = None
    _pool = None
    _close_hook = None
