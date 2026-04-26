"""Tavily web search wrapper.

Used by Phase 0 (pressure test - "has someone built this already?") and the
Red Team node ("does any current best-practice contradict this plan?").

Falls back to an empty result list if no Tavily API key is configured so
unit tests and offline dev still work end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..logging_config import get_logger
from ..settings import get_settings

logger = get_logger(__name__)


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str


async def search_web(query: str, *, max_results: int = 5) -> list[WebSearchResult]:
    """Search the web via Tavily. Returns [] if Tavily is not configured."""
    settings = get_settings()
    if not settings.tavily_api_key:
        logger.info("web_search.skipped_no_key", query=query[:80])
        return []

    try:
        from tavily import TavilyClient
    except ImportError:
        logger.warning("web_search.tavily_not_installed")
        return []

    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        raw: dict[str, Any] = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )
    except Exception as exc:
        logger.warning("web_search.failed", error=str(exc), query=query[:80])
        return []

    results: list[WebSearchResult] = []
    for item in raw.get("results", []):
        results.append(
            WebSearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", "")[:300],
            )
        )
    logger.info("web_search.completed", query=query[:80], result_count=len(results))
    return results


def format_for_prompt(results: list[WebSearchResult]) -> str:
    """Render a result list into a compact bullet list for an LLM prompt."""
    if not results:
        return "(no web search results - Tavily not configured or query returned nothing)"
    lines = []
    for r in results:
        lines.append(f"- {r.title} ({r.url}): {r.snippet}")
    return "\n".join(lines)
