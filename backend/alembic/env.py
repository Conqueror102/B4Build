"""Async Alembic environment for SQLAlchemy 2 + asyncpg."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_engine_from_config,
    create_async_engine,
)

from src.database_url import (
    merge_postgres_ssl_with_rds_ca_bundle,
    normalize_database_url_for_async_engine,
)
from src.db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _rds_ca_bundle_path() -> str | None:
    p = (os.environ.get("RDS_CA_BUNDLE_PATH") or "/app/rds-global-bundle.pem").strip()
    return p or None


def _async_engine_from_database_url() -> AsyncEngine | None:
    """Build engine from ``DATABASE_URL`` (ECS, local). Returns None to fall back to alembic.ini."""
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if not raw:
        return None
    url, connect_args = normalize_database_url_for_async_engine(raw)
    connect_args = merge_postgres_ssl_with_rds_ca_bundle(connect_args, _rds_ca_bundle_path())
    kwargs: dict = {"poolclass": pool.NullPool}
    if connect_args:
        kwargs["connect_args"] = connect_args
    return create_async_engine(url, **kwargs)


def _offline_url() -> str:
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if raw:
        url, _ = normalize_database_url_for_async_engine(raw)
        return url
    return config.get_main_option("sqlalchemy.url") or ""


def run_migrations_offline() -> None:
    url = _offline_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = _async_engine_from_database_url()
    if connectable is None:
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
