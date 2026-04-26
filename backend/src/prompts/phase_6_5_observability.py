"""Phase 6.5 - Observability.

Reference: AI Advisor doc, Table 6.5.
What we measure, where signals go, how we evaluate quality, and which
alerts wake someone up.
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 6.5 Observability" advisor.

Define what the team will measure once this thing is running, and where the
signals go.

Return ONE valid JSON object (not markdown, not a JSON Schema) with EXACTLY
these top-level keys:
- metrics
- tracing_tool
- log_sink
- eval_strategy
- alerting

metrics: 5-8 specific metrics. Each one should be a noun + threshold or
percentile, e.g. "p95 end-to-end latency (ms)", "schema validation failure
rate (%)", "cost per request (USD)", "retrieval precision@5", "user thumbs-up
rate". Avoid generic metrics like "uptime".

tracing_tool: pick one - LangSmith (default for OpenAI), Langfuse (open
source self-host), Phoenix (Arize, eval-heavy), or "OTel + Tempo" if the
team already runs OTel.

log_sink: name the actual destination - CloudWatch, Datadog, Better Stack,
Grafana Loki, etc.

eval_strategy: must cover BOTH:
- Offline: how do you build the golden set and what tool runs the eval
  (promptfoo, deepeval, custom pytest, LangSmith datasets).
- Online: what % of live traffic gets sampled into the eval set, and is
  there a human-in-the-loop step (rubric, annotators).

alerting: 3-5 concrete rules with thresholds. Example:
"PagerDuty if schema_failure_rate > 5% over 5 min" -- not "alert when bad".

Example shape (values are illustrative):
{"metrics":["..."],"tracing_tool":"...","log_sink":"...","eval_strategy":"...","alerting":["..."]}"""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_1", "phase_2", "phase_4"])
    user_msg = (
        f"{intake}\n\n"
        f"Prior phase outputs:\n{prior}\n\n"
        "Produce the ObservabilityPlan. Tailor metrics and alerts to the "
        "success criteria from Phase 1."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
