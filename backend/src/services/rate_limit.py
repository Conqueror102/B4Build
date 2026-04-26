"""Simple in-memory per-key sliding-window rate limiter (solo dev; Redis in P5)."""

from __future__ import annotations

import time
from collections import deque


class MemorySlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}

    def is_allowed(
        self,
        key: str,
        *,
        max_events: int,
        window_seconds: float,
    ) -> bool:
        now = time.perf_counter()
        cutoff = now - window_seconds
        q = self._events.setdefault(key, deque())
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= max_events:
            return False
        q.append(now)
        return True


_limiter = MemorySlidingWindowLimiter()


def user_chat_limiter() -> MemorySlidingWindowLimiter:
    return _limiter
