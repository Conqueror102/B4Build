"""OpenAI json_schema (strict) rejects Pydantic's $ref + description siblings; client strips them."""

from __future__ import annotations

from src.llm.client import _openai_json_schema_strip_ref_siblings
from src.schemas.phases import ToolsOpenSourcePhase


def _any_ref_with_siblings(node: object) -> bool:
    if isinstance(node, dict):
        if "$ref" in node and len(node) > 1:
            return True
        return any(_any_ref_with_siblings(v) for v in node.values())
    if isinstance(node, list):
        return any(_any_ref_with_siblings(x) for x in node)
    return False


def test_tools_open_source_schema_has_no_ref_sibling_keywords_after_sanitize() -> None:
    raw = ToolsOpenSourcePhase.model_json_schema()
    assert _any_ref_with_siblings(raw) is True
    _openai_json_schema_strip_ref_siblings(raw)
    assert _any_ref_with_siblings(raw) is False
