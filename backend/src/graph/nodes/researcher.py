"""Researcher node.

Executes live web searches via Tavily to provide the LLM with up-to-date
context (e.g., pricing, features) before it runs specific phases.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ...llm.client import get_llm_client
from ...logging_config import get_logger
from ...settings import get_settings
from ...tools.web_search import format_for_prompt, search_web
from ..state import AdvisorState

logger = get_logger(__name__)


class SearchQueries(BaseModel):
    queries: list[str] = Field(
        description="Exactly 1-3 targeted web search queries to fetch pricing or feature info.",
        max_length=3,
    )


async def researcher_node(state: AdvisorState) -> dict[str, Any]:
    """Determine what to search for and run Tavily queries."""
    phase_id = state.get("current_phase")
    idea = state.get("idea", "")
    request_id = state.get("metadata", {}).get("request_id", "unknown")

    settings = get_settings()
    if not settings.tavily_api_key:
        logger.warning("researcher.skipped_no_tavily_key", request_id=request_id)
        return {"research_context": []}

    # Extract the last user message if this is an iteration
    last_msg = ""
    messages = state.get("messages", [])
    if messages:
        # get the last user message
        for m in reversed(messages):
            if m.get("role") == "user":
                last_msg = m.get("content", "")
                break

    system_prompt = f"""You are a research query generator for an AI Architecture Advisor.
We are about to execute Phase: {phase_id} (e.g., Phase 4 Infrastructure or Phase 5 Cost Model).

The user's core idea:
{idea}

The user's latest constraint/question:
{last_msg}

Generate exactly 1 to 3 search queries to look up live, current pricing, limits, or features for the specific technologies mentioned by the user or relevant to the phase. Be specific (e.g., "AWS Fargate pricing 2024", "Vercel hobby tier limits")."""

    client = get_llm_client()
    try:
        query_model = await client.complete_structured(
            messages=[{"role": "system", "content": system_prompt}],
            schema=SearchQueries,
            request_id=request_id,
            phase="researcher",
            model=settings.openai_default_model,
        )
    except Exception as exc:
        logger.error("researcher.query_generation_failed", error=str(exc))
        return {"research_context": []}

    if not isinstance(query_model, SearchQueries) or not query_model.queries:
        return {"research_context": []}

    snippets = []
    for q in query_model.queries:
        logger.info("researcher.searching", query=q, request_id=request_id)
        try:
            results = await search_web(q)
            formatted = format_for_prompt(results)
            snippets.append(f"### Web Search: {q}\n{formatted}")
        except Exception as exc:
            logger.error("researcher.search_failed", query=q, error=str(exc))

    return {"research_context": snippets}
