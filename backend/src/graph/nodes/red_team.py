"""Red Team node - adversarial critique pass over all phase outputs."""

from __future__ import annotations

from typing import Any

from ...llm.client import get_llm_client
from ...logging_config import get_logger
from ...prompts import red_team as red_team_prompt
from ...prompts.token_budget import shrink_state_to_token_budget
from ...schemas.plan import RedTeamCritique
from ...settings import get_settings
from ..state import AdvisorState

logger = get_logger(__name__)


async def red_team_node(state: AdvisorState) -> dict[str, Any]:
    """Run the red-team critique using the reasoning model."""
    request_id = state.get("metadata", {}).get("request_id", "unknown")
    settings = get_settings()
    client = get_llm_client()

    d_llm = shrink_state_to_token_budget(
        dict(state),
        red_team_prompt.build_prompt,
        get_settings().red_team_max_context_tokens,
        model=settings.openai_reasoning_model,
    )
    messages = red_team_prompt.build_prompt(d_llm)

    logger.info("red_team.start", request_id=request_id)

    try:
        critique = await client.complete_structured(
            messages=messages,
            schema=RedTeamCritique,
            request_id=request_id,
            phase="red_team",
            model=settings.openai_reasoning_model,
            temperature=0.4,
            max_tokens=2500,
        )
    except Exception as exc:
        logger.error("red_team.failed", request_id=request_id, error=str(exc))
        return {
            "errors": [*(state.get("errors") or []), f"red_team: {exc}"],
            "red_team": RedTeamCritique(
                findings=[],
                overall_confidence="low",
                summary=f"Red team pass failed: {exc}",
            ),
        }

    logger.info(
        "red_team.complete",
        request_id=request_id,
        finding_count=len(critique.findings),
        confidence=critique.overall_confidence,
    )
    return {"red_team": critique}
