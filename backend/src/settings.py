"""Application settings, loaded from environment variables.

Single source of truth for configuration. Never read os.environ directly elsewhere.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app config. Loaded from .env (project root) and OS env vars."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_default_model: str = Field(
        default="gpt-4o-mini",
        description="Cheap model for simple/lookup tasks",
    )
    openai_reasoning_model: str = Field(
        default="gpt-4o",
        description="Stronger model for reasoning-heavy phases",
    )

    tavily_api_key: str = Field(default="", description="Tavily web search API key")

    github_token: str = Field(
        default="",
        description="GitHub PAT for repository search (Phase 3). Improves rate limits vs unauthenticated API.",
    )

    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "ai-build-advisor-dev"

    database_url: str = Field(
        default="postgresql+asyncpg://advisor:advisor@localhost:5432/advisor",
        description="Async SQLAlchemy URL (Phase 3+)",
    )

    rds_ca_bundle_path: str = Field(
        default="/app/rds-global-bundle.pem",
        description=(
            "Path to AWS RDS combined CA PEM (Dockerfile downloads this for ECS). "
            "If the file is missing, TLS still uses ssl=True without custom CA."
        ),
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL (Phase 5+)",
    )

    daily_openai_spend_cap: float = Field(
        default=10.0,
        description="USD - hard cap per day on OpenAI spend (tracked in DB) across all users",
    )
    per_request_cost_cap: float = Field(
        default=0.50,
        description="USD - hard cap per individual LLM call",
    )

    sentry_dsn: str = ""

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://192.168.0.127:3000",
        ],
        description="Allowed origins for CORS (frontend dev URL by default)",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, v: Any) -> Any:
        """ECS passes JSON in env; pydantic-settings may leave a string — parse explicitly."""
        if isinstance(v, str) and v.strip().startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

    @field_validator("cors_allow_origins", mode="after")
    @classmethod
    def normalize_cors_origins(cls, v: list[str]) -> list[str]:
        """Browsers send Origin without a trailing slash; tfvars typos with '/' break CORS."""
        return [o.rstrip("/") for o in v]

    llm_default_timeout_seconds: float = 60.0
    llm_max_retries: int = 3

    # Local / no-auth: single stub user (Phase 5+ replaces with Clerk)
    default_local_user_id: str = "00000000-0000-4000-8000-000000000001"
    # In-memory, per user id string (enough for solo local dev; Redis in Phase 5)
    api_rate_limit_per_user_per_minute: int = 60

    synthesizer_max_context_tokens: int = 100_000
    red_team_max_context_tokens: int = 100_000

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Use this everywhere."""
    return Settings()
