"use client";

import Link from "next/link";
import { ReportPanel } from "@/components/plan/report-panel";
import type { FullPlan } from "@/lib/types";
import type { PhaseState } from "@/hooks/use-plan-stream";

// MOCK DATA for the Sample Page (shape is illustrative; cast for strict FullPlan typing)
const mockPlan = {
  plan_id: "sample-plan-123",
  idea: "A B2B SaaS that allows law firms to upload PDF contracts. The system uses an LLM to find risky clauses, missing standard terms, and provides a redlined summary. Targeting 500 law firms.",
  created_at: "2024-01-15T10:00:00Z",
  total_cost_usd: 125.5,
  pressure_test: {
    is_viable: true,
    refusal_reason: null,
    summary: "Clear B2B use case with defined audience. The problem is well-suited for LLMs, specifically using RAG over the contract text.",
    similar_existing_solutions: ["LawGeex", "Kira Systems"],
    differentiators: ["Focus on SMB law firms", "Simpler UX"],
    risks: ["Accuracy requirements", "Data privacy"],
  },
  problem_model_fit: {
    problem_type: "extraction" as const,
    why_llm: "Claude 3 Opus excels at long-context document analysis and precise extraction over complex legal language.",
    deterministic_alternative: "Rule-based NER systems",
    success_criteria: ["90% accuracy on test contracts", "Under 30s processing time"],
    failure_modes: ["Hallucinated clauses", "Missed edge cases"],
  },
  architecture: {
    pattern: "rag" as const,
    scope_definition: {
      problem_why: "Law firms need to review contracts faster",
      personas_and_roles: ["Legal associate", "Partner"],
      mvp_definition: ["Upload PDF", "Get risk analysis", "Export redline"],
      success_in_3_months: ["5 firms using it", "80% accuracy on test set"],
    },
    feature_modules: [],
    system_architecture: [],
    components: [
      { name: "Frontend", technology: "Next.js + Tailwind", purpose: "Upload interface and redline viewer" },
      { name: "API Gateway", technology: "FastAPI", purpose: "Handle async PDF processing jobs" },
      { name: "Document Store", technology: "AWS S3", purpose: "Secure encrypted storage of raw PDFs" },
      { name: "Vector Database", technology: "Pinecone", purpose: "Store chunked contract sections for semantic search" },
      { name: "LLM Orchestration", technology: "LangChain", purpose: "Manage prompts and RAG pipeline" },
    ],
    data_flow: "User -> Frontend -> FastAPI -> S3 -> LangChain -> Pinecone -> Claude 3 Opus -> FastAPI -> User",
    notable_tradeoffs: [],
    data_model: [],
    api_design: {
      style: "REST",
      auth_strategy: "JWT",
      error_model: "RFC 7807",
      rate_limiting: "Per-tenant",
      endpoints: [],
    },
    ui_ux_approach: {
      key_screens: ["Upload", "Review", "Export"],
      component_tree_notes: "Standard SaaS layout",
      design_system_notes: "Tailwind + shadcn/ui",
      mobile_strategy: "Responsive web",
    },
    security_design: {
      roles_and_permissions: ["Admin", "User"],
      pii_handling: "Encrypted at rest",
      prompt_injection_controls: ["Input validation"],
      secrets_and_keys: ["AWS Secrets Manager"],
      security_basics: ["HTTPS", "CORS"],
    },
    deployment_plan: {
      environments: ["dev", "prod"],
      hosting: "AWS",
      ci_cd: "GitHub Actions",
      observability: "Datadog",
      cost_notes: "Pay as you go",
    },
    build_phases: [],
    risk_analysis: [],
    mermaid_system_architecture: "flowchart TB\nU[User] --> F[Frontend]\nF --> API[FastAPI]\nAPI --> S3[S3]\nAPI --> P[Pinecone]\nAPI --> C[Claude]",
    mermaid_request_data_flow: "sequenceDiagram\nUser->>Frontend: Upload PDF\nFrontend->>API: POST /analyze\nAPI->>S3: Store PDF\nAPI->>Claude: Analyze\nClaude->>API: Results\nAPI->>Frontend: Redline",
    mermaid_erd: "",
    mermaid_deployment: "",
    mermaid_ui_component_tree: "",
  },
  build_buy_train: {
    search_context: {
      query_used: "legal contract rag",
      repo_count_returned: 0,
      total_count_estimate: null,
      search_note: "Sample page — no live GitHub search",
    },
    github_recommendations: [],
    managed_tools: [
      {
        name: "Anthropic API",
        category: "Inference",
        role_in_app: "Long-context contract analysis",
        rationale: "Strong for legal prose and citations in this demo.",
        product_url: "https://www.anthropic.com",
      },
    ],
    integration_summary:
      "Sample: custom FastAPI RAG service calling Anthropic; PDF parsing via a commercial parser SDK.",
  },
  infrastructure: {
    mvp: [
      { name: "Edge", details: "Next.js on Vercel for uploads and review UI.", bullets: ["TLS by default"] },
      { name: "API", details: "FastAPI on a small PaaS instance for orchestration.", bullets: [] },
    ],
    production: [
      { name: "Serving", details: "Autoscaling containers behind a load balancer.", bullets: ["Health checks"] },
      { name: "Data", details: "Managed object storage + Postgres for metadata and audit.", bullets: ["Encryption at rest"] },
    ],
    graduation_path: "Harden auth, split workers, add WAF and regional DR as usage grows.",
    mermaid_mvp_stack: "flowchart TB\nU[User] --> W[Web]\nW --> A[API]\n",
    mermaid_production_stack: "flowchart TB\nU[User] --> LB[LB]\nLB --> S[Services]\n",
    mermaid_mvp_to_production: "flowchart LR\nM[MVP] --> P[Production]\n",
    summary_bullets: ["Vercel + PaaS API", "Managed storage", "Anthropic inference"],
  },
  cost_model: {
    line_items: [
      {
        item: "Anthropic API (Claude)",
        tied_to: "P2: LLM path; P4: hosted inference",
        cost_kind: "variable_usage" as const,
        monthly_min_usd: null,
        monthly_max_usd: null,
        notes: "Largest line at scale due to long PDF context and Opus pricing.",
      },
      {
        item: "Pinecone (vector index)",
        tied_to: "P4 MVP: semantic retrieval for clauses",
        cost_kind: "fixed_recurring" as const,
        monthly_min_usd: 0,
        monthly_max_usd: 200,
        notes: "Starter then usage-based; depends on index size and QPS.",
      },
      {
        item: "AWS ECS / compute for workers",
        tied_to: "P4: API and async PDF jobs",
        cost_kind: "mixed" as const,
        monthly_min_usd: 50,
        monthly_max_usd: 800,
        notes: "Grows with concurrent OCR and chunking load.",
      },
    ],
    stack_cost_summary:
      "In this design, model usage on large PDFs and vector storage dominate; fixed PaaS is smaller until traffic grows.",
    mvp_getting_started_note:
      "Budget for API keys and a minimal managed cluster first; add observability and higher Pinecone tier after validation.",
    scenarios: [
      {
        label: "Pilot (illustrative)",
        monthly_requests: 15_000,
        avg_input_tokens: 8_000,
        avg_output_tokens: 2_000,
        monthly_cost_usd: 420.0,
        notes: "Sample page — numbers are not from the live calculator.",
      },
    ],
    primary_cost_driver: "input + output tokens on long contract PDFs",
    optimization_opportunities: [
      "Route triage to a smaller model before Opus for final review",
      "Cache repeated boilerplate clause analysis",
    ],
    self_host_breakeven_requests_per_month: null,
  },
  security: {
    threats: ["Data leakage of sensitive contracts", "Prompt injection to manipulate output", "Tenant data mixing"],
    pii_handling: "S3 SSE-KMS encryption per tenant",
    prompt_injection_mitigations: ["Strict LLM output parsing", "Input validation"],
    rate_limiting: "Per-tenant quotas",
    auth_strategy: "JWT with Clerk",
    compliance_notes: ["SOC2 Type II", "GDPR compliant"],
  },
  observability: {
    metrics: ["PDF processing latency", "LLM token usage per tenant", "Extraction accuracy (thumbs up/down)"],
    tracing_tool: "LangSmith",
    log_sink: "Datadog",
    eval_strategy: "Human review + automated tests",
    alerting: ["Error rate > 5%", "Latency > 60s"],
  },
  scaling: {
    bottlenecks_at_10x: ["LLM API rate limits", "Concurrent PDF OCR processing"],
    bottlenecks_at_100x: ["Database connections", "S3 request limits"],
    caching_strategy: "Redis for repeated clause analysis",
    failover_strategy: "Multi-region deployment",
    cost_at_scale_concerns: ["Token costs grow linearly", "Storage costs for PDFs"],
  },
  red_team: {
    overall_confidence: "medium",
    summary:
      "The architecture relies too heavily on Claude 3 Opus for all tasks. Opus is slow and expensive. Prefer a cheaper model for triage and reserve Opus for complex reasoning. Law firms need SOC2/GDPR alignment and clear data residency with Anthropic.",
    findings: [
      {
        severity: "high",
        phase_id: "P2",
        concern:
          "Using Opus for every contract pass will blow cost and latency at scale.",
        suggested_mitigation:
          "Multi-model routing: Haiku/BM25 triage → Opus only when complex reasoning is required.",
      },
      {
        severity: "medium",
        phase_id: "P4",
        concern: "Sensitive PDFs must meet residency and retention policies per tenant.",
        suggested_mitigation:
          "Zero-retention APIs where possible, tenant-isolated buckets, documented DPA.",
      },
    ],
  },
  executive_summary: "The AI Legal Contract Reviewer is a viable B2B SaaS. The architecture leverages managed services to reduce operational overhead, but the primary risk is the unit economics of using frontier models on large documents. Implementing a multi-model strategy and async processing queues will be critical for scaling.",
  next_steps: [
    "Pilot with one firm and measure cost per reviewed page",
    "Add async PDF pipeline and queue depth metrics before scaling seats",
    "Formalize security review with counsel for retention and residency",
  ],
} as unknown as FullPlan;

