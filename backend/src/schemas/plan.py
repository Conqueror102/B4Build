"""Aggregate plan schema and the red-team critique."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .phases import (
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
    normalize_cost_model_payload,
    normalize_infrastructure_payload,
)


class RedTeamFinding(BaseModel):
    """One adversarial concern raised by the red-team pass."""

    severity: str = Field(description="critical | high | medium | low")
    phase_id: str = Field(description="Which phase the finding targets")
    concern: str
    suggested_mitigation: str


class RedTeamCritique(BaseModel):
    """Output of the red_team node - structured criticism of the plan."""

    findings: list[RedTeamFinding] = Field(default_factory=list)
    overall_confidence: str = Field(description="high | medium | low")
    summary: str = Field(description="One paragraph synthesis of the critique")


class FullPlan(BaseModel):
    """The final artefact returned to the frontend.

    Built by ``src.graph.nodes.synthesizer`` after every phase + red team
    completes. Stored by ``plan_id`` in ``src.store``.
    """

    plan_id: str
    title: str | None = None
    idea: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    pressure_test: PressureTestResult | None = None
    problem_model_fit: ProblemModelFit | None = None
    architecture: Architecture | None = None
    build_buy_train: BuildBuyTrain | ToolsOpenSourcePhase | None = None
    infrastructure: Infrastructure | None = None
    cost_model: CostModel | None = None
    security: SecurityPlan | None = None
    observability: ObservabilityPlan | None = None
    scaling: ScalingPlan | None = None

    red_team: RedTeamCritique | None = None

    executive_summary: str | None = Field(default=None, description="3-5 sentence TL;DR for the user")
    next_steps: list[str] | None = Field(default=None, description="Concrete actions for the user this week")

    total_cost_usd: float = Field(default=0.0, description="LLM spend across all phases")

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_phase_payloads(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        raw_bb = out.get("build_buy_train")
        if isinstance(raw_bb, dict):
            if raw_bb.get("recommendation") is not None:
                out["build_buy_train"] = BuildBuyTrain.model_validate(raw_bb)
            else:
                out["build_buy_train"] = ToolsOpenSourcePhase.model_validate(raw_bb)
        raw_inf = out.get("infrastructure")
        if isinstance(raw_inf, dict):
            out["infrastructure"] = Infrastructure.model_validate(
                normalize_infrastructure_payload(raw_inf)
            )
        raw_cm = out.get("cost_model")
        if isinstance(raw_cm, dict):
            out["cost_model"] = CostModel.model_validate(normalize_cost_model_payload(raw_cm))
        return out
