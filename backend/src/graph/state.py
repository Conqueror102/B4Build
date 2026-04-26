"""Shared graph state.

LangGraph requires a TypedDict (or Pydantic model) describing what every
node reads and writes. Each node returns a dict whose keys are merged into
this state by the framework.

Keep this file dependency-light - it imports schemas only for typing so the
module can be referenced from prompts without creating a cycle.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel

from ..schemas.plan import FullPlan, RedTeamCritique


class AdvisorState(TypedDict, total=False):
    """All data the LangGraph nodes share.

    ``total=False`` because LangGraph nodes can return partial dicts; the
    framework merges them into the running state.

    Keys
    ----
    idea
        The user's raw natural-language input.
    clarifying_answers
        ``question_key -> user_answer`` mapping (empty until the user replies
        to the coordinator's clarifying questions).
    phase_outputs
        ``phase_id -> validated Pydantic instance`` populated by ``phase_worker``.
    red_team
        Output of the ``red_team`` node, set after every phase completes.
    final_plan
        Set by ``synthesizer`` once the plan is fully built.
    messages
        Free-form chat transcript (system/user/assistant). Phase 4 will use
        this for multi-turn conversations.
    current_phase
        The phase id the worker is about to run, set by ``coordinator``.
    errors
        Per-node error strings. Set when a node fails so the SSE stream can
        emit ``{"event": "error", ...}`` without crashing the graph.
    total_cost_usd
        Running sum of LLM spend across phases.
    metadata
        Bag for request_id, user_id, plan_id, and feature flags.
    """

    idea: str
    clarifying_answers: dict[str, str]
    phase_outputs: dict[str, BaseModel]
    red_team: RedTeamCritique | None
    final_plan: FullPlan | None
    messages: Annotated[list[dict[str, Any]], operator.add]
    current_phase: str | None
    dirty_phases: list[str]
    research_context: list[str]
    errors: Annotated[list[str], operator.add]
    total_cost_usd: float
    metadata: dict[str, Any]


def new_state(
    idea: str,
    *,
    clarifying_answers: dict[str, str] | None = None,
    request_id: str,
    plan_id: str | None = None,
) -> AdvisorState:
    """Construct an initial state with sensible empty defaults."""
    return AdvisorState(
        idea=idea,
        clarifying_answers=clarifying_answers or {},
        phase_outputs={},
        red_team=None,
        final_plan=None,
        messages=[],
        current_phase=None,
        dirty_phases=[],
        research_context=[],
        errors=[],
        total_cost_usd=0.0,
        metadata={"request_id": request_id, "plan_id": plan_id},
    )