const mockPhases: Record<string, PhaseState> = {
  "P0": { title: "Pressure Test", status: "complete", output: mockPlan.pressure_test },
  "P1": { title: "Problem/Model Fit", status: "complete", output: mockPlan.problem_model_fit },
  "P2": { title: "Architecture", status: "complete", output: mockPlan.architecture },
  "P3": { title: "Tools & open source", status: "complete", output: mockPlan.build_buy_train },
  "P4": { title: "Infrastructure", status: "complete", output: mockPlan.infrastructure },
  "P5": { title: "Cost Model", status: "complete", output: mockPlan.cost_model },
  "P6.25": { title: "Security", status: "complete", output: mockPlan.security },
  "P6.5": { title: "Observability", status: "complete", output: mockPlan.observability },
  "P7": { title: "Scaling", status: "complete", output: mockPlan.scaling },
};

export default function SamplePlanPage() {
  return (
    <div className="flex h-[calc(100vh-var(--header-h,64px)-var(--footer-h,48px))] flex-col">
      <header className="flex items-center border-b border-border px-4 py-3 sm:px-6">
        <h1 className="text-sm font-semibold">Sample Plan: AI Legal Contract Reviewer</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left side: Report Panel */}
        <div className="flex-1 overflow-y-auto border-r border-border">
          <ReportPanel
            phases={mockPhases}
            redTeam={mockPlan.red_team!}
            plan={mockPlan}
            activePhaseId={null}
          />
        </div>

        {/* Right side: Mock Chat Panel */}
        <div className="w-full max-w-md shrink-0 bg-background flex flex-col p-6 items-center justify-center text-center">
          <h2 className="text-xl font-bold mb-4">Interactive Chat Disabled</h2>
          <p className="text-muted-foreground mb-8">
            This is a read-only sample. Sign up to generate your own architecture plans, challenge the AI, and iterate on constraints.
          </p>
          <Link
            href="/plan/new"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
          >
            Start Building
          </Link>
        </div>
      </div>
    </div>
  );
}
