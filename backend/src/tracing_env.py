"""Sync LangSmith / LangChain tracing settings into ``os.environ``.

LangSmith’s SDK reads env vars at runtime; pydantic-settings loads `.env` into
``Settings`` but does not always expose the same values to child libraries.
Call :func:`configure_langsmith_env` once at app startup before graph/LLM use.
"""

from __future__ import annotations

import os

from .settings import Settings


def configure_langsmith_env(settings: Settings) -> None:
    key = (settings.langchain_api_key or "").strip()
    if settings.langchain_tracing_v2 and key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = key
        project = (settings.langchain_project or "ai-build-advisor-dev").strip()
        if project:
            os.environ["LANGCHAIN_PROJECT"] = project
    else:
        # Do not send traces when disabled or when no API key is configured
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


def langsmith_tracing_active(settings: Settings) -> bool:
    """True when we should wrap the OpenAI client and export LLM runs to LangSmith."""
    return bool(settings.langchain_tracing_v2 and (settings.langchain_api_key or "").strip())
