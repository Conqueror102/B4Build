"""Phase prompt registry.

Each phase module exports ``build_prompt(state) -> list[dict]``. Adding a new
phase means: write the module, add the schema to ``schemas.phases``, register
it here, and append it to ``PHASE_ORDER``. The graph picks it up automatically
because ``phase_worker`` is polymorphic over this registry.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from ..schemas.phases import (
    Architecture,
    CostModel,
    Infrastructure,
    ObservabilityPlan,
    PressureTestResult,
    ProblemModelFit,
    ScalingPlan,
    SecurityPlan,
    ToolsOpenSourcePhase,
)
from . import (
    phase_0_pressure_test,
    phase_1_problem_model_fit,
    phase_2_architecture,
    phase_3_open_source_scouting,
    phase_4_infrastructure,
    phase_5_cost_model,
    phase_6_5_observability,
    phase_6_25_security,
    phase_7_scaling,
)

PromptBuilder = Callable[..., list[dict[str, Any]]]
ModelTier = str  # "default" -> gpt-4o-mini, "reasoning" -> gpt-4o


@dataclass(frozen=True)
class PhaseSpec:
    """How to run one phase: what prompt, what schema, which model tier."""

    phase_id: str
    title: str
    prompt_builder: PromptBuilder
    output_schema: type[BaseModel]
    model_tier: ModelTier


PHASE_REGISTRY: dict[str, PhaseSpec] = {
    "phase_0": PhaseSpec(
        phase_id="phase_0",
        title="Pressure test",
        prompt_builder=phase_0_pressure_test.build_prompt,
        output_schema=PressureTestResult,
        model_tier="default",
    ),
    "phase_1": PhaseSpec(
        phase_id="phase_1",
        title="Problem-model fit",
        prompt_builder=phase_1_problem_model_fit.build_prompt,
        output_schema=ProblemModelFit,
        model_tier="default",
    ),
    "phase_2": PhaseSpec(
        phase_id="phase_2",
        title="Architecture",
        prompt_builder=phase_2_architecture.build_prompt,
        output_schema=Architecture,
        model_tier="reasoning",
    ),
    "phase_3": PhaseSpec(
        phase_id="phase_3",
        title="Tools & open source",
        prompt_builder=phase_3_open_source_scouting.build_prompt,
        output_schema=ToolsOpenSourcePhase,
        model_tier="reasoning",
    ),
    "phase_4": PhaseSpec(
        phase_id="phase_4",
        title="Infrastructure",
        prompt_builder=phase_4_infrastructure.build_prompt,
        output_schema=Infrastructure,
        model_tier="default",
    ),
    "phase_5": PhaseSpec(
        phase_id="phase_5",
        title="Cost model",
        prompt_builder=phase_5_cost_model.build_prompt,
        output_schema=CostModel,
        model_tier="reasoning",
    ),
    "phase_6_25": PhaseSpec(
        phase_id="phase_6_25",
        title="Security & compliance",
        prompt_builder=phase_6_25_security.build_prompt,
        output_schema=SecurityPlan,
        model_tier="default",
    ),
    "phase_6_5": PhaseSpec(
        phase_id="phase_6_5",
        title="Observability",
        prompt_builder=phase_6_5_observability.build_prompt,
        output_schema=ObservabilityPlan,
        model_tier="default",
    ),
    "phase_7": PhaseSpec(
        phase_id="phase_7",
        title="Scaling & resilience",
        prompt_builder=phase_7_scaling.build_prompt,
        output_schema=ScalingPlan,
        model_tier="default",
    ),
}


PHASE_ORDER: list[str] = [
    "phase_0",
    "phase_1",
    "phase_2",
    "phase_3",
    "phase_4",
    "phase_5",
    "phase_6_25",
    "phase_6_5",
    "phase_7",
]


__all__ = [
    "PHASE_ORDER",
    "PHASE_REGISTRY",
    "ModelTier",
    "PhaseSpec",
    "PromptBuilder",
]
