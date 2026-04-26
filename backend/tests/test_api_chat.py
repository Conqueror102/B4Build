"""Happy-path test for /api/chat with the LLM client mocked.

Strategy: monkey-patch ``LLMClient.complete_structured`` to return a valid
Pydantic instance whose type matches the requested ``schema`` argument. That
lets us exercise the entire LangGraph state machine + the SSE streaming
layer without touching OpenAI.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from src import store
from src.llm import client as llm_client_module
from src.main import create_app
from src.prompts.coordinator import ClarifyingQuestion, ClarifyingQuestions
from src.prompts.synthesizer import SynthesizerOutput
from tests.test_schemas import _make_infrastructure, _make_tools_open_source_phase

from src.schemas.phases import (
    Architecture,
    ArchitectureComponent,
    ApiDesign,
    ApiEndpoint,
    CostLineItem,
    CostModel,
    CostScenario,
    BuildPhase,
    DataEntity,
    Infrastructure,
    ObservabilityPlan,
    PressureTestResult,
    ProblemModelFit,
    RiskItem,
    ScopeDefinition,
    FeatureModule,
    ServiceComponent,
    UiUxApproach,
    SecurityDesign,
    DeploymentPlan,
    UserStory,
    ScalingPlan,
    SecurityPlan,
    ToolsOpenSourcePhase,
)
from src.schemas.plan import RedTeamCritique, RedTeamFinding


def _fixture_for(schema: type[BaseModel]) -> BaseModel:
    """Return a valid instance of the requested schema for use in tests."""
    if schema is PressureTestResult:
        return PressureTestResult(
            is_viable=True,
            summary="Worth building.",
            similar_existing_solutions=["Glean"],
            differentiators=["Self-host"],
            risks=["Regulatory drift"],
        )
    if schema is ProblemModelFit:
        return ProblemModelFit(
            problem_type="search",
            why_llm="LLM-augmented retrieval beats keyword for natural queries.",
            success_criteria=["P@5 > 0.8"],
            failure_modes=["Hallucinated citations"],
        )
    if schema is Architecture:
        return Architecture(
            pattern="rag",
            scope_definition=ScopeDefinition(
                problem_why="Help employees find answers in internal docs.",
                personas_and_roles=["Engineer", "Sales", "Admin"],
                mvp_definition=["Search across docs", "Citations", "Admin ingestion"],
                success_in_3_months=["P@5 > 0.8", "p95 < 2.5s", "Adoption in 3 teams"],
            ),
            feature_modules=[
                FeatureModule(
                    name="Search",
                    description="Ask natural language questions over company docs.",
                    user_stories=[
                        UserStory(as_a="Employee", i_want="to ask questions", so_that="I find answers fast")
                    ],
                ),
                FeatureModule(
                    name="Ingestion",
                    description="Connect and sync data sources.",
                    user_stories=[
                        UserStory(as_a="Admin", i_want="to connect Google Drive", so_that="docs are searchable")
                    ],
                ),
                FeatureModule(
                    name="Admin",
                    description="Manage access and data sources.",
                    user_stories=[
                        UserStory(as_a="Admin", i_want="to control permissions", so_that="PII stays protected")
                    ],
                ),
            ],
            system_architecture=[
                ServiceComponent(name="WebApp", responsibility="UI", technology="Next.js"),
                ServiceComponent(name="Api", responsibility="Auth + query orchestration", technology="FastAPI"),
                ServiceComponent(name="Retriever", responsibility="Vector search", technology="pgvector"),
                ServiceComponent(name="LLM", responsibility="Answer generation", technology="gpt-4o-mini"),
            ],
            components=[
                ArchitectureComponent(
                    name="Embedder", purpose="encode", technology="text-embedding-3-small"
                ),
                ArchitectureComponent(name="LLM", purpose="answer", technology="gpt-4o-mini"),
            ],
            data_flow="user -> retriever -> generator -> response",
            notable_tradeoffs=["latency vs cost"],
            data_model=[
                DataEntity(
                    name="documents",
                    primary_key="id",
                    fields=["id:uuid", "source:str", "uri:str", "content:text"],
                    indexes=["source", "uri"],
                    relationships=[],
                ),
                DataEntity(
                    name="chunks",
                    primary_key="id",
                    fields=["id:uuid", "document_id:uuid", "content:text", "embedding:vector"],
                    indexes=["document_id", "ivfflat(embedding)"],
                    relationships=["documents 1->many chunks"],
                ),
                DataEntity(
                    name="queries",
                    primary_key="id",
                    fields=["id:uuid", "user_id:uuid", "q:text", "created_at:timestamp"],
                    indexes=["user_id", "created_at"],
                    relationships=[],
                ),
            ],
            api_design=ApiDesign(
                style="REST (simpler for a small team)",
                auth_strategy="Session/JWT via Clerk",
                error_model="JSON {code,message,details?} + 4xx/5xx",
                rate_limiting="Per-user 60 rpm at gateway",
                endpoints=[
                    ApiEndpoint(method="POST", path="/api/query", purpose="Ask a question", auth="user"),
                    ApiEndpoint(method="POST", path="/api/sources", purpose="Connect a source", auth="admin"),
                    ApiEndpoint(method="GET", path="/api/plan/{id}", purpose="Fetch plan", auth="user"),
                ],
            ),
            ui_ux_approach=UiUxApproach(
                key_screens=["Login", "Search", "Results with citations", "Admin sources"],
                component_tree_notes="Layout -> Sidebar -> SearchBox, ResultsList, CitationDrawer",
                design_system_notes="Compact dashboard, strong hierarchy, mono for ids/logs",
                mobile_strategy="Desktop-first; responsive for reading results",
            ),
            security_design=SecurityDesign(
                roles_and_permissions=["user: query", "admin: manage sources"],
                pii_handling="Do not index raw PII; redact before embedding.",
                prompt_injection_controls=["Cite-only answers", "Tool schema validation"],
                secrets_and_keys=["OpenAI key in secrets manager", "OAuth tokens encrypted"],
                security_basics=["Rate limiting", "Input validation", "Audit logging"],
            ),
            deployment_plan=DeploymentPlan(
                environments=["dev", "staging", "prod"],
                hosting="Render/Fly for API + Vercel for web",
                ci_cd="GitHub Actions → deploy on main",
                observability="Sentry + logs + basic metrics",
                cost_notes="Start with hosted LLM; monitor token burn",
            ),
            build_phases=[
                BuildPhase(phase="Phase 1", goal="Skeleton", deliverables=["Auth", "Query API", "UI shell"]),
                BuildPhase(phase="Phase 2", goal="MVP", deliverables=["Ingestion", "Vector search", "Citations"]),
                BuildPhase(phase="Phase 3", goal="Polish", deliverables=["Eval harness", "Admin UX", "Caching"]),
            ],
            risk_analysis=[
                RiskItem(risk="Hallucinations", impact="Trust loss", mitigation="Citations + refusal policy"),
                RiskItem(risk="PII leakage", impact="Compliance", mitigation="Redaction + access controls"),
                RiskItem(risk="Cost spikes", impact="Budget", mitigation="Caching + limits + smaller model"),
            ],
            mermaid_system_architecture="flowchart LR\nuser[User] --> web[WebApp]\nweb --> api[Api]\napi --> retr[Retriever]\napi --> llm[LLM]\nretr --> db[(Postgres)]\n",
            mermaid_request_data_flow="sequenceDiagram\nparticipant U as User\nparticipant W as Web\nparticipant A as API\nparticipant R as Retriever\nparticipant L as LLM\nU->>W: Ask\nW->>A: POST /api/query\nA->>R: search\nR-->>A: topK\nA->>L: generate\nL-->>A: answer+cites\nA-->>W: response\n",
            mermaid_erd="erDiagram\nDOCUMENTS ||--o{ CHUNKS : has\nDOCUMENTS {\n  uuid id\n  string source\n}\nCHUNKS {\n  uuid id\n  uuid document_id\n}\n",
            mermaid_deployment="flowchart LR\nsubgraph edge[Edge]\ncdn[CDN]\nend\nsubgraph app[App]\nweb[NextJS]\napi[FastAPI]\nend\nsubgraph data[Data]\npg[(Postgres)]\nend\ncdn --> web\nweb --> api\napi --> pg\n",
            mermaid_ui_component_tree="flowchart TB\nApp --> Layout\nLayout --> Sidebar\nLayout --> Main\nMain --> SearchBox\nMain --> ResultsList\nResultsList --> ResultItem\nResultItem --> CitationDrawer\n",
        )
    if schema is ToolsOpenSourcePhase:
        return _make_tools_open_source_phase()
    if schema is Infrastructure:
        return _make_infrastructure()
    if schema is CostModel:
        return CostModel(
            line_items=[
                CostLineItem(
                    item="LLM API",
                    tied_to="P2 + P4",
                    cost_kind="variable_usage",
                    monthly_min_usd=None,
                    monthly_max_usd=None,
                    notes="See table.",
                )
            ],
            stack_cost_summary="Test stack summary.",
            mvp_getting_started_note="Test MVP note.",
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
    if schema is SecurityPlan:
        return SecurityPlan(
            threats=["LLM01 prompt injection"],
            pii_handling="Strip PII before vector store.",
            prompt_injection_mitigations=["Delimiters", "Schema validation"],
            rate_limiting="100 rpm/user",
            auth_strategy="Clerk",
            compliance_notes=[],
        )
    if schema is ObservabilityPlan:
        return ObservabilityPlan(
            metrics=["p95 latency", "cost per request"],
            tracing_tool="LangSmith",
            log_sink="CloudWatch",
            eval_strategy="Offline promptfoo + 5% online sample",
            alerting=["PagerDuty if schema_failure_rate > 5%"],
        )
    if schema is ScalingPlan:
        return ScalingPlan(
            bottlenecks_at_10x=["OpenAI rate limit"],
            bottlenecks_at_100x=["Single Postgres write node"],
            caching_strategy="Redis prompt cache",
            failover_strategy="LiteLLM router to Anthropic",
            cost_at_scale_concerns=["Re-embedding"],
        )
    if schema is RedTeamCritique:
        return RedTeamCritique(
            findings=[
                RedTeamFinding(
                    severity="medium",
                    phase_id="phase_5",
                    concern="Token assumptions optimistic.",
                    suggested_mitigation="Sample real prompts.",
                )
            ],
            overall_confidence="medium",
            summary="Solid plan with one cost caveat.",
        )
    if schema is SynthesizerOutput:
        return SynthesizerOutput(
            executive_summary="Buy Glean; it covers 80% of this need today.",
            next_steps=["Sign up for Glean trial", "Run a 50-doc spike"],
        )
    if schema is ClarifyingQuestions:
        return ClarifyingQuestions(
            questions=[
                ClarifyingQuestion(
                    key="scale",
                    question="What's your expected daily request volume?",
                    why_we_ask="Drives Phase 5 cost model.",
                )
            ]
        )
    raise AssertionError(f"no fixture for schema {schema.__name__}")


@pytest.fixture
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace LLMClient.complete_structured with a deterministic stub."""

    async def fake_complete_structured(
        self: Any,
        messages: list[dict[str, Any]],
        *,
        schema: type[BaseModel],
        request_id: str,
        phase: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> BaseModel:
        return _fixture_for(schema)

    monkeypatch.setattr(
        llm_client_module.LLMClient,
        "complete_structured",
        fake_complete_structured,
    )
    store.clear()
    yield
    store.clear()


def _parse_sse(text: str) -> list[dict[str, Any]]:
    """Parse a TestClient SSE response body into event dicts."""
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


def test_chat_runs_full_graph_and_emits_done(mock_llm: None) -> None:
    body = {
        "idea": (
            "Internal AI search over our company wiki and Google Docs. "
            "We have ~200 employees and want this for engineering and sales teams."
        ),
        "clarifying_answers": {"scale": "1k req/day", "stack": "Postgres on AWS"},
    }
    with TestClient(create_app()) as client:
        with client.stream("POST", "/api/chat", json=body) as response:
            assert response.status_code == 200
            text = response.read().decode("utf-8")

        events = _parse_sse(text)
        event_types = [e["event"] for e in events]

        assert "phase_start" in event_types
        assert "phase_complete" in event_types
        assert "red_team" in event_types
        assert "synthesizer" in event_types
        assert "done" in event_types

        phase_complete_events = [e for e in events if e["event"] == "phase_complete"]
        assert len(phase_complete_events) == 9
        expected_phases = {
            "phase_0",
            "phase_1",
            "phase_2",
            "phase_3",
            "phase_4",
            "phase_5",
            "phase_6_25",
            "phase_6_5",
            "phase_7",
        }
        assert {e["phase_id"] for e in phase_complete_events} == expected_phases

        done = next(e for e in events if e["event"] == "done")
        plan_id = done["data"]["plan_id"]
        uuid.UUID(plan_id)

        plan_resp = client.get(f"/api/plan/{plan_id}")
        assert plan_resp.status_code == 200
        plan_body = plan_resp.json()
        assert plan_body["plan"]["plan_id"] == plan_id
        assert plan_body["plan"]["architecture"]["pattern"] == "rag"


def test_get_plan_404_for_unknown_id() -> None:
    store.clear()
    missing = "00000000-0000-4000-8000-00000000dead"
    with TestClient(create_app()) as client:
        response = client.get(f"/api/plan/{missing}")
        assert response.status_code == 404


def test_chat_clarify_branch_when_idea_short_and_no_answers(mock_llm: None) -> None:
    body = {"idea": "Build a chatbot."}
    with TestClient(create_app()) as client:
        with client.stream("POST", "/api/chat", json=body) as response:
            assert response.status_code == 200
            text = response.read().decode("utf-8")

    events = _parse_sse(text)
    event_types = [e["event"] for e in events]
    assert "clarify" in event_types
    assert "done" not in event_types
