"""Pydantic models for each advisor phase output.

One model per phase. The names mirror the advisor doc:

- Phase 0   -> PressureTestResult
- Phase 1   -> ProblemModelFit
- Phase 2   -> Architecture
- Phase 3   -> ToolsOpenSourcePhase (legacy stored as BuildBuyTrain)
- Phase 4   -> Infrastructure (list-based layers; legacy shapes migrated on read)
- Phase 5   -> CostModel (stack line_items + deterministic LLM usage scenarios; legacy on read)
- Phase 6.25 -> SecurityPlan
- Phase 6.5  -> ObservabilityPlan
- Phase 7   -> ScalingPlan

These models are passed both to ``LLMClient.complete_structured`` (where
they constrain the OpenAI ``json_schema`` response format) and to the
synthesizer (which copies them into the final ``FullPlan``).

Keep field descriptions short - they are sent to the model as part of the
schema and counted as input tokens.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class PressureTestResult(BaseModel):
    """Phase 0 - is this idea worth pursuing at all?"""

    is_viable: bool = Field(description="Whether the idea is worth building right now")
    refusal_reason: str | None = Field(
        default=None,
        description="If refusing, the specific guardrail that triggered (e.g. medical, legal)",
    )
    summary: str = Field(description="2-3 sentence verdict")
    similar_existing_solutions: list[str] = Field(
        default_factory=list,
        description="Off-the-shelf products that already do this; <=5 items",
    )
    differentiators: list[str] = Field(
        default_factory=list,
        description="What would make the user's version meaningfully different",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="High-level risks to flag before continuing",
    )


class ProblemModelFit(BaseModel):
    """Phase 1 - is the problem actually a good fit for an LLM?"""

    problem_type: Literal[
        "classification",
        "extraction",
        "generation",
        "summarization",
        "search",
        "agent",
        "translation",
        "other",
    ]
    why_llm: str = Field(description="Why an LLM is (or is not) the right tool")
    deterministic_alternative: str | None = Field(
        default=None,
        description="A non-LLM approach that might be simpler, if applicable",
    )
    success_criteria: list[str] = Field(
        description="Measurable signals the system is working (e.g. P@1 > 0.8)"
    )
    failure_modes: list[str] = Field(description="What 'going wrong' looks like in production")


class ArchitectureComponent(BaseModel):
    name: str
    purpose: str
    technology: str = Field(
        description="Concrete tech choice (e.g. 'pgvector', 'OpenAI gpt-4o-mini')"
    )


class ScopeDefinition(BaseModel):
    problem_why: str = Field(description="What problem this solves and why it matters")
    personas_and_roles: list[str] = Field(description="Primary user personas and roles")
    mvp_definition: list[str] = Field(description="What is in MVP vs what is later")
    success_in_3_months: list[str] = Field(description="What success looks like in ~3 months")


class UserStory(BaseModel):
    as_a: str
    i_want: str
    so_that: str


class FeatureModule(BaseModel):
    name: str
    description: str
    user_stories: list[UserStory] = Field(min_length=1)


class ServiceComponent(BaseModel):
    name: str
    responsibility: str
    technology: str
    scaling_notes: str | None = None


class DataEntity(BaseModel):
    name: str = Field(description="Table/collection name")
    primary_key: str
    fields: list[str] = Field(description="Key fields/columns (name:type)")
    indexes: list[str] = Field(default_factory=list, description="Important indexes")
    relationships: list[str] = Field(
        default_factory=list,
        description="Relationships (e.g. 'users 1->many projects')",
    )


class ApiEndpoint(BaseModel):
    method: str = Field(description="HTTP method (GET/POST/PUT/DELETE)")
    path: str = Field(description="Path, e.g. /api/plan/{id}")
    purpose: str
    auth: str | None = Field(default=None, description="Auth requirement/role")


class ApiDesign(BaseModel):
    style: str = Field(description="REST or GraphQL; brief rationale")
    auth_strategy: str = Field(description="JWT/session/OAuth and why")
    error_model: str = Field(description="How errors are shaped and surfaced")
    rate_limiting: str = Field(description="Rate limits and where enforced")
    endpoints: list[ApiEndpoint] = Field(min_length=3)


class UiUxApproach(BaseModel):
    key_screens: list[str] = Field(description="Screens to build first")
    component_tree_notes: str = Field(description="Reusable components + hierarchy notes")
    design_system_notes: str = Field(description="Colors/typography/spacing philosophy")
    mobile_strategy: str = Field(description="Mobile-first/desktop-first + rationale")


class SecurityDesign(BaseModel):
    roles_and_permissions: list[str]
    pii_handling: str
    prompt_injection_controls: list[str]
    secrets_and_keys: list[str]
    security_basics: list[str] = Field(description="Rate limiting, validation, audit logging, etc.")


class DeploymentPlan(BaseModel):
    environments: list[str] = Field(description="dev/staging/prod strategy")
    hosting: str
    ci_cd: str
    observability: str
    cost_notes: str | None = None


class BuildPhase(BaseModel):
    phase: str
    goal: str
    deliverables: list[str]


class RiskItem(BaseModel):
    risk: str
    impact: str
    mitigation: str


class Architecture(BaseModel):
    """Phase 2 - full reference architecture (deep)."""

    pattern: Literal[
        "rag",
        "agent",
        "fine_tuned",
        "tool_use",
        "router",
        "pipeline",
        "hybrid",
    ]
    # High-level system breakdown
    scope_definition: ScopeDefinition
    feature_modules: list[FeatureModule] = Field(min_length=3)
    system_architecture: list[ServiceComponent] = Field(min_length=4)

    # Keep the original fields for backwards compatibility / quick scan
    components: list[ArchitectureComponent] = Field(min_length=2)
    data_flow: str = Field(description="Step-by-step request walkthrough")
    notable_tradeoffs: list[str]

    # Deep design
    data_model: list[DataEntity] = Field(min_length=3)
    api_design: ApiDesign
    ui_ux_approach: UiUxApproach
    security_design: SecurityDesign
    deployment_plan: DeploymentPlan
    build_phases: list[BuildPhase] = Field(min_length=3)
    risk_analysis: list[RiskItem] = Field(min_length=3)

    # Mermaid diagrams (no styling directives)
    mermaid_system_architecture: str
    mermaid_request_data_flow: str
    mermaid_erd: str
    mermaid_deployment: str
    mermaid_ui_component_tree: str


class OpenSourceRepo(BaseModel):
    """An open-source repository recommendation."""

    name: str = Field(description="Repository name (owner/repo)")
    url: str = Field(description="GitHub URL")
    stars: int = Field(description="Number of stars")
    why_relevant: str = Field(description="Why this repo fits the project")
    how_to_integrate: str = Field(description="How to use it in the architecture")
    license: str | None = Field(description="License type (MIT, Apache, GPL, etc.)")
    license_risks: str = Field(description="Any licensing concerns or restrictions")
    last_updated: str = Field(description="Last update date")


class BuildBuyTrain(BaseModel):
    """Legacy Phase 3 — build/buy/train (kept for parsing old stored plans only)."""

    recommendation: Literal["build", "buy", "fine_tune", "hybrid", "compose_oss"]
    rationale: str

    open_source_candidates: list[OpenSourceRepo] = Field(
        default_factory=list,
        description="Top open-source repositories that could be used",
    )
    recommended_stack_from_oss: str | None = Field(
        default=None,
        description="How to compose the recommended OSS projects together",
    )
    integration_plan: list[str] = Field(
        default_factory=list,
        description="Steps to integrate the OSS components",
    )

    candidate_vendors: list[str] = Field(
        default_factory=list,
        description="Off-the-shelf products to evaluate",
    )
    fine_tune_recommended: bool = Field(default=False)
    fine_tune_dataset_size_estimate: int | None = Field(
        default=None,
        description="If fine-tuning, ballpark labelled examples needed",
    )


class GitHubSearchContext(BaseModel):
    """How GitHub search was run for Phase 3 (may be empty)."""

    query_used: str | None = Field(default=None, description="Search string sent to GitHub")
    repo_count_returned: int = Field(default=0, ge=0, description="Repos passed into the prompt")
    total_count_estimate: int | None = Field(
        default=None,
        description="GitHub total_count if available",
    )
    search_note: str | None = Field(
        default=None,
        description="One line, e.g. rate limited or no matches",
    )


class ManagedToolRecommendation(BaseModel):
    """SaaS, SDK, or managed product (not necessarily on GitHub)."""

    name: str = Field(description="Product or vendor name")
    category: str = Field(description="Short label, e.g. Video, Auth, Email")
    role_in_app: str = Field(description="What it does in this product")
    rationale: str = Field(description="Why this pick for this idea")
    product_url: str | None = Field(default=None, description="Canonical URL if known")


class ToolsOpenSourcePhase(BaseModel):
    """Phase 3 — concrete tools/services + curated GitHub repos (no build/buy enum)."""

    search_context: GitHubSearchContext = Field(
        description="Echo search metadata; always include (use zeros when search failed)",
    )
    github_recommendations: list[OpenSourceRepo] = Field(
        default_factory=list,
        description="Prioritize repos from the search list when provided; else empty",
    )
    managed_tools: list[ManagedToolRecommendation] = Field(
        min_length=1,
        description="At least one concrete tool or vendor the build should use",
    )
    integration_summary: str = Field(
        description="How repos + managed tools fit together for this product",
    )


class InfraLayer(BaseModel):
    """One named slice of infrastructure (idea-specific, no fixed categories)."""

    name: str = Field(description="Short title, e.g. Model inference, Data store, Realtime")
    details: str = Field(description="Paragraph: what, where, why for this product")
    bullets: list[str] = Field(
        default_factory=list,
        description="Optional checklist under this layer",
    )


class Infrastructure(BaseModel):
    """Phase 4: idea-specific infra layers (MVP + production) + diagrams."""

    mvp: list[InfraLayer] = Field(
        min_length=1,
        description="Only layers this product needs at MVP; omit categories that do not apply",
    )
    production: list[InfraLayer] = Field(
        min_length=1,
        description="Production-grade view; only layers that apply",
    )
    graduation_path: str = Field(
        description="How to grow MVP to prod: order of migrations, what to keep vs replace"
    )
    mermaid_mvp_stack: str = Field(description="Mermaid: MVP components and data path")
    mermaid_production_stack: str = Field(
        description="Mermaid: production stack with failure domains"
    )
    mermaid_mvp_to_production: str = Field(
        description="Mermaid: side-by-side or flow showing graduation"
    )
    summary_bullets: list[str] = Field(
        default_factory=list,
        description="3-7 short bullets for exec scan (hosting, inference, cost posture, etc.)",
        max_length=12,
    )


def normalize_infrastructure_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert legacy infrastructure JSON into the current Infrastructure shape."""
    if not raw:
        return raw
    if isinstance(raw.get("mvp"), list):
        return raw
    # Legacy flat (hosting + rationale only)
    if "mvp" not in raw or not isinstance(raw.get("mvp"), dict):
        bullets = [
            x
            for x in (
                f"Hosting: {raw.get('hosting')}" if raw.get("hosting") else None,
                f"Inference: {raw.get('inference_provider')}"
                if raw.get("inference_provider")
                else None,
                f"Vector: {raw.get('vector_store')}" if raw.get("vector_store") else None,
                f"Queue: {raw.get('queue')}" if raw.get("queue") else None,
                f"Secrets: {raw.get('secrets_manager')}" if raw.get("secrets_manager") else None,
            )
            if x
        ]
        rationale = raw.get("rationale") or "Legacy infrastructure snapshot."
        return {
            "mvp": [{"name": "Legacy summary (MVP)", "details": rationale, "bullets": bullets}],
            "production": [
                {
                    "name": "Legacy summary (production)",
                    "details": rationale,
                    "bullets": bullets,
                }
            ],
            "graduation_path": "Imported from an older plan format; regenerate for a full layer-based infra pass.",
            "mermaid_mvp_stack": "flowchart TB\nL[Legacy plan]\n",
            "mermaid_production_stack": "flowchart TB\nL[Legacy plan]\n",
            "mermaid_mvp_to_production": "flowchart LR\nA[Legacy] --> B[Regenerate]\n",
            "summary_bullets": bullets[:7] or [rationale[:200]],
        }
    # Legacy deep: mvp and production are objects
    mvp_obj = raw.get("mvp") or {}
    prod_obj = raw.get("production") or {}

    def _layer(title: str, body: str, extra: list[str]) -> dict[str, Any]:
        return {"name": title, "details": body or "—", "bullets": [b for b in extra if b][:12]}

    mvp_layers: list[dict[str, Any]] = []
    if isinstance(mvp_obj, dict):
        mvp_layers.append(
            _layer(
                "MVP philosophy",
                str(mvp_obj.get("philosophy", "")),
                [
                    f"Inference: {mvp_obj.get('inference_and_models')}",
                    f"Frontend: {mvp_obj.get('frontend_hosting')}",
                    f"Backend: {mvp_obj.get('backend_api')}",
                    f"Database: {mvp_obj.get('database')}",
                ],
            )
        )
        def_list = mvp_obj.get("explicitly_deferred_to_production") or []
        if isinstance(def_list, list) and def_list:
            mvp_layers.append(
                _layer(
                    "Deferred to production",
                    "Items intentionally skipped at MVP.",
                    [str(x) for x in def_list],
                )
            )
    if not mvp_layers:
        mvp_layers = [_layer("MVP", raw.get("rationale") or "—", [])]

    prod_layers: list[dict[str, Any]] = []
    if isinstance(prod_obj, dict):
        prod_layers.append(
            _layer(
                "Production posture",
                str(prod_obj.get("philosophy", "")),
                [
                    f"Cloud: {prod_obj.get('primary_cloud')}",
                    f"Compute: {prod_obj.get('compute_and_serving')}",
                    f"Data: {prod_obj.get('database_and_persistence')}",
                ],
            )
        )
        ch = prod_obj.get("what_changes_from_mvp") or []
        if isinstance(ch, list) and ch:
            prod_layers.append(
                _layer(
                    "Changes from MVP", "Upgrades when moving to production.", [str(x) for x in ch]
                )
            )
    if not prod_layers:
        prod_layers = [_layer("Production", raw.get("rationale") or "—", [])]

    return {
        "mvp": mvp_layers,
        "production": prod_layers,
        "graduation_path": raw.get("graduation_path")
        or "See prior plan version for full graduation narrative.",
        "mermaid_mvp_stack": raw.get("mermaid_mvp_stack") or "flowchart TB\nL[Legacy MVP]\n",
        "mermaid_production_stack": raw.get("mermaid_production_stack")
        or "flowchart TB\nL[Legacy production]\n",
        "mermaid_mvp_to_production": raw.get("mermaid_mvp_to_production")
        or "flowchart LR\nA[MVP] --> B[Production]\n",
        "summary_bullets": [
            x
            for x in (
                raw.get("hosting"),
                raw.get("inference_provider"),
                raw.get("secrets_manager"),
            )
            if x
        ],
    }


