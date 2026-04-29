"""Deterministic JSON diff engine for Phase 4 Conversation Iteration.

Produces a list of differences between two dicts (old phase state vs new phase state)
so the frontend can display them visually without relying on LLM summaries.
"""

from __future__ import annotations

from typing import Any


def _is_dict(val: Any) -> bool:
    return isinstance(val, dict)


def _is_list(val: Any) -> bool:
    return isinstance(val, list)


def diff_dicts(
    old_dict: dict[str, Any], new_dict: dict[str, Any], path: str = ""
) -> list[dict[str, Any]]:
    """Compare two dictionaries and return a list of JSON Patch-like operations."""
    diffs: list[dict[str, Any]] = []

    old_keys = set(old_dict.keys())
    new_keys = set(new_dict.keys())

    for key in old_keys - new_keys:
        current_path = f"{path}.{key}" if path else key
        diffs.append({"op": "remove", "path": current_path, "old": old_dict[key], "new": None})

    for key in new_keys - old_keys:
        current_path = f"{path}.{key}" if path else key
        diffs.append({"op": "add", "path": current_path, "old": None, "new": new_dict[key]})

    for key in old_keys & new_keys:
        current_path = f"{path}.{key}" if path else key
        old_val = old_dict[key]
        new_val = new_dict[key]

        if old_val == new_val:
            continue

        if _is_dict(old_val) and _is_dict(new_val):
            diffs.extend(diff_dicts(old_val, new_val, current_path))
        elif _is_list(old_val) and _is_list(new_val):
            # For lists, if they differ, we'll just treat it as a replace for simplicity
            # rather than computing complex list-level edits (add/remove at index).
            diffs.append({"op": "replace", "path": current_path, "old": old_val, "new": new_val})
        else:
            diffs.append({"op": "replace", "path": current_path, "old": old_val, "new": new_val})

    return diffs
