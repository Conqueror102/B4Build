"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")
os.environ.setdefault("APP_ENV", "development")
# In-memory DB for API tests; avoid requiring Docker Postgres
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Clear cached settings so tests can override env vars per-test if needed."""
    from src.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
