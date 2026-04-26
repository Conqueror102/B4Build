"""Phase 5 - Cost model.

The LLM anchors **stack, tools, and infrastructure** to dollars (line items) and
still copies a **deterministic** API token cost table from ``cost_calculator``.

CRITICAL: the ``scenarios[*].monthly_cost_usd`` values are NOT for the model to
recompute; they come from ``src.tools.cost_calculator`` (Python) and must be
copied verbatim.
"""

from __future__ import annotations

from typing import Any

from ..tools.cost_calculator import CostCalculatorInput, calculate_costs, format_for_prompt
from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 5 Cost Model" advisor.

You receive (1) the user's prior phases, including **architecture, tools, and
infrastructure**, and (2) a **precomputed** deterministic table of LLM API
token costs for several request-volume scenarios. Your job is both:

1) **Stack & tools (from the plan)**: build ``line_items`` that tie real cost
   drivers to *named* things from the prior phases. Each row should say what
   the money is for, whether it is typically **free, usage-based, fixed
   recurring, one-time, or mixed**, and honest **monthly_min_usd** /
   **monthly_max_usd** *ranges when you can justify them* from public free-tier
   or list pricing. If you cannot know the price, set both to null and explain
   in **notes** (e.g. "check vendor pricing; often $0 on free tier for MVP").

2) **Deterministic API usage (table)**: copy **scenarios** from the table
   verbatim. Do **not** recompute **monthly_cost_usd** or change the scenario
   labels/counts. Add a short **notes** per scenario naming the model/provider
   the table assumes (e.g. gpt-4o-mini) if helpful.

3) **Narrative**: **stack_cost_summary** = how the P2 + P3 + P4 choices
   together drive monthly spend and what is usually free at MVP.
   **mvp_getting_started_note** = in what order to open
   budgets (hosting, DB, auth, API keys, observability) for a shippable MVP.

Return ONE JSON object (not markdown) with EXACTLY these top-level keys:
- line_items
- stack_cost_summary
- mvp_getting_started_note
- scenarios
- primary_cost_driver
- optimization_opportunities
- self_host_breakeven_requests_per_month

**line_items** (minimum 5 rows when prior phases are detailed): cover at
least: LLM/inference, hosting/edge, database/storage, search or vector (if
in arch/infra), auth (if any), one observability/CI or API tool from P3–P4, and
anything else that is clearly a paid or usage line. Use **tied_to** with
   clear references like "P2: RAG", "P3: [tool from tools phase]", "P4 MVP: [layer name]".
   Mark honestly **free** only when the product has a true free tier or
is self-hostable with no license fee; do not label paid SaaS as free.

**self_host_breakeven_requests_per_month**: copy from the deterministic table
when present; else null.

Do NOT invent new scenario rows. Do NOT change the dollar amounts in
**scenarios** — they are computed in Python."""


def _default_scenarios() -> list[CostCalculatorInput]:
    """Three default scale tiers if the user hasn't specified their own."""
    return [
        CostCalculatorInput(
            label="Pilot (1k req/day)",
            monthly_requests=30_000,
            avg_input_tokens=2_000,
            avg_output_tokens=400,
        ),
        CostCalculatorInput(
            label="Growth (10k req/day)",
            monthly_requests=300_000,
            avg_input_tokens=2_000,
            avg_output_tokens=400,
        ),
        CostCalculatorInput(
            label="Scale (100k req/day)",
            monthly_requests=3_000_000,
            avg_input_tokens=2_000,
            avg_output_tokens=400,
            self_host_gpu_usd_per_hour=1.10,
        ),
    ]


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = _default_scenarios()
    results = calculate_costs(scenarios)
    table = format_for_prompt(results)

    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_1", "phase_2", "phase_3", "phase_4"])

    user_msg = (
        f"{intake}\n\n"
        f"Prior phase outputs (use names from here for line_items; do not ignore Phase 3):\n{prior}\n\n"
        "Deterministic LLM API cost table (copy **monthly_cost_usd** and scenario\n"
        "request counts/labels from this; do your own math for line_items when pricing tools — "
        "not for these rows):\n"
        f"{table}\n\n"
        "Fill the CostModel schema. The scenario **monthly_cost_usd** values are fixed by the table above; "
        "everything else (line_items, summaries, notes) is grounded in the prior phases."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
