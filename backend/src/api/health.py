"""Health and readiness endpoints.

/health  - liveness check (always 200 if process is running)
/ready   - readiness check (verifies external deps; 503 if not ready)
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Always returns 200 if the process is alive."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        env=settings.app_env,
        version="0.1.0",
    )


@router.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    """Readiness probe.

    Phase 0: trivial check (no external deps yet).
    Phase 3+: verify DB connectivity.
    Phase 5+: verify Redis connectivity.
    """
    settings = get_settings()
    return HealthResponse(
        status="ready",
        env=settings.app_env,
        version="0.1.0",
    )
