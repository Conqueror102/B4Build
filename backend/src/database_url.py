"""PostgreSQL URL normalization for asyncpg (RDS / Secrets Manager URLs)."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_database_url_for_async_engine(database_url: str) -> tuple[str, dict[str, Any]]:
    """Build an asyncpg-safe URL and optional ``connect_args``.

    Secrets Manager often stores ``postgresql://...?sslmode=require``. SQLAlchemy passes
    query params to asyncpg, which only accepts specific ``sslmode`` values and can error
    if the URL is malformed or if ``ssl=true`` is misinterpreted.

    We strip ``sslmode`` and ``ssl`` from the query string and pass ``ssl=True`` via
    ``connect_args`` when connecting to RDS or when the original URL requested TLS.

    ``DATABASE_URL`` is injected by ECS from Secrets Manager — no boto3 here.
    """
    url = database_url.strip()
    if not url:
        return url, {}

    if url.startswith("sqlite"):
        return url, {}

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    if not (url.startswith("postgresql://") or url.startswith("postgresql+asyncpg://")):
        return url, {}

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    qs = parse_qs(parsed.query, keep_blank_values=True)

    sslmode_vals: list[str] = []
    ssl_vals: list[str] = []
    for key in list(qs.keys()):
        kl = key.lower()
        if kl == "sslmode":
            sslmode_vals.extend(qs.pop(key, []))
        elif kl == "ssl":
            ssl_vals.extend(qs.pop(key, []))

    want_tls = False
    if "rds.amazonaws.com" in hostname:
        want_tls = True

    for v in sslmode_vals:
        vl = (v or "").strip().lower()
        if vl == "disable":
            want_tls = False
        elif vl in ("require", "verify-ca", "verify-full", "prefer", "allow"):
            want_tls = True

    for v in ssl_vals:
        vl = (v or "").strip().lower()
        if vl in ("true", "1", "require"):
            want_tls = True

    if hostname in ("localhost", "127.0.0.1") or hostname.endswith(".local"):
        want_tls = False

    new_query = urlencode(qs, doseq=True)
    clean = urlunparse(
        (
            "postgresql+asyncpg",
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )

    connect_args: dict[str, Any] = {}
    if want_tls:
        connect_args["ssl"] = True

    return clean, connect_args
