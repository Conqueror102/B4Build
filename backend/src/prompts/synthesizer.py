"""Synthesizer - compile the final FullPlan.

The synthesizer node owns the executive summary + next-steps fields of
``FullPlan``. The phase outputs themselves are already typed Pydantic
instances; the synthesizer just needs to write the human-readable wrapper
the user actually reads.

To keep token cost low we only ask the LLM for the two narrative fields and
let the node code stitch the typed outputs into the FullPlan envelope.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ._shared import render_intake, render_prior_outputs


class SynthesizerOutput(BaseModel):
    executive_summary: str = Field(description="3-5 sentence TL;DR for the user")
    next_steps: list[str] = Field(description="3-7 concrete actions the user should take this week")


SYSTEM = """You are the "Synthesizer" of the AI Build Advisor.

You will receive available phase outputs and the red-team critique. Some phases
may be missing because the user selected a smaller template (partial plan).
Do NOT invent missing phase outputs.

1. executive_summary: 3-5 sentences a busy founder would read in the
   first email. Lead with the main tools / OSS choices from Phase 3, the
   architecture pattern (Phase 2), and the rough monthly cost at pilot
   scale (Phase 5). End with the single biggest red-team concern.

2. next_steps: 3-7 imperative bullets the user can do THIS WEEK. Each
   item must start with a verb ("Sign up for ...", "Run a 50-doc spike
   on ...", "Get a quote from ..."). No vague "explore further"."""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state)
    red_team = state.get("red_team")
    red_team_str = (
        red_team.model_dump_json(indent=2) if isinstance(red_team, BaseModel) else "(none)"
    )
    user_msg = (
        f"{intake}\n\n"
        f"Phase outputs (may be partial):\n{prior}\n\n"
        f"Red team critique:\n```json\n{red_team_str}\n```\n\n"
        "Produce the SynthesizerOutput."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
