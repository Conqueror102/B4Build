"""Pydantic schemas used across the backend.

Schemas serve a dual purpose:
- They validate HTTP request/response bodies in FastAPI.
- They are passed to ``LLMClient.complete_structured`` so the OpenAI
  ``response_format=json_schema`` machinery enforces the same shape on LLM
  outputs.

That dual use is why every schema lives in this single package.
"""

from .chat import ChatRequest, ChatStreamEvent, PlanResponse
from .intake import IntakeAnswers
from .phases import (
    Architecture,
    BuildBuyTrain,
    CostLineItem,
    CostModel,
    InfraLayer,
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
from .plan import FullPlan, RedTeamCritique

__all__ = [
    "Architecture",
    "BuildBuyTrain",
    "InfraLayer",
    "ChatRequest",
    "ChatStreamEvent",
    "CostLineItem",
    "CostModel",
    "FullPlan",
    "Infrastructure",
    "IntakeAnswers",
    "ObservabilityPlan",
    "PlanResponse",
    "PressureTestResult",
    "ProblemModelFit",
    "RedTeamCritique",
    "ScalingPlan",
    "SecurityPlan",
    "ToolsOpenSourcePhase",
    "normalize_cost_model_payload",
    "normalize_infrastructure_payload",
]
