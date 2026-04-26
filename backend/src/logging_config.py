"""structlog configuration.

Produces JSON logs in production, human-readable in dev.
PII scrubbing processors are added before any sink.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from .settings import get_settings

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _mask_emails(_logger: Any, _name: str, event_dict: EventDict) -> EventDict:
    """Mask email addresses anywhere in log values."""
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            event_dict[key] = EMAIL_PATTERN.sub("<email>", value)
    return event_dict


def _truncate_prompts(_logger: Any, _name: str, event_dict: EventDict) -> EventDict:
    """Never log full prompts/completions in CloudWatch.

    LangSmith captures full prompts; logs should only have metadata.
    """
    for key in ("prompt", "completion", "messages"):
        if key in event_dict:
            value = event_dict[key]
            if isinstance(value, str) and len(value) > 200:
                event_dict[key] = value[:200] + f"... [truncated, {len(value)} total]"
            elif isinstance(value, list):
                event_dict[key] = f"<{len(value)} messages, redacted>"
    return event_dict


def configure_logging() -> None:
    """Configure structlog. Call once at app startup."""
    settings = get_settings()

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
        _mask_emails,
        _truncate_prompts,
    ]

    if settings.is_production:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger. Use module __name__ as the name argument."""
    return structlog.get_logger(name)
