"""Shrank advisor state for huge phase_outputs so Synthesizer / Red Team do not OOM the context window."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import tiktoken

# Drop least-critical phases first (still in partial plans only if we ever trim mid-pipeline; usually all 9 exist)
_PHASE_TRIM_ORDER: tuple[str, ...] = (
    "phase_7",
    "phase_6_5",
    "phase_6_25",
    "phase_5",
    "phase_4",
    "phase_3",
    "phase_2",
    "phase_1",
    "phase_0",
)


def _count_tokens(*parts: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    text = "\n".join(parts)
    return len(enc.encode(text))


def shrink_state_to_token_budget(
    state: dict[str, Any],
    build_messages: Callable[[dict[str, Any]], list[dict[str, str]]],
    max_tokens: int,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """If ``build_messages`` would exceed ``max_tokens``, remove whole phases until it fits (or we cannot shrink more)."""
    s = {**state}
    po: dict[str, Any] = {**dict(state.get("phase_outputs") or {})}
    s["phase_outputs"] = po
    meta: dict[str, Any] = {**(s.get("metadata") or {})}
    s["metadata"] = meta
    for _ in range(12):
        msgs = build_messages(s)
        text = "\n".join(
            m.get("content", "") for m in msgs if isinstance(m.get("content"), str)
        )
        if _count_tokens(text, model=model) <= max_tokens:
            return s
        outputs = s.get("phase_outputs") or {}
        if not isinstance(outputs, dict) or not outputs:
            meta["token_shrink_stuck"] = True
            return s
        for pid in _PHASE_TRIM_ORDER:
            if pid in outputs:
                prior = list(meta.get("token_shrink_dropped") or [])
                prior.append(pid)
                meta["token_shrink_dropped"] = prior
                del outputs[pid]
                s["phase_outputs"] = outputs
                break
    meta["token_shrink_exhausted"] = True
    return s
