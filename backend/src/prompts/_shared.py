"""Shared helpers for prompt builders.

Phase prompt modules import from here so they can stay tightly focused on
their own system + user message and not duplicate "render prior outputs"
boilerplate.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def render_prior_outputs(
    state: dict[str, Any],
    *,
    include: list[str] | None = None,
) -> str:
    """Render previously-completed phase outputs into a compact JSON block.

    The LLM gets a single ```json ... ``` fenced block for context, instead of
    one giant pasted prompt. Pass ``include=["phase_0", "phase_1"]`` to limit
    which phases the current phase actually needs.
    """
    outputs: dict[str, BaseModel] = state.get("phase_outputs", {}) or {}
    if include is not None:
        outputs = {k: v for k, v in outputs.items() if k in include}
    if not outputs:
        return "(no prior phase outputs yet)"

    rendered: dict[str, Any] = {}
    for phase_id, model in outputs.items():
        if isinstance(model, BaseModel):
            rendered[phase_id] = model.model_dump(mode="json")
        else:
            rendered[phase_id] = model

    return "```json\n" + json.dumps(rendered, indent=2, default=str) + "\n```"


def render_intake(state: dict[str, Any]) -> str:
    """Render the user's idea, clarifying answers, and conversation history."""
    idea = state.get("idea", "(no idea provided)")
    answers = state.get("clarifying_answers", {}) or {}

    out = f"User's original idea:\n{idea}\n\n"
    if answers:
        bullets = "\n".join(f"- {k}: {v}" for k, v in answers.items())
        out += f"Clarifying answers:\n{bullets}\n\n"

    messages = state.get("messages", [])
    # We skip the very first user message if it's identical to `idea`,
    # but `idea` might just be the first message.
    # Let's just render the messages that are iterations (e.g. beyond the first message)
    if len(messages) > 1:
        out += "Iteration History (changes requested by user):\n"
        for idx, m in enumerate(messages):
            # Only show subsequent iterations or AI responses
            if idx == 0 and m.get("content") == idea:
                continue
            role = m.get("role", "unknown")
            content = m.get("content", "")
            out += f"{role.upper()}: {content}\n"

    research = state.get("research_context")
    if research:
        out += "\n--- LIVE WEB RESEARCH CONTEXT ---\n"
        out += "Use the following live, up-to-date information to inform your analysis (especially for pricing, vendor features, or limits):\n\n"
        for idx, snippet in enumerate(research):
            out += f"Research Snippet {idx + 1}:\n{snippet}\n\n"
        out += "---------------------------------\n"

    return out
