"""Wire-format models for /api/chat and /api/plan."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .plan import FullPlan


class ChatRequest(BaseModel):
    """POST /api/chat request body."""

    idea: str = Field(min_length=10, description="User's project idea")
    active_phase_order: list[str] | None = Field(
        default=None,
        description=(
            "Optional subset/ordering of phases to run for this plan. "
            "May contain canonical ids (phase_0..phase_7, phase_6_25, phase_6_5) "
            "or display ids (P0..P7, P6.25, P6.5)."
        ),
    )
    clarifying_answers: dict[str, str] | None = Field(
        default=None,
        description="If null, graph may emit a clarifying-questions event and stop",
    )
    plan_id: str | None = Field(
        default=None,
        description="If continuing a previous conversation, the plan id to attach to",
    )


class ChatStreamEvent(BaseModel):
    """One server-sent event from /api/chat.

    The event types are deliberately string-typed (not enum) so we can
    add new ones without breaking the frontend contract.
    """

    event: Literal[
        "init",
        "phase_start",
        "phase_complete",
        "clarify",
        "red_team",
        "diff",
        "chat_reply",
        "synthesizer",
        "done",
        "error",
    ]
    phase_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class PlanResponse(BaseModel):
    """GET /api/plan/{plan_id} response."""

    plan: FullPlan


class PlanSummary(BaseModel):
    """One row in GET /api/plans."""

    id: str
    title: str
    status: str
    total_cost_usd: float
    created_at: str
    updated_at: str


class PlanListResponse(BaseModel):
    plans: list[PlanSummary]
