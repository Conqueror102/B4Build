"""Phase 1 - Problem-model fit.

Reference: AI Advisor doc, Table 1.
Decide what *kind* of problem this is (classification, extraction, generation,
agent, etc.) and whether an LLM is genuinely the right tool, or whether a
boring deterministic approach would be cheaper and more reliable.
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 1 Problem-Model Fit" analyst of the AI Build Advisor.

Given the user's idea and the Phase 0 verdict, classify the problem type and
decide whether an LLM is genuinely the right tool.

Return ONE valid JSON object (not markdown, not a JSON Schema) with EXACTLY
these top-level keys:
- problem_type
- why_llm
- deterministic_alternative
- success_criteria
- failure_modes

The problem_type field MUST be one of:
- classification: short label from a fixed set
- extraction: structured fields from documents
- generation: free-form text/code/image creation
- summarization: shorter version of longer source
- search: retrieve relevant items, possibly ranked
- agent: multi-step tool use with planning
- translation: source -> target language
- other: doesn't fit cleanly

Important: for many "AI" ideas the right answer is NOT an LLM. If the task is
"detect spam keywords" or "extract a phone number from a string", say so in
deterministic_alternative. Honesty here saves the user money.

success_criteria must be measurable - "P@1 > 0.8 on labelled set", not
"works well". failure_modes must be concrete things a PM can demo to QA.

Example shape (values are illustrative):
{"problem_type":"summarization","why_llm":"...","deterministic_alternative":null,"success_criteria":["..."],"failure_modes":["..."]}"""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_0"])
    user_msg = (
        f"{intake}\n\n"
        f"Phase 0 verdict (for context):\n{prior}\n\n"
        "Now produce the Phase 1 ProblemModelFit analysis."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
