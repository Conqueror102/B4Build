/**
 * TypeScript mirror of the backend Pydantic schemas in
 * `backend/src/schemas/*.py`. Keep field names in sync.
 */

export type ProblemType =
  | "classification"
  | "extraction"
  | "generation"
  | "summarization"
  | "search"
  | "agent"
  | "translation"
  | "other";

export type ArchitecturePattern =
  | "rag"
  | "agent"
  | "fine_tuned"
  | "tool_use"
  | "router"
  | "pipeline"
  | "hybrid";

export type BuildBuyTrainRecommendation = "build" | "buy" | "fine_tune" | "hybrid" | "compose_oss";

export interface OpenSourceRepo {
  name: string;
  url: string;
  stars: number;
  why_relevant: string;
  how_to_integrate: string;
  license: string | null;
  license_risks: string;
  last_updated: string;
}

export interface PressureTestResult {
  is_viable: boolean;
  refusal_reason: string | null;
  summary: string;
  similar_existing_solutions: string[];
  differentiators: string[];
  risks: string[];
}

export interface ProblemModelFit {
  problem_type: ProblemType;
  why_llm: string;
  deterministic_alternative: string | null;
  success_criteria: string[];
  failure_modes: string[];
}

export interface ArchitectureComponent {
  name: string;
  purpose: string;
  technology: string;
}

export interface ScopeDefinition {
  problem_why: string;
  personas_and_roles: string[];
  mvp_definition: string[];
  success_in_3_months: string[];
}

export interface UserStory {
  as_a: string;
  i_want: string;
  so_that: string;
}

export interface FeatureModule {
  name: string;
  description: string;
  user_stories: UserStory[];
}

export interface ServiceComponent {
  name: string;
  responsibility: string;
  technology: string;
  scaling_notes?: string | null;
}

export interface DataEntity {
  name: string;
  primary_key: string;
  fields: string[];
  indexes: string[];
  relationships: string[];
}

export interface ApiEndpoint {
  method: string;
  path: string;
  purpose: string;
  auth?: string | null;
}

export interface ApiDesign {
  style: string;
  auth_strategy: string;
  error_model: string;
  rate_limiting: string;
  endpoints: ApiEndpoint[];
}

export interface UiUxApproach {
  key_screens: string[];
  component_tree_notes: string;
  design_system_notes: string;
  mobile_strategy: string;
}

export interface SecurityDesign {
  roles_and_permissions: string[];
  pii_handling: string;
  prompt_injection_controls: string[];
  secrets_and_keys: string[];
  security_basics: string[];
}

export interface DeploymentPlan {
  environments: string[];
  hosting: string;
  ci_cd: string;
  observability: string;
  cost_notes?: string | null;
}

export interface BuildPhase {
  phase: string;
  goal: string;
  deliverables: string[];
}

export interface RiskItem {
  risk: string;
  impact: string;
  mitigation: string;
}

export interface Architecture {
  pattern: ArchitecturePattern;
  scope_definition: ScopeDefinition;
  feature_modules: FeatureModule[];
  system_architecture: ServiceComponent[];
  components: ArchitectureComponent[];
  data_flow: string;
  notable_tradeoffs: string[];
  data_model: DataEntity[];
  api_design: ApiDesign;
  ui_ux_approach: UiUxApproach;
  security_design: SecurityDesign;
  deployment_plan: DeploymentPlan;
  build_phases: BuildPhase[];
  risk_analysis: RiskItem[];
  mermaid_system_architecture: string;
  mermaid_request_data_flow: string;
  mermaid_erd: string;
  mermaid_deployment: string;
  mermaid_ui_component_tree: string;
}

export interface BuildBuyTrain {
  recommendation: BuildBuyTrainRecommendation;
  rationale: string;
  open_source_candidates?: OpenSourceRepo[];
  recommended_stack_from_oss?: string | null;
  integration_plan?: string[];
  candidate_vendors: string[];
  fine_tune_recommended: boolean;
  fine_tune_dataset_size_estimate: number | null;
}

