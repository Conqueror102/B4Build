"""Tests for asyncpg / RDS database URL normalization."""

from __future__ import annotations

from src.database_url import normalize_database_url_for_async_engine


def test_rds_sslmode_require_stripped_and_connect_args_ssl() -> None:
    raw = (
        "postgresql://user:secret@xx.rds.amazonaws.com:5432/app"
        "?sslmode=require&foo=bar"
    )
    url, args = normalize_database_url_for_async_engine(raw)
    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url
    assert "ssl=" not in url.lower()
    assert "foo=bar" in url
    assert args == {"ssl": True}


def test_localhost_no_tls_by_default() -> None:
    raw = "postgresql://u:p@localhost:5432/dev"
    url, args = normalize_database_url_for_async_engine(raw)
    assert url.startswith("postgresql+asyncpg://")
    assert args == {}


def test_ssl_true_query_stripped_rds_still_tls() -> None:
    raw = "postgresql://u:p@db.xx.us-east-1.rds.amazonaws.com:5432/db?ssl=true"
    url, args = normalize_database_url_for_async_engine(raw)
    assert "ssl=" not in url.lower()
    assert args == {"ssl": True}


def test_postgres_scheme_alias() -> None:
    raw = "postgres://u:p@127.0.0.1:5432/dev"
    url, args = normalize_database_url_for_async_engine(raw)
    assert url.startswith("postgresql+asyncpg://127.0.0.1")


def test_non_rds_host_sslmode_require_gets_tls() -> None:
    """Cloud DBs (e.g. Neon) may not have rds.amazonaws.com in the hostname."""
    raw = "postgresql://u:p@ep-abc.us-east-1.aws.neon.tech:5432/db?sslmode=require"
    url, args = normalize_database_url_for_async_engine(raw)
    assert "sslmode" not in url
    assert args == {"ssl": True}
