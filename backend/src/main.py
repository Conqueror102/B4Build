"""FastAPI application entry point."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from .api import chat, export, health, plan
from .db import models
from .db.bootstrap import create_all_sqlite_schema, ensure_default_user_exists
from .db.session import dispose_engine, get_engine, init_engine
from .logging_config import configure_logging, get_logger
from .services import checkpointing
from .settings import get_settings
from .tracing_env import configure_langsmith_env


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run on startup and shutdown."""
    configure_logging()
    settings = get_settings()
    configure_langsmith_env(settings)
    logger = get_logger(__name__)

    dsn = (settings.sentry_dsn or "").strip()
    # Secret may still be Terraform placeholder "REPLACE_..."; must be a real https DSN
    if dsn.startswith("https://"):
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            send_default_pii=False,
        )
        logger.info("sentry.initialized", env=settings.app_env)

    init_engine(settings.database_url)
    url = settings.database_url
    if "sqlite" in url:
        await create_all_sqlite_schema(models.Base, get_engine())
    uu = uuid.UUID(settings.default_local_user_id)
    try:
        await ensure_default_user_exists(uu, email="local-dev@advisor.local")
    except Exception as exc:
        logger.warning("default_user_seed_skipped", error=str(exc))
    await checkpointing.init_checkpointer(url)

    logger.info(
        "app.startup",
        env=settings.app_env,
        log_level=settings.log_level,
        default_model=settings.openai_default_model,
        reasoning_model=settings.openai_reasoning_model,
        daily_spend_cap_usd=settings.daily_openai_spend_cap,
        per_request_cost_cap_usd=settings.per_request_cost_cap,
    )

    yield

    await checkpointing.close_checkpointer()
    await dispose_engine()
    logger.info("app.shutdown")


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    """Mirror CORSMiddleware so error responses still allow browser JS to read status/body."""
    origin = request.headers.get("origin")
    if not origin:
        return {}
    settings = get_settings()
    normalized = origin.rstrip("/")
    allowed = {o.rstrip("/") for o in settings.cors_allow_origins}
    if normalized not in allowed:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    }


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="AI Build Advisor",
        description="Conversational AI advisor for engineers building AI applications",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Unhandled exceptions bypass CORSMiddleware response wrapping; browsers then show a CORS
    # error even when the real problem is e.g. HTTP 500. Attach the same allow-origin headers.
    @app.middleware("http")
    async def cors_headers_on_errors(request: Request, call_next):  # type: ignore[misc]
        logger = get_logger(__name__)
        try:
            return await call_next(request)
        except HTTPException as exc:
            extra = dict(exc.headers) if exc.headers else {}
            headers = {**_cors_headers_for_request(request), **extra}
            return JSONResponse(
                content={"detail": exc.detail},
                status_code=exc.status_code,
                headers=headers,
            )
        except Exception:
            logger.exception("unhandled_exception")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=_cors_headers_for_request(request),
            )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(plan.router)
    app.include_router(export.router)

    return app


app = create_app()