export interface GitHubSearchContext {
  query_used: string | null;
  repo_count_returned: number;
  total_count_estimate: number | null;
  search_note: string | null;
}

export interface ManagedToolRecommendation {
  name: string;
  category: string;
  role_in_app: string;
  rationale: string;
  product_url?: string | null;
}

/** Current Phase 3 output (tools + GitHub-backed OSS). */
export interface ToolsOpenSourcePhase {
  search_context: GitHubSearchContext;
  github_recommendations: OpenSourceRepo[];
  managed_tools: ManagedToolRecommendation[];
  integration_summary: string;
}

export interface InfraLayer {
  name: string;
  details: string;
  bullets?: string[];
}

export interface MvpInfrastructure {
  philosophy: string;
  inference_and_models: string;
  frontend_hosting: string;
  backend_api: string;
  database: string;
  file_object_storage: string;
  auth_identity: string;
  vector_search: string | null;
  async_and_queue: string | null;
  secrets_and_config: string;
  domain_and_tls: string;
  monitoring_errors: string;
  ci_cd: string;
  explicitly_deferred_to_production: string[];
  mvp_risks: string[];
}

export interface ProductionInfrastructure {
  philosophy: string;
  primary_cloud: string;
  compute_and_serving: string;
  database_and_persistence: string;
  caching: string;
  cdn_waf_and_edge: string;
  file_object_storage: string;
  auth_identity: string;
  vector_and_search: string | null;
  messaging_and_queue: string | null;
  load_balancing: string;
  autoscaling: string;
  network_and_security: string;
  ci_cd: string;
  secrets_kms: string;
  logging_tracing_metrics: string;
  backup_and_disaster_recovery: string;
  cost_governance: string;
  cost_and_rate_limit_enforcement: string;
  what_changes_from_mvp: string[];
}

/** Phase 4: list-based (current), legacy deep (mvp object), or legacy flat. */
export interface Infrastructure {
  mvp?: InfraLayer[] | MvpInfrastructure;
  production?: InfraLayer[] | ProductionInfrastructure;
  graduation_path?: string;
  mermaid_mvp_stack?: string;
  mermaid_production_stack?: string;
  mermaid_mvp_to_production?: string;
  summary_bullets?: string[];
  hosting?: string;
  inference_provider?: string;
  vector_store?: string | null;
  queue?: string | null;
  secrets_manager?: string;
  rationale?: string;
}

export interface CostScenario {
  label: string;
  monthly_requests: number;
  avg_input_tokens: number;
  avg_output_tokens: number;
  monthly_cost_usd: number;
  notes: string | null;
}

export type CostKind =
  | "free"
  | "variable_usage"
  | "fixed_recurring"
  | "one_time"
  | "mixed";

export interface CostLineItem {
  item: string;
  tied_to: string;
  cost_kind: CostKind;
  monthly_min_usd: number | null;
  monthly_max_usd: number | null;
  notes: string;
}

export interface CostModel {
  line_items: CostLineItem[];
  stack_cost_summary: string;
  mvp_getting_started_note: string;
  scenarios: CostScenario[];
  primary_cost_driver: string;
  optimization_opportunities: string[];
  self_host_breakeven_requests_per_month: number | null;
}

export interface SecurityPlan {
  threats: string[];
  pii_handling: string;
  prompt_injection_mitigations: string[];
  rate_limiting: string;
  auth_strategy: string;
  compliance_notes: string[];
}

export interface ObservabilityPlan {
  metrics: string[];
  tracing_tool: string;
  log_sink: string;
  eval_strategy: string;
  alerting: string[];
}

export interface ScalingPlan {
  bottlenecks_at_10x: string[];
  bottlenecks_at_100x: string[];
  caching_strategy: string;
  failover_strategy: string;
  cost_at_scale_concerns: string[];
}

