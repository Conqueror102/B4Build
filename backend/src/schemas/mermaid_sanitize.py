"""Strip markdown fences from LLM-produced Mermaid strings so the browser can parse them."""

from __future__ import annotations

import re


def strip_mermaid_fences(value: str) -> str:
    """Remove ``` / ```mermaid wrappers models sometimes emit despite JSON-only instructions."""
    s = value.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:mermaid)?\s*\n?", "", s, count=1, flags=re.IGNORECASE)
        s = re.sub(r"\n?```\s*$", "", s, count=1)
    return s.strip()
