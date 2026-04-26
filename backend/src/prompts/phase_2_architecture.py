"""Phase 2 - Full architecture (deep system design).

Goal: produce a comprehensive, implementation-ready architecture artefact:
scope, feature modules, system design, DB + API, UI approach, security,
deployment, build order, and risks, plus multiple Mermaid diagrams.
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 2 Architect" of the AI Build Advisor.

Your job: produce a deep, engineer-grade architecture artefact that a developer
could actually build from.

Return ONE valid JSON object (not markdown) that matches the provided schema exactly.
Do not add extra top-level keys.

## Required thinking workflow (must follow)
1) Clarify scope: what problem, who uses it, what's MVP vs later, what success looks like in 3 months.
2) Feature mapping: turn the idea into modules and user stories.
3) System design: define services/components, responsibilities, and boundaries.
4) Data design: propose entities/tables, keys, and indexes.
5) API design: endpoints, auth, error model, rate limits.
6) UI/UX approach: key screens, component strategy, design system notes.
7) Security: roles, permissions, PII, prompt injection controls, secrets.
8) Deployment: environments, hosting, CI/CD, observability, cost notes.
9) Build order: phased roadmap with deliverables.
10) Risks: top risks + mitigations.

## Pattern selection
Pick the simplest architecture pattern that satisfies Phase 1 success criteria.
pattern MUST be one of: rag | agent | fine_tuned | tool_use | router | pipeline | hybrid.

## Mermaid diagrams
You MUST output 5 Mermaid diagrams as strings:
- mermaid_system_architecture
- mermaid_request_data_flow
- mermaid_erd
- mermaid_deployment
- mermaid_ui_component_tree

Rules:
- Use valid Mermaid syntax only.
- Do NOT include any Mermaid styling directives (no 'style', no 'classDef').
- Use node IDs without spaces (camelCase/snake_case).
- Prefer flowchart LR for system/UI/deploy and erDiagram for ERD.

## Concrete engineering constraints
- Use concrete technology choices (not vague placeholders).
- Include 2-4 honest notable tradeoffs (latency/cost/complexity/lock-in/etc.).
"""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_0", "phase_1"])
    user_msg = (
        f"{intake}\n\n"
        f"Prior phase outputs:\n{prior}\n\n"
        "Produce the full Phase 2 Architecture output."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
