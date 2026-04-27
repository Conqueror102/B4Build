"""Tests for DB URL normalization for psycopg."""

from urllib.parse import quote, urlparse

from src.services.urls import to_psycopg_conninfo


def test_asyncpg_prefix_stripped() -> None:
    raw = "postgresql+asyncpg://user:secret@localhost:5432/db"
    out = to_psycopg_conninfo(raw)
    assert "+asyncpg" not in out
    assert out.startswith("postgresql://")


def test_password_special_chars_encoded() -> None:
    # Characters that break naive URLs if unencoded
    pwd = 'p@ss#word$99^foo!bar*baz%qux'
    raw = f"postgresql://admin:{pwd}@db.example.com:5432/appdb"
    out = to_psycopg_conninfo(raw)
    parsed = urlparse(out)
    assert parsed.password == pwd
    assert quote(pwd, safe="") in out


def test_password_can_contain_colons() -> None:
    pwd = "part1:part2:part3"
    raw = f"postgresql://user:{pwd}@host.example.com/db"
    out = to_psycopg_conninfo(raw)
    assert urlparse(out).password == pwd


def test_sslmode_added_when_query_empty() -> None:
    raw = "postgresql://u:p@h:5432/db"
    out = to_psycopg_conninfo(raw)
    assert "sslmode=require" in out


def test_ssl_true_maps_to_sslmode() -> None:
    raw = "postgresql://u:p@h:5432/db?ssl=true"
    out = to_psycopg_conninfo(raw)
    assert "sslmode=require" in out


def test_existing_sslmode_preserved() -> None:
    raw = "postgresql://u:p@h:5432/db?sslmode=verify-full"
    out = to_psycopg_conninfo(raw)
    assert "sslmode=verify-full" in out
    assert out.count("sslmode") == 1