export interface RedTeamFinding {
  severity: "critical" | "high" | "medium" | "low" | string;
  phase_id: string;
  concern: string;
  suggested_mitigation: string;
}

export interface RedTeamCritique {
  findings: RedTeamFinding[];
  overall_confidence: "high" | "medium" | "low" | string;
  summary: string;
}

export interface FullPlan {
  plan_id: string;
  idea: string;
  created_at: string;
  pressure_test: PressureTestResult;
  problem_model_fit: ProblemModelFit;
  architecture: Architecture;
  build_buy_train: BuildBuyTrain | ToolsOpenSourcePhase;
  infrastructure: Infrastructure;
  cost_model: CostModel;
  security: SecurityPlan;
  observability: ObservabilityPlan;
  scaling: ScalingPlan;
  red_team: RedTeamCritique;
  executive_summary: string;
  next_steps: string[];
  total_cost_usd: number;
}

export interface ChatRequest {
  idea: string;
  active_phase_order?: string[] | null;
  clarifying_answers?: Record<string, string> | null;
  plan_id?: string | null;
}

export type SseEventName =
  | "init"
  | "phase_start"
  | "phase_complete"
  | "clarify"
  | "red_team"
  | "synthesizer"
  | "done"
  | "error";

export interface SseInit {
  event: "init";
  data: { plan_id: string; active_phase_order?: string[] };
}

export interface SsePhaseStart {
  event: "phase_start";
  phase_id: string;
  data: { title: string };
}

export interface SsePhaseComplete {
  event: "phase_complete";
  phase_id: string;
  data: { title: string; output: any };
}

export interface SseRedTeam {
  event: "red_team";
  data: { critique: any };
}

export interface SseClarify {
  event: "clarify";
  data: { questions: any[] };
}

export interface SseDiff {
  event: "diff";
  data: { diff: any[] };
}

export interface SseChatReply {
  event: "chat_reply";
  data: { message: string };
}

export interface SseSynthesizer {
  event: "synthesizer";
  data: { plan_id: string };
}

export interface SseDone {
  event: "done";
  data: { plan_id: string; plan: FullPlan | null };
}

export interface SseError {
  event: "error";
  phase_id?: string;
  data: { message: string };
}

export type SseEvent =
  | SseInit
  | SsePhaseStart
  | SsePhaseComplete
  | SseRedTeam
  | SseClarify
  | SseDiff
  | SseChatReply
  | SseSynthesizer
  | SseDone
  | SseError;

export interface ChatResponse {
  plan: FullPlan;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number };

/** Static labels for the 9 plan phases, used in placeholder UI. */
export const PLAN_PHASES: { id: string; title: string; blurb: string }[] = [
  {
    id: "P0",
    title: "Pressure test",
    blurb: "Is this idea worth building? Existing solutions, differentiators, risks.",
  },
  {
    id: "P1",
    title: "Problem / model fit",
    blurb: "Is this actually an LLM problem? Success criteria and failure modes.",
  },
  {
    id: "P2",
    title: "Architecture",
    blurb: "Reference architecture: RAG, agent, router, pipeline, or hybrid.",
  },
  {
    id: "P3",
    title: "Tools & open source",
    blurb: "GitHub-backed repos plus concrete managed tools and services for your build.",
  },
  {
    id: "P4",
    title: "Infrastructure",
    blurb: "MVP and production infra layers, graduation path, and diagrams—only what this product needs.",
  },
  {
    id: "P5",
    title: "Cost model",
    blurb: "Deterministic cost projections at 100, 1k, and 10k users.",
  },
  {
    id: "P6.25",
    title: "Security",
    blurb: "OWASP-LLM threats, PII handling, prompt injection, auth, compliance.",
  },
  {
    id: "P6.5",
    title: "Observability",
    blurb: "Metrics, tracing, logs, evaluation strategy, alerting.",
  },
  {
    id: "P7",
    title: "Scaling",
    blurb: "Bottlenecks at 10x and 100x, caching, failover, cost at scale.",
  },
];
