"""Canonical phase-id helpers.

The backend executes phases using canonical ids (e.g. ``phase_4``), while the
frontend often displays shorter ids (e.g. ``P4``). Iteration features (dirty
phases, deep dives) may also produce display ids.

This module provides a single source of truth for normalizing any incoming id
into a canonical ``phase_*`` id, plus helpers for working with ordered lists.
"""

from __future__ import annotations

from collections.abc import Iterable


# Canonical execution ids used by PHASE_REGISTRY / PHASE_ORDER.
CANONICAL_PHASE_ORDER: list[str] = [
    "phase_0",
    "phase_1",
    "phase_2",
    "phase_3",
    "phase_4",
    "phase_5",
    "phase_6_25",
    "phase_6_5",
    "phase_7",
]


_DISPLAY_TO_CANONICAL: dict[str, str] = {
    "P0": "phase_0",
    "P1": "phase_1",
    "P2": "phase_2",
    "P3": "phase_3",
    "P4": "phase_4",
    "P5": "phase_5",
    "P6.25": "phase_6_25",
    "P6.5": "phase_6_5",
    "P7": "phase_7",
}


def to_canonical_phase_id(raw: str | None) -> str | None:
    """Normalize a phase id into a canonical ``phase_*`` id.

    Accepts:
    - canonical ids: ``phase_4``
    - display ids: ``P4``, ``P6.25``, ``P6.5``
    - legacy-ish spellings: ``phase_6.25`` / ``phase_6.5``
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None

    # Fast path: display ids.
    if s in _DISPLAY_TO_CANONICAL:
        return _DISPLAY_TO_CANONICAL[s]

    # Legacy-ish: phase_6.25 / phase_6.5
    if s == "phase_6.25":
        return "phase_6_25"
    if s == "phase_6.5":
        return "phase_6_5"

    # Canonical.
    if s.startswith("phase_") and s in CANONICAL_PHASE_ORDER:
        return s

    return None


def normalize_phase_list(
    phase_ids: Iterable[str] | None,
    *,
    default_order: list[str] | None = None,
) -> list[str]:
    """Return a deduped, canonical, order-stable phase list.

    - Drops unknown ids
    - Normalizes display ids -> canonical
    - Sorts by ``default_order`` (defaults to CANONICAL_PHASE_ORDER)
    """
    if not phase_ids:
        return []

    order = default_order or CANONICAL_PHASE_ORDER
    allowed = set(order)

    seen: set[str] = set()
    canonical: list[str] = []
    for pid in phase_ids:
        c = to_canonical_phase_id(pid)
        if c is None or c not in allowed:
            continue
        if c in seen:
            continue
        seen.add(c)
        canonical.append(c)

    # Stable sort to match the canonical phase progression.
    idx = {pid: i for i, pid in enumerate(order)}
    canonical.sort(key=lambda p: idx.get(p, 10_000))
    return canonical

