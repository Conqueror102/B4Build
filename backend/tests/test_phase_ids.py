from __future__ import annotations

from src.graph.phase_ids import (
    CANONICAL_PHASE_ORDER,
    normalize_phase_list,
    to_canonical_phase_id,
)


def test_to_canonical_phase_id_display_ids() -> None:
    assert to_canonical_phase_id("P0") == "phase_0"
    assert to_canonical_phase_id("P6.25") == "phase_6_25"
    assert to_canonical_phase_id("P6.5") == "phase_6_5"


def test_to_canonical_phase_id_canonical_ids() -> None:
    assert to_canonical_phase_id("phase_4") == "phase_4"
    assert to_canonical_phase_id(" phase_5 ") == "phase_5"


def test_to_canonical_phase_id_legacy_spellings() -> None:
    assert to_canonical_phase_id("phase_6.25") == "phase_6_25"
    assert to_canonical_phase_id("phase_6.5") == "phase_6_5"


def test_to_canonical_phase_id_unknowns() -> None:
    assert to_canonical_phase_id(None) is None
    assert to_canonical_phase_id("") is None
    assert to_canonical_phase_id("P9") is None
    assert to_canonical_phase_id("phase_999") is None


def test_normalize_phase_list_dedup_and_order() -> None:
    got = normalize_phase_list(["P5", "phase_2", "P5", "phase_6.5", "P0"])
    assert got == ["phase_0", "phase_2", "phase_5", "phase_6_5"]
    assert got == [p for p in CANONICAL_PHASE_ORDER if p in set(got)]
