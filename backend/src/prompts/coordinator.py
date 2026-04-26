"""Coordinator prompt - asks clarifying questions before the phase loop.

Used when the user's intake is too thin to run the phases meaningfully.
The coordinator emits 3-5 short questions; the frontend renders them as a
form, the user replies, and the next /api/chat call runs the full graph.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ._shared import render_intake


class ClarifyingQuestion(BaseModel):
    key: str = Field(description="snake_case identifier the answer will be stored under")
    question: str = Field(description="The actual question to show the user")
    why_we_ask: str = Field(description="One sentence explaining why this matters")


class ClarifyingQuestions(BaseModel):
    questions: list[ClarifyingQuestion] = Field(min_length=1, max_length=5)


SYSTEM = """You are the "Coordinator" of the AI Build Advisor.

The user gave us a short idea and we need a bit more context before we can
produce a useful plan. Ask 3-5 clarifying questions, no more.

Pick questions whose answers will MATERIALLY change downstream phases:
- Domain (medical/legal/finance flips Phase 0 guardrails)
- Scale (req/day - drives Phase 5 cost model)
- Latency budget (P95 ms - flips Phase 2 architecture)
- Data sensitivity (PII/PHI - drives Phase 6.25)
- Existing tech stack (Postgres / GCP / Vercel - constrains Phase 4)
- Solo or team build (drives Phase 3 tools and OSS picks)

Each question must be ONE sentence and answerable in <30 seconds. Avoid
yes/no questions when a short text answer is more informative."""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    user_msg = (
        f"{intake}\n\nGenerate the ClarifyingQuestions to ask before we start the phase loop."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
