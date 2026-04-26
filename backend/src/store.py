"""In-memory plan store.

Phase 1 only - Phase 3 will replace this with Postgres + SQLAlchemy. The
public surface (``put``, ``get``, ``has``) is intentionally minimal so the
swap is mechanical.

Thread/async safety: the dict mutations are atomic in CPython, and we are
single-process for Phase 1, so we don't bother with a lock.
"""

from __future__ import annotations

from .schemas.plan import FullPlan

_PLANS: dict[str, FullPlan] = {}


def put(plan: FullPlan) -> None:
    _PLANS[plan.plan_id] = plan


def get(plan_id: str) -> FullPlan | None:
    return _PLANS.get(plan_id)


def has(plan_id: str) -> bool:
    return plan_id in _PLANS


def clear() -> None:
    """Used by tests to reset state between cases."""
    _PLANS.clear()
