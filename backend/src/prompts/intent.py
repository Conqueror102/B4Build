"""Intent classification schemas for Phase 4."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    intent: Literal[
        "start_new", "edit", "what_if", "deep_dive", "challenge", "clarify_response", "chat"
    ] = Field(description="The user's core intent in their message")
    affected_phases: list[str] | None = Field(
        description=(
            "List of canonical phase IDs affected by the intent, if it's an edit or what_if. "
            "Use ids from the registry, e.g. 'phase_0', 'phase_2', 'phase_6_25', 'phase_6_5'. "
            "Do NOT use display ids like 'P2'."
        )
    )
    target_phase: str | None = Field(
        description=(
            "Specific canonical phase ID being challenged or deep-dived, if applicable "
            "(e.g. 'phase_2'). Do NOT use display ids like 'P2'."
        )
    )
    needs_clarification: bool = Field(
        description="True ONLY if the user's request is extremely vague and we must ask a clarifying question before proceeding"
    )
    clarifying_question: str | None = Field(
        description="If needs_clarification is True, the specific question to ask the user"
    )
