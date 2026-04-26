"""Normalize DB URL strings (SQLAlchemy <-> libpq / psycopg)."""

from __future__ import annotations


def to_psycopg_conninfo(url: str) -> str:
    """Strip SQLAlchemy async driver for psycopg ``AsyncConnectionPool``."""
    u = url.strip()
    if "+asyncpg" in u:
        return u.replace("postgresql+asyncpg://", "postgresql://", 1)
    if u.startswith("postgres://"):
        return u.replace("postgres://", "postgresql://", 1)
    if u.startswith("postgresql://") and "://" in u[12:]:
        return u
    return u
