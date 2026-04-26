"""Request-scoped context: active plan for attributing OpenAI spend."""

from __future__ import annotations

import contextvars
import uuid

_active_plan_id: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "active_plan_id", default=None
)


def get_active_plan_id() -> uuid.UUID | None:
    return _active_plan_id.get()


def set_active_plan_id(plan_id: uuid.UUID | None) -> contextvars.Token[uuid.UUID | None]:
    return _active_plan_id.set(plan_id)


def reset_active_plan_id(token: contextvars.Token[uuid.UUID | None]) -> None:
    _active_plan_id.reset(token)
