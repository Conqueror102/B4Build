"""Phase 7 - Scaling & resilience.

Reference: AI Advisor doc, Table 7.
Where does this break at 10x and 100x current scale, what do we cache, and
what's the multi-provider / multi-region failover story?
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 7 Scaling" advisor.

Reason about what breaks first when traffic grows by 10x and 100x relative
to the pilot scale from Phase 5. Be concrete about WHICH component fails
and HOW.

Return ONE valid JSON object (not markdown, not a JSON Schema) with EXACTLY
these top-level keys:
- bottlenecks_at_10x
- bottlenecks_at_100x
- caching_strategy
- failover_strategy
- cost_at_scale_concerns

bottlenecks_at_10x: 3-5 items, each naming a specific component
(e.g. "OpenAI rate limit on Tier 2 account", "single Postgres write node",
"vector search > 500ms when index > 10M chunks").

bottlenecks_at_100x: 3-5 items, ditto. These are usually qualitatively
different from the 10x list (cost/architecture changes, not just adding a
replica).

caching_strategy: name what gets cached and where (Redis-backed prompt
caching, response cache keyed on normalized query, embedding cache, CDN
edge cache for static assets).

failover_strategy: real plan. "If OpenAI is down, fall back to Anthropic
via LiteLLM router with the same prompt template" is good. "We will use a
multi-cloud strategy" is not.

cost_at_scale_concerns: things that grow super-linearly (re-embedding on
schema change, training data labelling, fine-tune jobs).

Example shape (values are illustrative):
{"bottlenecks_at_10x":["..."],"bottlenecks_at_100x":["..."],"caching_strategy":"...","failover_strategy":"...","cost_at_scale_concerns":["..."]}"""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_2", "phase_4", "phase_5"])
    user_msg = (
        f"{intake}\n\n"
        f"Prior phase outputs:\n{prior}\n\n"
        "Produce the ScalingPlan. Be specific about which component breaks "
        "and what the fix looks like."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
