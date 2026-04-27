"""Normalize DB URL strings (SQLAlchemy <-> libpq / psycopg)."""

from __future__ import annotations
from urllib.parse import urlparse, urlunparse, quote, unquote, parse_qs, urlencode


def to_psycopg_conninfo(database_url: str) -> str:
    """
    Convert DATABASE_URL to psycopg3-compatible connection string.
    
    Fixes for AWS RDS:
    - Properly handles special characters in passwords (# $ ^ ! % * ? etc.)
    - Ensures ?sslmode=require is present for RDS SSL connections
    - Handles both raw and URL-encoded passwords from Secrets Manager
    
    psycopg3 uses libpq which requires proper URL encoding for special chars.
    """
    if not database_url or not database_url.strip():
        return database_url.strip() if database_url else ""

    u = database_url.strip()

    # Normalize driver prefixes
    u = u.replace("postgresql+asyncpg://", "postgresql://", 1)
    u = u.replace("postgres://", "postgresql://", 1)

    try:
        parsed = urlparse(u)
    except Exception:
        # If URL parsing fails completely, return as-is
        return u

    # Handle password encoding: decode first (in case it's already encoded), then encode properly
    if parsed.password:
        # Decode any existing encoding, then re-encode safely
        # This handles both raw passwords and already-encoded ones
        raw_password = unquote(parsed.password)
        safe_password = quote(raw_password, safe="")
        
        # Rebuild netloc with properly encoded password
        if parsed.username:
            userinfo = f"{parsed.username}:{safe_password}"
        else:
            userinfo = safe_password
        
        if parsed.hostname:
            netloc = f"{userinfo}@{parsed.hostname}"
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
        else:
            netloc = userinfo
        
        parsed = parsed._replace(netloc=netloc)

    # Ensure sslmode=require for RDS (AWS requires SSL)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    if "sslmode" not in query_params:
        query_params["sslmode"] = ["require"]
    
    new_query = urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)

    return urlunparse(parsed)
