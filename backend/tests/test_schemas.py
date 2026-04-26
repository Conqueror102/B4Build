"""Schemas serialise/round-trip cleanly.

We don't try to mock the LLM here - we just exercise the Pydantic models so
a typo in a Field declaration breaks fast.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.schemas.intake import IntakeAnswers
from src.schemas.phases import (
    Architecture,
    ArchitectureComponent,
    ApiDesign,
    ApiEndpoint,
    BuildBuyTrain,
    BuildPhase,
    CostLineItem,
    CostModel,
    CostScenario,
    DataEntity,
    GitHubSearchContext,
    InfraLayer,
    Infrastructure,
    ManagedToolRecommendation,
    OpenSourceRepo,
    ObservabilityPlan,
    PressureTestResult,
    ProblemModelFit,
    RiskItem,
    ScopeDefinition,
    FeatureModule,
    ServiceComponent,
    ToolsOpenSourcePhase,
    UiUxApproach,
    SecurityDesign,
    DeploymentPlan,
    UserStory,
    ScalingPlan,
    SecurityPlan,
    normalize_infrastructure_payload,
)
from src.schemas.plan import FullPlan, RedTeamCritique, RedTeamFinding


def _make_pressure_test() -> PressureTestResult:
    return PressureTestResult(
        is_viable=True,
        summary="Looks viable.",
        similar_existing_solutions=["Notion AI"],
        differentiators=["Self-host"],
        risks=["LLM cost"],
    )


def _make_problem_model_fit() -> ProblemModelFit:
    return ProblemModelFit(
        problem_type="summarization",
        why_llm="Summarization benefits from generative models.",
        success_criteria=["ROUGE-L > 0.4"],
        failure_modes=["Hallucinated facts"],
    )


def _make_architecture() -> Architecture:
    return Architecture(
        pattern="rag",
        scope_definition=ScopeDefinition(
            problem_why="Summarize and answer questions over documents.",
            personas_and_roles=["User", "Admin"],
            mvp_definition=["Upload docs", "Ask questions", "Citations"],
            success_in_3_months=["P@5 > 0.8", "p95 < 2s"],
        ),
        feature_modules=[
            FeatureModule(
                name="Auth",
                description="Sign-in and access control.",
                user_stories=[UserStory(as_a="User", i_want="to sign in", so_that="my data is private")],
            ),
            FeatureModule(
                name="Docs",
                description="Ingest and manage documents.",
                user_stories=[UserStory(as_a="Admin", i_want="to upload docs", so_that="they are searchable")],
            ),
            FeatureModule(
                name="Q&A",
                description="Ask questions and get cited answers.",
                user_stories=[UserStory(as_a="User", i_want="to ask questions", so_that="I get answers fast")],
            ),
        ],
        system_architecture=[
            ServiceComponent(name="Web", responsibility="UI", technology="Next.js"),
            ServiceComponent(name="API", responsibility="Auth + orchestration", technology="FastAPI"),
            ServiceComponent(name="DB", responsibility="Store docs + vectors", technology="Postgres+pgvector"),
            ServiceComponent(name="LLM", responsibility="Generate answers", technology="gpt-4o-mini"),
        ],
        components=[
            ArchitectureComponent(
                name="Embedder", purpose="Encode chunks", technology="text-embedding-3-small"
            ),
            ArchitectureComponent(name="LLM", purpose="Answer", technology="gpt-4o-mini"),
        ],
        data_flow="user -> retrieve -> generate -> respond",
        notable_tradeoffs=["Cost vs. latency"],
        data_model=[
            DataEntity(
                name="documents",
                primary_key="id",
                fields=["id:uuid", "content:text"],
                indexes=[],
                relationships=["documents 1->many chunks"],
            ),
            DataEntity(
                name="chunks",
                primary_key="id",
                fields=["id:uuid", "document_id:uuid", "embedding:vector"],
                indexes=["document_id"],
                relationships=[],
            ),
            DataEntity(
                name="users",
                primary_key="id",
                fields=["id:uuid", "email:text"],
                indexes=["email"],
                relationships=[],
            ),
        ],
        api_design=ApiDesign(
            style="REST",
            auth_strategy="Session/JWT",
            error_model="JSON {code,message}",
            rate_limiting="Per-user rate limit",
            endpoints=[
                ApiEndpoint(method="POST", path="/api/query", purpose="Ask question", auth="user"),
                ApiEndpoint(method="POST", path="/api/docs", purpose="Upload doc", auth="admin"),
                ApiEndpoint(method="GET", path="/api/docs", purpose="List docs", auth="user"),
            ],
        ),
        ui_ux_approach=UiUxApproach(
            key_screens=["Login", "Upload", "Ask", "Results"],
            component_tree_notes="App -> Layout -> (Upload, Ask, Results)",
            design_system_notes="Simple dashboard components.",
            mobile_strategy="Desktop-first",
        ),
        security_design=SecurityDesign(
            roles_and_permissions=["user", "admin"],
            pii_handling="Redact before embedding.",
            prompt_injection_controls=["Schema validation"],
            secrets_and_keys=["OpenAI key"],
            security_basics=["Rate limiting", "Input validation"],
        ),
        deployment_plan=DeploymentPlan(
            environments=["dev", "prod"],
            hosting="Vercel + Render",
            ci_cd="GitHub Actions",
            observability="Sentry",
            cost_notes=None,
        ),
        build_phases=[
            BuildPhase(phase="Phase 1", goal="Skeleton", deliverables=["Auth", "API"]),
            BuildPhase(phase="Phase 2", goal="MVP", deliverables=["RAG", "UI"]),
            BuildPhase(phase="Phase 3", goal="Polish", deliverables=["Eval", "Caching"]),
        ],
        risk_analysis=[
            RiskItem(risk="Hallucinations", impact="Trust", mitigation="Citations"),
            RiskItem(risk="Cost", impact="Budget", mitigation="Caching"),
            RiskItem(risk="PII", impact="Compliance", mitigation="Redaction"),
        ],
        mermaid_system_architecture="flowchart LR\nuser[User] --> web[Web]\nweb --> api[API]\napi --> db[(DB)]\napi --> llm[LLM]\n",
        mermaid_request_data_flow="flowchart LR\nuser[User] --> api[API]\napi --> retr[Retriever]\nretr --> db[(DB)]\napi --> llm[LLM]\nllm --> api\napi --> user\n",
        mermaid_erd="erDiagram\nDOCUMENTS ||--o{ CHUNKS : has\n",
        mermaid_deployment="flowchart LR\nweb[Web] --> api[API]\napi --> db[(DB)]\n",
        mermaid_ui_component_tree="flowchart TB\nApp --> Layout\nLayout --> Upload\nLayout --> Ask\nLayout --> Results\n",
    )


def _make_legacy_build_buy_train() -> BuildBuyTrain:
    return BuildBuyTrain(
        recommendation="buy",
        rationale="Existing tools cover this.",
        candidate_vendors=["Glean"],
        fine_tune_recommended=False,
    )


def _make_tools_open_source_phase() -> ToolsOpenSourcePhase:
    return ToolsOpenSourcePhase(
        search_context=GitHubSearchContext(
            query_used="rag AI wiki",
            repo_count_returned=1,
            total_count_estimate=42,
            search_note="OK",
        ),
        github_recommendations=[
            OpenSourceRepo(
                name="org/rag-starter",
                url="https://github.com/org/rag-starter",
                stars=1200,
                why_relevant="Matches internal search use case.",
                how_to_integrate="Fork and wire retriever to FastAPI.",
                license="MIT",
                license_risks="None",
                last_updated="2024-06-01",
            )
        ],
        managed_tools=[
            ManagedToolRecommendation(
                name="OpenAI",
                category="Inference",
                role_in_app="Embeddings + chat completions",
                rationale="Fast path for MVP.",
                product_url="https://platform.openai.com",
            )
        ],
        integration_summary="Use rag-starter layout with OpenAI APIs behind FastAPI.",
    )


def _make_infrastructure() -> Infrastructure:
    return Infrastructure(
        mvp=[
            InfraLayer(
                name="Client and edge",
                details="Next.js on Vercel with Clerk auth.",
                bullets=["Preview deploys per PR"],
            ),
            InfraLayer(
                name="API and jobs",
                details="FastAPI on Railway; background embedding worker same service.",
                bullets=["Single instance MVP"],
            ),
        ],
        production=[
            InfraLayer(
                name="Serving",
                details="Containerized API on Fargate behind ALB; autoscaling on CPU.",
                bullets=["Min 2 tasks"],
            ),
            InfraLayer(
                name="Data",
                details="RDS Postgres Multi-AZ; pgvector where search needs it.",
                bullets=["PgBouncer", "Nightly snapshots"],
            ),
        ],
        graduation_path=(
            "Keep Postgres schema; add PgBouncer; move API to Fargate; add SQS for long "
            "embedding jobs; front CloudFront."
        ),
        mermaid_mvp_stack="flowchart TB\nU[User] --> V[Vercel]\nV --> R[Railway API]\nR --> P[(Postgres)]\n",
        mermaid_production_stack="flowchart TB\nU[User] --> CF[CloudFront]\nCF --> ALB[ALB]\nALB --> F[Fargate]\nF --> RDS[(RDS)]\n",
        mermaid_mvp_to_production="flowchart LR\nM[MVP] -->|gradual| P[Production]\n",
        summary_bullets=["Vercel+Railway MVP", "Fargate+RDS prod", "OpenAI inference"],
    )


def _make_cost_model() -> CostModel:
    return CostModel(
        line_items=[
            CostLineItem(
                item="OpenAI API (chat completions)",
                tied_to="P2: application flow; P4: inference",
                cost_kind="variable_usage",
                monthly_min_usd=None,
                monthly_max_usd=None,
                notes="Dollar amounts for tokens are in the scenario table below.",
            ),
            CostLineItem(
                item="Postgres (managed)",
                tied_to="P4 MVP: primary database",
                cost_kind="fixed_recurring",
                monthly_min_usd=0.0,
                monthly_max_usd=25.0,
                notes="Typical small free tier; confirm with your provider.",
            ),
            CostLineItem(
                item="CI / source hosting",
                tied_to="P3: dev workflow",
                cost_kind="free",
                monthly_min_usd=0.0,
                monthly_max_usd=0.0,
                notes="Public repos and basic CI often $0; private scale may add cost.",
            ),
        ],
        stack_cost_summary="Usage-based LLM spend dominates; fixed infra is modest at pilot scale.",
        mvp_getting_started_note="Use free DB and app hosting tiers if possible; reserve budget for API usage per the pilot row.",
        scenarios=[
            CostScenario(
                label="Pilot",
                monthly_requests=30_000,
                avg_input_tokens=2000,
                avg_output_tokens=400,
                monthly_cost_usd=18.0,
            )
        ],
        primary_cost_driver="input tokens",
        optimization_opportunities=["Prompt caching"],
        self_host_breakeven_requests_per_month=None,
    )


def _make_security() -> SecurityPlan:
    return SecurityPlan(
        threats=["LLM01 prompt injection"],
        pii_handling="Strip emails before vector indexing.",
        prompt_injection_mitigations=["Delimiters", "Output schema validation"],
        rate_limiting="100 req/min/user",
        auth_strategy="Clerk",
        compliance_notes=[],
    )


def _make_observability() -> ObservabilityPlan:
    return ObservabilityPlan(
        metrics=["p95 latency", "cost per request"],
        tracing_tool="LangSmith",
        log_sink="CloudWatch",
        eval_strategy="Offline promptfoo + 5% online sample",
        alerting=["PagerDuty if schema_failure_rate > 5%"],
    )


def _make_scaling() -> ScalingPlan:
    return ScalingPlan(
        bottlenecks_at_10x=["OpenAI rate limit"],
        bottlenecks_at_100x=["Single Postgres write node"],
        caching_strategy="Redis prompt cache",
        failover_strategy="LiteLLM router to Anthropic",
        cost_at_scale_concerns=["Re-embedding"],
    )


def _make_red_team() -> RedTeamCritique:
    return RedTeamCritique(
        findings=[
            RedTeamFinding(
                severity="high",
                phase_id="phase_5",
                concern="Cost assumes constant 2k input tokens.",
                suggested_mitigation="Sample real prompts and recompute.",
            )
        ],
        overall_confidence="medium",
        summary="Plan is broadly sound but cost figures are optimistic.",
    )


def test_intake_is_complete_heuristic() -> None:
    short = IntakeAnswers(idea="A short idea.")
    assert not short.is_complete()
    long_idea = IntakeAnswers(
        idea="A much longer idea that crosses the 80-character threshold for being detailed enough."
    )
    assert long_idea.is_complete()
    with_answers = IntakeAnswers(idea="Short idea.", answers={"scale": "1k/day"})
    assert with_answers.is_complete()


def test_full_plan_serialises() -> None:
    plan = FullPlan(
        plan_id="plan_test123",
        idea="Build an internal AI search tool over our wiki.",
        created_at=datetime.now(UTC),
        pressure_test=_make_pressure_test(),
        problem_model_fit=_make_problem_model_fit(),
        architecture=_make_architecture(),
        build_buy_train=_make_tools_open_source_phase(),
        infrastructure=_make_infrastructure(),
        cost_model=_make_cost_model(),
        security=_make_security(),
        observability=_make_observability(),
        scaling=_make_scaling(),
        red_team=_make_red_team(),
        executive_summary="Buy Glean for now.",
        next_steps=["Sign up for Glean trial"],
        total_cost_usd=0.42,
    )

    dumped = plan.model_dump(mode="json")
    assert dumped["plan_id"] == "plan_test123"
    assert dumped["architecture"]["pattern"] == "rag"
    assert len(dumped["red_team"]["findings"]) == 1

    round_trip = FullPlan.model_validate(dumped)
    assert round_trip.plan_id == plan.plan_id
    assert round_trip.cost_model.scenarios[0].monthly_cost_usd == 18.0


def test_full_plan_migrates_legacy_cost_model_without_line_items() -> None:
    plan = FullPlan.model_validate(
        {
            "plan_id": "legacy_cost",
            "cost_model": {
                "scenarios": [
                    {
                        "label": "Pilot",
                        "monthly_requests": 1_000,
                        "avg_input_tokens": 100,
                        "avg_output_tokens": 50,
                        "monthly_cost_usd": 9.99,
                    }
                ],
                "primary_cost_driver": "api usage",
                "optimization_opportunities": ["caching"],
            },
        }
    )
    assert plan.cost_model is not None
    assert len(plan.cost_model.line_items) >= 1
    assert plan.cost_model.stack_cost_summary
    assert plan.cost_model.mvp_getting_started_note
    assert plan.cost_model.scenarios[0].monthly_cost_usd == 9.99


def test_phase_schemas_have_json_schema() -> None:
    """Every phase schema must produce a json_schema OpenAI can consume."""
    for cls in (
        PressureTestResult,
        ProblemModelFit,
        Architecture,
        ToolsOpenSourcePhase,
        Infrastructure,
        CostModel,
        SecurityPlan,
        ObservabilityPlan,
        ScalingPlan,
    ):
        schema = cls.model_json_schema()
        assert "properties" in schema
        assert schema["type"] == "object"


def test_full_plan_loads_legacy_build_buy_train_json() -> None:
    legacy = _make_legacy_build_buy_train().model_dump(mode="json")
    plan = FullPlan.model_validate(
        {
            "plan_id": "legacy_p3",
            "idea": "Test",
            "build_buy_train": legacy,
        }
    )
    assert isinstance(plan.build_buy_train, BuildBuyTrain)
    assert plan.build_buy_train.recommendation == "buy"


def test_normalize_legacy_flat_infrastructure() -> None:
    raw = {
        "hosting": "Vercel + Render",
        "inference_provider": "OpenAI",
        "secrets_manager": "Doppler",
        "rationale": "Simple MVP stack.",
    }
    inf = Infrastructure.model_validate(normalize_infrastructure_payload(raw))
    assert len(inf.mvp) >= 1
    assert len(inf.production) >= 1
    assert inf.graduation_path
