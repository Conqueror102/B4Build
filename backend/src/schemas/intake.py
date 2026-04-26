"""User intake: the raw idea plus answers to clarifying questions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntakeAnswers(BaseModel):
    """What the user told us before the graph starts running phases.

    ``idea`` is the original free-text prompt. ``answers`` is the dict the
    coordinator's clarifying questions get answered into. Phase 4 will turn
    this into a multi-turn conversation; for Phase 1 we accept either an
    empty dict (graph asks for clarifications) or a populated one (graph
    runs end-to-end).
    """

    idea: str = Field(min_length=10, description="User's natural-language project idea")
    answers: dict[str, str] = Field(
        default_factory=dict,
        description="phase_id or question_key -> user's answer",
    )

    def is_complete(self) -> bool:
        """We treat the intake as 'complete enough to run' if any answers exist
        OR the idea is detailed enough (heuristic: > 80 chars).

        Coordinator can override by setting ``state.metadata['skip_clarify'] = True``.
        """
        return bool(self.answers) or len(self.idea) > 80
