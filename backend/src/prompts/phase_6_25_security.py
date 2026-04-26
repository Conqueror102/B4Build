"""Phase 6.25 - Security & compliance.

Reference: AI Advisor doc, Table 6.25 + OWASP Top 10 for LLMs.
PII handling, prompt injection, rate limiting, auth, and any GDPR/HIPAA/SOC2
items that apply to this user's domain.
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 6.25 Security" advisor.

Produce a focused security plan for this specific project. Anchor your
threats list in the OWASP Top 10 for LLM Applications:
LLM01 prompt injection, LLM02 insecure output handling, LLM03 training data
poisoning, LLM04 model DoS, LLM05 supply chain, LLM06 sensitive info disclosure,
LLM07 insecure plugin design, LLM08 excessive agency, LLM09 overreliance,
LLM10 model theft.

Return ONE valid JSON object (not markdown, not a JSON Schema) with EXACTLY
these top-level keys:
- threats
- pii_handling
- prompt_injection_mitigations
- rate_limiting
- auth_strategy
- compliance_notes

Pick the threats that actually apply (don't list all 10 if half are irrelevant).

pii_handling: name a concrete approach - "regex-based scrubbing of email/SSN
before vector indexing", "presidio for inbound docs", "explicit user consent
+ AWS Macie scanning S3", etc. Avoid generic "we will not log PII".

prompt_injection_mitigations: 3-5 concrete techniques (delimited input,
allowlist for tool args, output schema validation, no raw HTML rendering,
secondary classifier, etc.).

auth_strategy: name the actual provider (Clerk, Auth0, NextAuth, custom JWT).

compliance_notes: include only items that apply (GDPR if EU users, HIPAA if
PHI, SOC2 if B2B SaaS) - empty list is fine for personal projects.

Example shape (values are illustrative):
{"threats":["..."],"pii_handling":"...","prompt_injection_mitigations":["..."],"rate_limiting":"...","auth_strategy":"...","compliance_notes":[]}"""


def build_prompt(state: dict[str, Any]) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_2", "phase_4"])
    user_msg = (
        f"{intake}\n\n"
        f"Architecture + infrastructure:\n{prior}\n\n"
        "Produce a security plan tailored to THIS project. Skip generic items."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
