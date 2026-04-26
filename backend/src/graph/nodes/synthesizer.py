"""Synthesizer node - assembles the final FullPlan."""

from __future__ import annotations

import uuid
from typing import Any

from ...llm.client import get_llm_client
from ...logging_config import get_logger
from ...prompts import synthesizer as synth_prompt
from ...prompts.token_budget import shrink_state_to_token_budget
from ...schemas.phases import (
    Architecture,
    BuildBuyTrain,
    CostModel,
    Infrastructure,
    ObservabilityPlan,
    PressureTestResult,
    ProblemModelFit,
    ScalingPlan,
    SecurityPlan,
    ToolsOpenSourcePhase,
    normalize_infrastructure_payload,
)
from ...schemas.plan import FullPlan, RedTeamCritique
from ...settings import get_settings
from ..state import AdvisorState

logger = get_logger(__name__)


async def synthesizer_node(state: AdvisorState) -> dict[str, Any]:
    """Build the FullPlan from typed phase outputs + red-team critique."""
    request_id = state.get("metadata", {}).get("request_id", "unknown")
    settings = get_settings()
    client = get_llm_client()

    d_llm = shrink_state_to_token_budget(
        dict(state),
        synth_prompt.build_prompt,
        settings.synthesizer_max_context_tokens,
        model=settings.openai_default_model,
    )
    messages = synth_prompt.build_prompt(d_llm)
    logger.info("synthesizer.start", request_id=request_id)

    try:
        narrative = await client.complete_structured(
            messages=messages,
            schema=synth_prompt.SynthesizerOutput,
            request_id=request_id,
            phase="synthesizer",
            model=settings.openai_default_model,
            temperature=0.3,
            max_tokens=1500,
        )
    except Exception as exc:
        logger.error("synthesizer.failed", request_id=request_id, error=str(exc))
        return {
            "errors": [*(state.get("errors") or []), f"synthesizer: {exc}"],
            "final_plan": None,
        }

    outputs = state.get("phase_outputs", {}) or {}
    red_team = state.get("red_team")
    if not isinstance(red_team, RedTeamCritique):
        red_team = RedTeamCritique(
            findings=[], overall_confidence="low", summary="Red team output missing."
        )

    plan_id = state.get("metadata", {}).get("plan_id") or f"plan_{uuid.uuid4().hex[:12]}"

    try:
        plan = FullPlan(
            plan_id=plan_id,
            idea=state.get("idea", ""),
            pressure_test=_maybe_cast(outputs.get("phase_0"), PressureTestResult),
            problem_model_fit=_maybe_cast(outputs.get("phase_1"), ProblemModelFit),
            architecture=_maybe_cast(outputs.get("phase_2"), Architecture),
            build_buy_train=_maybe_cast_phase3_output(outputs.get("phase_3")),
            infrastructure=_maybe_cast_infrastructure(outputs.get("phase_4")),
            cost_model=_maybe_cast(outputs.get("phase_5"), CostModel),
            security=_maybe_cast(outputs.get("phase_6_25"), SecurityPlan),
            observability=_maybe_cast(outputs.get("phase_6_5"), ObservabilityPlan),
            scaling=_maybe_cast(outputs.get("phase_7"), ScalingPlan),
            red_team=red_team,
            executive_summary=narrative.executive_summary,
            next_steps=narrative.next_steps,
            total_cost_usd=state.get("total_cost_usd", 0.0),
        )
    except Exception as exc:
        logger.error("synthesizer.assemble_failed", request_id=request_id, error=str(exc))
        return {"errors": [*(state.get("errors") or []), f"synthesizer.assemble: {exc}"]}

    logger.info("synthesizer.complete", request_id=request_id, plan_id=plan_id)
    return {"final_plan": plan, "metadata": {**state.get("metadata", {}), "plan_id": plan_id}}


def _cast(obj: Any, expected: type) -> Any:
    """Defensive cast - typed phase outputs should already be the right type."""
    if isinstance(obj, expected):
        return obj
    if obj is None:
        raise ValueError(f"missing required phase output for {expected.__name__}")
    if hasattr(obj, "model_dump"):
        return expected(**obj.model_dump())
    if isinstance(obj, dict):
        return expected(**obj)
    raise TypeError(f"cannot cast {type(obj).__name__} to {expected.__name__}")


def _maybe_cast(obj: Any, expected: type) -> Any | None:
    """Like _cast, but returns None when the phase was skipped/missing."""
    if obj is None:
        return None
    return _cast(obj, expected)


def _maybe_cast_phase3_output(obj: Any) -> BuildBuyTrain | ToolsOpenSourcePhase | None:
    """Phase 3: legacy BuildBuyTrain JSON or new ToolsOpenSourcePhase."""
    if obj is None:
        return None
    if isinstance(obj, (BuildBuyTrain, ToolsOpenSourcePhase)):
        return obj
    if hasattr(obj, "model_dump"):
        return _maybe_cast_phase3_output(obj.model_dump())
    if isinstance(obj, dict):
        if obj.get("recommendation") is not None:
            return BuildBuyTrain.model_validate(obj)
        return ToolsOpenSourcePhase.model_validate(obj)
    raise TypeError(f"cannot cast phase_3 output {type(obj).__name__}")


def _maybe_cast_infrastructure(obj: Any) -> Infrastructure | None:
    """Phase 4: normalize legacy infra dicts before validating."""
    if obj is None:
        return None
    if isinstance(obj, Infrastructure):
        return obj
    if hasattr(obj, "model_dump"):
        return Infrastructure.model_validate(
            normalize_infrastructure_payload(obj.model_dump(mode="json"))
        )
    if isinstance(obj, dict):
        return Infrastructure.model_validate(normalize_infrastructure_payload(obj))
    raise TypeError(f"cannot cast phase_4 output {type(obj).__name__}")
