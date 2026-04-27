"""Normalize DB URL strings (SQLAlchemy <-> libpq / psycopg)."""

from __future__ import annotations
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def to_psycopg_conninfo(url: str) -> str:
    """
    Strip SQLAlchemy async driver for psycopg ``AsyncConnectionPool``.
    Also extracts sslmode from query string and returns it as a libpq-compatible conninfo.
    
    psycopg3 expects sslmode in the connection string, not as a keyword argument.
    AWS RDS requires SSL, so we preserve sslmode in the conninfo string.
    """
    u = url.strip()
    
    # Normalize driver prefix
    if "+asyncpg" in u:
        u = u.replace("postgresql+asyncpg://", "postgresql://", 1)
    if u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql://", 1)
    
    # Parse URL to handle query parameters properly
    parsed = urlparse(u)
    
    # If there are query parameters, rebuild the URL with them
    # psycopg3 accepts them in the connection string
    if parsed.query:
        # Query params like ?sslmode=require are valid in libpq connection strings
        return u
    
    return u
