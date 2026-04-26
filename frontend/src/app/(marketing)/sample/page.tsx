"use client";

import { ReportPanel } from "@/components/plan/report-panel";
import type { FullPlan, RedTeamCritique } from "@/lib/types";
import type { PhaseState } from "@/hooks/use-plan-stream";

// MOCK DATA for the Sample Page (shape is illustrative; cast for strict FullPlan typing)
const mockPlan = {
  id: "sample-plan-123",
  title: "AI Legal Contract Reviewer",
  idea_summary: "A B2B SaaS that allows law firms to upload PDF contracts. The system uses an LLM to find risky clauses, missing standard terms, and provides a redlined summary. Targeting 500 law firms.",
  total_cost_usd: 125.5,
  pressure_test: {
    status: "pass",
    feedback: "Clear B2B use case with defined audience. The problem is well-suited for LLMs, specifically using RAG over the contract text.",
    adjusted_constraints: ["Must handle large PDFs securely", "Requires high-accuracy extraction", "Must retain formatting"],
  },
  problem_model_fit: {
    recommended_model: "claude-3-opus",
    reasoning: "Claude 3 Opus excels at long-context document analysis and precise extraction over complex legal language.",
    alternatives_considered: ["gpt-4-turbo"],
  },
  architecture: {
    components: [
      { name: "Frontend", technology: "Next.js + Tailwind", purpose: "Upload interface and redline viewer" },
      { name: "API Gateway", technology: "FastAPI", purpose: "Handle async PDF processing jobs" },
      { name: "Document Store", technology: "AWS S3", purpose: "Secure encrypted storage of raw PDFs" },
      { name: "Vector Database", technology: "Pinecone", purpose: "Store chunked contract sections for semantic search" },
      { name: "LLM Orchestration", technology: "LangChain", purpose: "Manage prompts and RAG pipeline" },
    ],
    data_flow: "User -> Frontend -> FastAPI -> S3 -> LangChain -> Pinecone -> Claude 3 Opus -> FastAPI -> User",
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
    mitigations: ["S3 SSE-KMS encryption per tenant", "Strict LLM output parsing", "Row-level security in Postgres"],
  },
  observability: {
    metrics: ["PDF processing latency", "LLM token usage per tenant", "Extraction accuracy (thumbs up/down)"],
    tools: ["Datadog", "LangSmith", "Sentry"],
  },
  scaling: {
    bottlenecks: ["LLM API rate limits", "Concurrent PDF OCR processing"],
    solutions: ["Implement async queueing (Celery/Redis)", "Request quota increases from Anthropic"],
  },
  red_team: {
    severity: "medium",
    critique: "The architecture relies too heavily on Claude 3 Opus for all tasks. Opus is slow and expensive. You should use a cheaper model (like Haiku) for initial triaging and chunking, and only use Opus for the final complex reasoning. Additionally, law firms have strict data residency requirements (e.g., SOC2, GDPR). Ensure Anthropic has a zero-retention agreement.",
    unhandled_risks: ["Data residency compliance", "High latency for 100+ page contracts"],
    recommendations: ["Implement a multi-model router (Haiku for simple extraction, Opus for complex)", "Add a 'processing' state in the UI via WebSockets"],
  },
  executive_summary: "The AI Legal Contract Reviewer is a viable B2B SaaS. The architecture leverages managed services to reduce operational overhead, but the primary risk is the unit economics of using frontier models on large documents. Implementing a multi-model strategy and async processing queues will be critical for scaling.",
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
          <a
            href="/plan/new"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
          >
            Start Building
          </a>
        </div>
      </div>
    </div>
  );
}
