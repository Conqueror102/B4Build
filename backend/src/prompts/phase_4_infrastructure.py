"""Phase 4 — Dynamic infrastructure (MVP + production layers + diagrams)."""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 4 Infrastructure" planner.

Output ONE JSON object (not markdown) with the exact keys the schema requires.

## Shape
- `mvp`: array of layers. Each layer: `name` (short title), `details` (one paragraph),
  optional `bullets` (0+ strings).
- `production`: same structure for the production-grade design.
- `summary_bullets`: 3-7 very short strings for an exec scan (optional but recommended).

## Rules
- **Idea-driven only:** include a layer ONLY if it matters for THIS product. Do NOT
  add placeholder layers (e.g. "vector database") unless Phase 2's architecture
  actually needs that kind of system. If the app has no async messaging, do not
  invent a queue layer.
- MVP layers should read as **actionable** (what to provision first). Production
  layers add reliability, security, scale, observability, backups, and cost controls
  **where relevant**.
- Use Phase 2 (architecture) and Phase 3 (tools / repos / APIs) as sources of truth.

## graduation_path
Ordered steps to evolve MVP → production without a full rewrite.

## Mermaid (three strings)
- `mermaid_mvp_stack`: `flowchart TB` or `flowchart LR` — real MVP data path only.
- `mermaid_production_stack`: production topology; only components you described.
- `mermaid_mvp_to_production`: one diagram showing how MVP grows into production.

No HTML, no `style` directives. Short labels.

## summary_bullets
Concrete fragments (e.g. "Vercel + Railway MVP", "RDS Multi-AZ prod", "OpenAI API")."""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_2", "phase_3"])
    user_msg = (
        f"{intake}\n\n"
        f"Prior architecture and Phase 3 tools/OSS context:\n{prior}\n\n"
        "Produce the infrastructure JSON. MVP must be cheap to operate; production "
        "must be defensible for real users. Diagrams must differ (MVP / prod / path). "
        "Omit entire layers that do not apply—do not pad with generic cloud blocks."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
