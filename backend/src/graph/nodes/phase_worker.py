"""Polymorphic phase worker.

Reads ``state.current_phase``, looks up the spec in
``src.prompts.PHASE_REGISTRY``, builds the prompt, calls
``LLMClient.complete_structured`` with the spec's output schema, and writes
the validated Pydantic instance into ``state.phase_outputs[phase_id]``.

Adding a new phase is one entry in the registry - this node never changes.
"""

from __future__ import annotations

from typing import Any

from ...llm.client import LLMClient, get_llm_client
from ...logging_config import get_logger
from ...prompts import PHASE_REGISTRY, PhaseSpec
from ...settings import get_settings
from ..state import AdvisorState

logger = get_logger(__name__)


def _model_for_tier(tier: str) -> str:
    """Resolve a tier name to an actual OpenAI model id from settings."""
    settings = get_settings()
    if tier == "reasoning":
        return settings.openai_reasoning_model
    return settings.openai_default_model


async def phase_worker_node(state: AdvisorState) -> dict[str, Any]:
    """Run whichever phase ``state.current_phase`` points at."""
    phase_id = state.get("current_phase")
    if not phase_id or phase_id not in PHASE_REGISTRY:
        return {"errors": [*(state.get("errors") or []), f"unknown phase: {phase_id}"]}

    spec: PhaseSpec = PHASE_REGISTRY[phase_id]
    request_id = state.get("metadata", {}).get("request_id", "unknown")

    # Phase 3: GitHub search + prompt context (query and counts always passed)
    github_repos: list[dict[str, Any]] = []
    github_query = ""
    github_total_count = 0
    if phase_id == "phase_3":
        try:
            from ...tools.github_search import build_search_query, search_github_repos

            idea = state.get("idea", "")
            architecture = state.get("phase_outputs", {}).get("phase_2")
            arch_pattern = (
                architecture.pattern if architecture and hasattr(architecture, "pattern") else None
            )

            query = build_search_query(idea, arch_pattern)
            github_query = query

            logger.info("phase_3.github_search", request_id=request_id, query=query)
            search_result = await search_github_repos(
                query,
                max_results=10,
                min_stars=20,  # Lower threshold to include more projects
                updated_within_months=24,  # Include stable, mature projects
            )

            github_repos = [repo.model_dump() for repo in search_result.repos]
            github_total_count = int(search_result.total_count or 0)
            logger.info(
                "phase_3.github_search_complete",
                request_id=request_id,
                found=len(github_repos),
                total=github_total_count,
            )
        except Exception as e:
            logger.warning("phase_3.github_search_failed", request_id=request_id, error=str(e))
            github_repos = []
            github_query = github_query or ""

    if phase_id == "phase_3":
        messages = spec.prompt_builder(
            dict(state),
            github_repos=github_repos,
            github_query=github_query,
            github_total_count=github_total_count,
        )
    else:
        messages = spec.prompt_builder(dict(state))

    client: LLMClient = get_llm_client()
    model = _model_for_tier(spec.model_tier)

    logger.info(
        "phase.start",
        request_id=request_id,
        phase=phase_id,
        title=spec.title,
        model=model,
    )

    try:
        # Phase-specific token budgets: Phases 2 and 4 are intentionally verbose.
        max_tokens = 2000
        temperature = 0.3
        if phase_id == "phase_2":
            max_tokens = 9000
            temperature = 0.2
        if phase_id == "phase_3":
            max_tokens = 4000
            temperature = 0.25
        if phase_id == "phase_4":
            max_tokens = 6000
            temperature = 0.25
        if phase_id == "phase_5":
            max_tokens = 4500
            temperature = 0.25

        result = await client.complete_structured(
            messages=messages,
            schema=spec.output_schema,
            request_id=request_id,
            phase=phase_id,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.error("phase.failed", request_id=request_id, phase=phase_id, error=str(exc))
        # Avoid infinite retry loops: if a phase fails schema validation or errors,
        # treat it as skipped for this run by removing it from active_phase_order.
        meta = dict(state.get("metadata", {}) or {})
        apo = meta.get("active_phase_order")
        if isinstance(apo, list) and phase_id in apo:
            meta["active_phase_order"] = [p for p in apo if p != phase_id]
        return {
            "errors": [*(state.get("errors") or []), f"{phase_id}: {exc}"],
            "current_phase": None,
            "metadata": meta,
        }

    logger.info("phase.complete", request_id=request_id, phase=phase_id)

    new_outputs = dict(state.get("phase_outputs", {}) or {})
    new_outputs[phase_id] = result

    return {
        "phase_outputs": new_outputs,
        "current_phase": None,
    }
