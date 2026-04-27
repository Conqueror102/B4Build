"""Normalize DB URL strings (SQLAlchemy <-> libpq / psycopg)."""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse


def to_psycopg_conninfo(url: str) -> str:
    """
    Strip SQLAlchemy async driver for psycopg ``AsyncConnectionPool`` / libpq.

    Passwords (and usernames) with special characters ``# $ ^ ! % * : @`` must be
    percent-encoded in the URI. Raw characters break parsing or are treated as
    malformed percent-encoding (especially ``%``).

    psycopg3 expects ``sslmode`` (or compatible SSL params) in the connection string
    for RDS; we ensure ``sslmode=require`` when neither ``sslmode`` nor ``ssl`` is set,
    and map ``ssl=true`` to ``sslmode=require`` when appropriate.
    """
    u = url.strip()

    if "+asyncpg" in u:
        u = u.replace("postgresql+asyncpg://", "postgresql://", 1)
    if u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(u)
    netloc = parsed.netloc

    # Re-encode userinfo: use partition so passwords may contain ':' (first colon only splits user/pass)
    if "@" in netloc:
        userinfo, hostpart = netloc.rsplit("@", 1)
        if ":" in userinfo:
            u_name, _, u_pass = userinfo.partition(":")
        else:
            u_name, u_pass = userinfo, ""
        netloc = f"{quote(u_name, safe='')}:{quote(u_pass, safe='')}@{hostpart}"

    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "sslmode" not in params:
        if params.get("ssl") == "false":
            pass  # local dev — do not force TLS
        elif params.get("ssl") == "true":
            params["sslmode"] = "require"
        elif "ssl" not in params:
            params["sslmode"] = "require"

    new_query = urlencode(params)

    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, new_query, parsed.fragment))