class CostScenario(BaseModel):
    label: str = Field(description="e.g. 'Pilot - 1k requests/day'")
    monthly_requests: int
    avg_input_tokens: int
    avg_output_tokens: int
    monthly_cost_usd: float = Field(
        description="Computed by deterministic calculator, not LLM math"
    )
    notes: str | None = None


CostKind = Literal["free", "variable_usage", "fixed_recurring", "one_time", "mixed"]


class CostLineItem(BaseModel):
    """One row: tool / infra cost tied back to prior phases."""

    item: str = Field(description="Short label, e.g. 'Vercel (frontend)' or 'OpenAI API'")
    tied_to: str = Field(description="Traceability: e.g. P2 component, P3 tool name, P4 layer name")
    cost_kind: CostKind
    monthly_min_usd: float | None = Field(
        default=None, description="Lower monthly $ if knowable; null if free or unknown"
    )
    monthly_max_usd: float | None = Field(
        default=None, description="Upper monthly $; null if N/A or unknown"
    )
    notes: str = Field(description="Free tier, usage-based math, or caveats; keep concise")


def normalize_cost_model_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Fill Phase 5 fields missing from older stored plans."""
    if not raw or not isinstance(raw, dict):
        return raw
    out = dict(raw)
    items = out.get("line_items")
    if not isinstance(items, list) or len(items) < 1:
        out["line_items"] = [
            {
                "item": "LLM / inference (API usage — see scenario table below)",
                "tied_to": "Phase 2 (model path) and Phase 4 (inference provider)",
                "cost_kind": "variable_usage",
                "monthly_min_usd": None,
                "monthly_max_usd": None,
                "notes": "Dollar amounts for token usage are in the deterministic table; regenerate this phase for a line-by-line stack breakdown.",
            },
            {
                "item": "Application hosting, database, and core cloud services",
                "tied_to": "Phase 4 (infrastructure layers)",
                "cost_kind": "mixed",
                "monthly_min_usd": None,
                "monthly_max_usd": None,
                "notes": "Re-run the cost phase to mark each provider as free vs paid at your expected scale.",
            },
            {
                "item": "Auth, CI, and third-party tools from your tools list",
                "tied_to": "Phases 3 & 4 (tools + security/observability choices)",
                "cost_kind": "fixed_recurring",
                "monthly_min_usd": None,
                "monthly_max_usd": None,
                "notes": "Often $0 on free tiers at low scale; re-import for per-tool estimates.",
            },
        ]
    if not (out.get("stack_cost_summary") or "").strip():
        out["stack_cost_summary"] = (
            "The scenario table below shows deterministic API token cost at the assumed request volume. "
            "Re-run the cost phase to tie each line item to your architecture, tools, and infrastructure."
        )
    if not (out.get("mvp_getting_started_note") or "").strip():
        out["mvp_getting_started_note"] = (
            "Plan for the smallest paid tiers you need to go live (hosting, DB, auth) plus variable LLM spend from the "
            "pilot row in the table; add observability and CI when you leave the solo-dev stage."
        )
    return out


class CostModel(BaseModel):
    """Phase 5 - stack-anchored cost plus deterministic LLM-usage scenarios.

    ``line_items`` connect dollars to the chosen architecture, tools, and
    infrastructure. The numeric ``scenarios[*].monthly_cost_usd`` values come
    from ``src.tools.cost_calculator`` (Python) — the model must copy them.
    """

    line_items: list[CostLineItem] = Field(
        min_length=1,
        description="At least one row; prefer 5+ covering P2-P4 by name",
    )
    stack_cost_summary: str = Field(
        description="2-4 sentences on how the stack (arch + tools + infra) maps to $"
    )
    mvp_getting_started_note: str = Field(
        description="What to budget to ship MVP: paid tiers, deposit, and order of spend"
    )
    scenarios: list[CostScenario] = Field(min_length=1)
    primary_cost_driver: str
    optimization_opportunities: list[str]
    self_host_breakeven_requests_per_month: int | None = Field(
        default=None,
        description="At what volume self-hosting beats API; null if never",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return normalize_cost_model_payload(data)
        return data


class SecurityPlan(BaseModel):
    """Phase 6.25 - security and compliance checklist."""

    threats: list[str] = Field(description="OWASP-LLM and project-specific threats")
    pii_handling: str = Field(description="How user PII is detected, masked, or excluded")
    prompt_injection_mitigations: list[str]
    rate_limiting: str
    auth_strategy: str
    compliance_notes: list[str] = Field(
        default_factory=list,
        description="GDPR / HIPAA / SOC2 considerations if relevant",
    )


class ObservabilityPlan(BaseModel):
    """Phase 6.5 - what we measure and where signals go."""

    metrics: list[str] = Field(description="e.g. p95 latency, cost per request, schema-fail rate")
    tracing_tool: str = Field(description="LangSmith / Phoenix / OTel collector")
    log_sink: str = Field(description="Where structured logs go in prod")
    eval_strategy: str = Field(description="Offline evals + online sampling approach")
    alerting: list[str] = Field(description="Specific alert rules and thresholds")


class ScalingPlan(BaseModel):
    """Phase 7 - what breaks at 10x and how we'd fix it."""

    bottlenecks_at_10x: list[str]
    bottlenecks_at_100x: list[str]
    caching_strategy: str
    failover_strategy: str = Field(description="Multi-provider / multi-region story")
    cost_at_scale_concerns: list[str]
