"""Tests for LLM mermaid string cleanup."""

from src.schemas.mermaid_sanitize import strip_mermaid_fences


def test_strip_plain_no_fence() -> None:
    s = "flowchart LR\n  A --> B\n"
    assert strip_mermaid_fences(s) == s.strip()


def test_strip_mermaid_fence() -> None:
    raw = "```mermaid\nflowchart LR\n  U --> V\n```"
    assert strip_mermaid_fences(raw) == "flowchart LR\n  U --> V"


def test_strip_generic_fence() -> None:
    raw = "```\nerDiagram\n  X ||--o{ Y\n```"
    assert strip_mermaid_fences(raw).startswith("erDiagram")
