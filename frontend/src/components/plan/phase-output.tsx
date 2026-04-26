"use client";

import * as React from "react";
import {
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Server,
  Brain,
  Wrench,
  BarChart3,
  Eye,
  TrendingUp,
  Cloud,
  Package,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  PressureTestResult,
  ProblemModelFit,
  Architecture,
  ArchitectureComponent,
  MvpInfrastructure,
  ProductionInfrastructure,
  BuildBuyTrain,
  ToolsOpenSourcePhase,
  InfraLayer,
  Infrastructure,
  CostModel,
  CostLineItem,
  SecurityPlan,
  ObservabilityPlan,
  ScalingPlan,
} from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Shared helpers                                                     */
/* ------------------------------------------------------------------ */

function Section({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </h4>
      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (!items.length) return <p className="text-sm text-muted-foreground">None</p>;
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm leading-relaxed text-foreground/85">
          <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/50" />
          {item}
        </li>
      ))}
    </ul>
  );
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 border-b border-border/40 last:border-0">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <span className="text-sm text-foreground/90 text-right">{value ?? "—"}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P0 — Pressure Test                                                 */
/* ------------------------------------------------------------------ */

export function PressureTestOutput({ data }: { data: PressureTestResult }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        {data.is_viable ? (
          <Badge variant="success">
            <CheckCircle2 className="h-3 w-3" /> Viable
          </Badge>
        ) : (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3" /> Not Viable
          </Badge>
        )}
        {data.refusal_reason && (
          <span className="text-sm text-muted-foreground">{data.refusal_reason}</span>
        )}
      </div>
      <Section label="Summary">
        <p className="text-sm leading-relaxed text-foreground/85">{data.summary}</p>
      </Section>
      <Section label="Similar existing solutions">
        <BulletList items={data.similar_existing_solutions} />
      </Section>
      <Section label="Differentiators">
        <BulletList items={data.differentiators} />
      </Section>
      <Section label="Risks">
        <BulletList items={data.risks} />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P1 — Problem / Model Fit                                           */
/* ------------------------------------------------------------------ */

export function ProblemModelFitOutput({ data }: { data: ProblemModelFit }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Brain className="h-3 w-3" /> {data.problem_type}
        </Badge>
      </div>
      <Section label="Why an LLM?">
        <p className="text-sm leading-relaxed text-foreground/85">{data.why_llm}</p>
      </Section>
      {data.deterministic_alternative && (
        <Section label="Deterministic alternative">
          <p className="text-sm text-foreground/85">{data.deterministic_alternative}</p>
        </Section>
      )}
      <Section label="Success criteria">
        <BulletList items={data.success_criteria} />
      </Section>
      <Section label="Failure modes">
        <BulletList items={data.failure_modes} />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P2 — Architecture                                                  */
/* ------------------------------------------------------------------ */

/** New Phase 2 "deep" payloads include scope_definition; old saved plans do not. */
function isDeepPhase2Architecture(
  data: unknown,
): data is Architecture {
  if (!data || typeof data !== "object") return false;
  const s = (data as { scope_definition?: unknown }).scope_definition;
  return (
    s != null && typeof s === "object" && s !== null && "problem_why" in s
  );
}

function LegacyArchitectureOutput({ data }: { data: Record<string, unknown> }) {
  const pattern = (typeof data.pattern === "string" ? data.pattern : "hybrid") as Architecture["pattern"];
  const components = (
    Array.isArray(data.components) ? data.components : []
  ) as ArchitectureComponent[];
  const dataFlow = typeof data.data_flow === "string" ? data.data_flow : "";
  const tradeoffs = (Array.isArray(data.notable_tradeoffs)
    ? data.notable_tradeoffs
    : []) as string[];

  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Server className="h-3 w-3" /> {pattern}
        </Badge>
      </div>
      <Section label="Components">
        <div className="space-y-2">
          {components.length === 0 ? (
            <p className="text-sm text-muted-foreground">None</p>
          ) : (
            components.map((c, i) => (
              <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
                <p className="text-sm font-medium text-foreground">{c.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{c.purpose}</p>
                <Badge variant="outline" className="mt-1.5 text-[10px]">{c.technology}</Badge>
              </div>
            ))
          )}
        </div>
      </Section>
      <Section label="Data flow">
        <p className="text-sm leading-relaxed text-foreground/85 font-mono text-xs bg-muted/40 rounded-lg p-3 border border-border/40">
          {dataFlow || "—"}
        </p>
      </Section>
      <Section label="Notable tradeoffs">
        <BulletList items={tradeoffs} />
      </Section>
    </div>
  );
}

function DeepPhase2ArchitectureOutput({ data }: { data: Architecture }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Server className="h-3 w-3" /> {data.pattern}
        </Badge>
      </div>
      <Section label="Scope definition">
        <div className="space-y-3">
          <div className="rounded-lg border border-border/60 bg-muted/30 p-3">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
              Problem / why
            </p>
            <p className="mt-1 text-sm leading-relaxed text-foreground/85">
              {data.scope_definition.problem_why}
            </p>
          </div>
          <Section label="Personas & roles">
            <BulletList items={data.scope_definition.personas_and_roles} />
          </Section>
          <Section label="MVP definition">
            <BulletList items={data.scope_definition.mvp_definition} />
          </Section>
          <Section label="Success in 3 months">
            <BulletList items={data.scope_definition.success_in_3_months} />
          </Section>
        </div>
      </Section>
      <Section label="Feature modules (user stories → modules)">
        <div className="space-y-3">
          {data.feature_modules.map((m, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{m.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{m.description}</p>
              <div className="mt-2 space-y-1">
                {m.user_stories.map((s, j) => (
                  <p key={j} className="text-xs text-foreground/80">
                    <span className="font-mono text-muted-foreground">As a</span> {s.as_a},{" "}
                    <span className="font-mono text-muted-foreground">I want</span> {s.i_want},{" "}
                    <span className="font-mono text-muted-foreground">so that</span> {s.so_that}.
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
      <Section label="System architecture (services & boundaries)">
        <div className="space-y-2">
          {data.system_architecture.map((c, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{c.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{c.responsibility}</p>
              <Badge variant="outline" className="mt-1.5 text-[10px]">
                {c.technology}
              </Badge>
              {c.scaling_notes && (
                <p className="mt-2 text-xs text-foreground/75">{c.scaling_notes}</p>
              )}
            </div>
          ))}
        </div>
      </Section>
      <Section label="Components">
        <div className="space-y-2">
          {data.components.map((c, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{c.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{c.purpose}</p>
              <Badge variant="outline" className="mt-1.5 text-[10px]">{c.technology}</Badge>
            </div>
          ))}
        </div>
      </Section>
      <Section label="Data flow">
        <p className="text-sm leading-relaxed text-foreground/85 font-mono text-xs bg-muted/40 rounded-lg p-3 border border-border/40">
          {data.data_flow}
        </p>
      </Section>
      <Section label="Data model (ERD sketch)">
        <div className="space-y-2">
          {data.data_model.map((e, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{e.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5">PK: {e.primary_key}</p>
              <div className="mt-2">
                <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  Fields
                </p>
                <BulletList items={e.fields} />
              </div>
              {!!e.indexes?.length && (
                <div className="mt-2">
                  <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                    Indexes
                  </p>
                  <BulletList items={e.indexes} />
                </div>
              )}
              {!!e.relationships?.length && (
                <div className="mt-2">
                  <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                    Relationships
                  </p>
                  <BulletList items={e.relationships} />
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>
      <Section label="API design">
        <FieldRow label="Style" value={data.api_design.style} />
        <FieldRow label="Auth strategy" value={data.api_design.auth_strategy} />
        <FieldRow label="Error model" value={data.api_design.error_model} />
        <FieldRow label="Rate limiting" value={data.api_design.rate_limiting} />
        <Section label="Endpoints">
          <div className="space-y-2">
            {data.api_design.endpoints.map((ep, i) => (
              <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
                <p className="text-xs font-mono text-foreground/85">
                  {ep.method.toUpperCase()} {ep.path}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{ep.purpose}</p>
                {ep.auth && (
                  <Badge variant="outline" className="mt-1.5 text-[10px]">
                    {ep.auth}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </Section>
      </Section>
      <Section label="UI/UX approach">
        <Section label="Key screens">
          <BulletList items={data.ui_ux_approach.key_screens} />
        </Section>
        <Section label="Component tree notes">
          <p className="text-sm leading-relaxed text-foreground/85">
            {data.ui_ux_approach.component_tree_notes}
          </p>
        </Section>
        <Section label="Design system notes">
          <p className="text-sm leading-relaxed text-foreground/85">
            {data.ui_ux_approach.design_system_notes}
          </p>
        </Section>
        <FieldRow label="Mobile strategy" value={data.ui_ux_approach.mobile_strategy} />
      </Section>
      <Section label="Security design">
        <Section label="Roles & permissions">
          <BulletList items={data.security_design.roles_and_permissions} />
        </Section>
        <FieldRow label="PII handling" value={data.security_design.pii_handling} />
        <Section label="Prompt injection controls">
          <BulletList items={data.security_design.prompt_injection_controls} />
        </Section>
        <Section label="Secrets & keys">
          <BulletList items={data.security_design.secrets_and_keys} />
        </Section>
        <Section label="Security basics">
          <BulletList items={data.security_design.security_basics} />
        </Section>
      </Section>
      <Section label="Deployment plan">
        <Section label="Environments">
          <BulletList items={data.deployment_plan.environments} />
        </Section>
        <FieldRow label="Hosting" value={data.deployment_plan.hosting} />
        <FieldRow label="CI/CD" value={data.deployment_plan.ci_cd} />
        <FieldRow label="Observability" value={data.deployment_plan.observability} />
        {data.deployment_plan.cost_notes && (
          <FieldRow label="Cost notes" value={data.deployment_plan.cost_notes} />
        )}
      </Section>
      <Section label="Build phases (execution plan)">
        <div className="space-y-2">
          {data.build_phases.map((bp, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{bp.phase}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{bp.goal}</p>
              <div className="mt-2">
                <BulletList items={bp.deliverables} />
              </div>
            </div>
          ))}
        </div>
      </Section>
      <Section label="Risk analysis">
        <div className="space-y-2">
          {data.risk_analysis.map((r, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">{r.risk}</p>
              <p className="mt-1 text-xs text-muted-foreground">Impact: {r.impact}</p>
              <p className="mt-1 text-xs text-foreground/80">Mitigation: {r.mitigation}</p>
            </div>
          ))}
        </div>
      </Section>
      <Section label="Notable tradeoffs">
        <BulletList items={data.notable_tradeoffs} />
      </Section>
    </div>
  );
}

export function ArchitectureOutput({ data }: { data: Architecture }) {
  if (!isDeepPhase2Architecture(data)) {
    return (
      <LegacyArchitectureOutput data={data as unknown as Record<string, unknown>} />
    );
  }
  return <DeepPhase2ArchitectureOutput data={data} />;
}

/* ------------------------------------------------------------------ */
/*  P3 — Tools & open source (legacy build/buy supported)             */
/* ------------------------------------------------------------------ */

export function BuildBuyTrainOutput({ data }: { data: BuildBuyTrain }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Wrench className="h-3 w-3" /> {data.recommendation}
        </Badge>
        {data.fine_tune_recommended && (
          <Badge variant="warning">Fine-tune recommended</Badge>
        )}
      </div>
      <Section label="Rationale">
        <p className="text-sm leading-relaxed text-foreground/85">{data.rationale}</p>
      </Section>
      <Section label="Candidate vendors">
        <BulletList items={data.candidate_vendors} />
      </Section>
      {data.fine_tune_dataset_size_estimate != null && (
        <FieldRow
          label="Estimated dataset size"
          value={`~${data.fine_tune_dataset_size_estimate.toLocaleString()} samples`}
        />
      )}
    </div>
  );
}

export function ToolsOpenSourceOutput({ data }: { data: ToolsOpenSourcePhase }) {
  const sc = data.search_context;
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Package className="h-3 w-3" /> Tools &amp; open source
        </Badge>
      </div>
      <Section label="GitHub search">
        <FieldRow label="Query used" value={sc?.query_used ?? "—"} />
        <FieldRow label="Repos in prompt" value={String(sc?.repo_count_returned ?? 0)} />
        <FieldRow label="Total (estimate)" value={sc?.total_count_estimate != null ? String(sc.total_count_estimate) : "—"} />
        <FieldRow label="Note" value={sc?.search_note ?? "—"} />
      </Section>
      <Section label="GitHub recommendations">
        {data.github_recommendations.length === 0 ? (
          <p className="text-sm text-muted-foreground">None — search returned no curated repos.</p>
        ) : (
          <div className="space-y-3">
            {data.github_recommendations.map((repo, i) => (
              <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
                <p className="text-sm font-medium text-foreground">
                  <a href={repo.url} className="underline-offset-2 hover:underline" target="_blank" rel="noreferrer">
                    {repo.name}
                  </a>{" "}
                  <span className="text-xs text-muted-foreground">({repo.stars} stars)</span>
                </p>
                <p className="mt-1 text-xs text-muted-foreground">Updated {repo.last_updated}</p>
                <p className="mt-2 text-sm text-foreground/85">{repo.why_relevant}</p>
                <p className="mt-1 text-xs text-foreground/80">{repo.how_to_integrate}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  License: {repo.license ?? "—"} — {repo.license_risks}
                </p>
              </div>
            ))}
          </div>
        )}
      </Section>
      <Section label="Managed tools &amp; services">
        <div className="space-y-3">
          {data.managed_tools.map((t, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <p className="text-sm font-medium text-foreground">
                {t.name}{" "}
                <span className="text-xs font-normal text-muted-foreground">({t.category})</span>
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{t.role_in_app}</p>
              <p className="mt-2 text-sm text-foreground/85">{t.rationale}</p>
              {t.product_url && (
                <a href={t.product_url} className="mt-1 inline-block text-xs underline" target="_blank" rel="noreferrer">
                  {t.product_url}
                </a>
              )}
            </div>
          ))}
        </div>
      </Section>
      <Section label="How it fits together">
        <p className="text-sm leading-relaxed text-foreground/85">{data.integration_summary}</p>
      </Section>
    </div>
  );
}

function isLegacyBuildBuyTrain(data: unknown): data is BuildBuyTrain {
  return (
    typeof data === "object" &&
    data !== null &&
    "recommendation" in data &&
    typeof (data as BuildBuyTrain).recommendation === "string"
  );
}

export function Phase3Output({ data }: { data: BuildBuyTrain | ToolsOpenSourcePhase }) {
  if (isLegacyBuildBuyTrain(data)) {
    return <BuildBuyTrainOutput data={data} />;
  }
  return <ToolsOpenSourceOutput data={data} />;
}

/* ------------------------------------------------------------------ */
/*  P4 — Infrastructure                                                */
/* ------------------------------------------------------------------ */

type DeepInfra = Infrastructure & {
  mvp: MvpInfrastructure;
  production: ProductionInfrastructure;
};

/** Only show a row when the value is set—legacy flat infra. */
function p4OptionalRow(
  label: string,
  value: string | null | undefined,
): React.ReactNode {
  if (value == null || (typeof value === "string" && !value.trim())) {
    return null;
  }
  return <FieldRow label={label} value={value} />;
}

function isListPhase4Infrastructure(data: unknown): data is Infrastructure & {
  mvp: InfraLayer[];
  production: InfraLayer[];
} {
  if (!data || typeof data !== "object") return false;
  const o = data as Infrastructure;
  const m = o.mvp;
  const p = o.production;
  if (!Array.isArray(m) || !Array.isArray(p) || m.length === 0 || p.length === 0) {
    return false;
  }
  const m0 = m[0] as Record<string, unknown>;
  return typeof m0?.name === "string" && typeof m0?.details === "string";
}

function isDeepObjectPhase4Infrastructure(data: unknown): data is DeepInfra {
  if (!data || typeof data !== "object") return false;
  const o = data as Record<string, unknown>;
  const m = o.mvp;
  const p = o.production;
  return (
    m != null &&
    typeof m === "object" &&
    !Array.isArray(m) &&
    "philosophy" in (m as object) &&
    p != null &&
    typeof p === "object" &&
    !Array.isArray(p) &&
    "philosophy" in (p as object)
  );
}

function LegacyInfrastructureOutput({ data }: { data: Infrastructure }) {
  return (
    <div className="space-y-4 animate-in-fade">
      <FieldRow label="Hosting" value={data.hosting ?? "—"} />
      <FieldRow label="Inference provider" value={data.inference_provider ?? "—"} />
      {p4OptionalRow("Vector / semantic store", data.vector_store)}
      {p4OptionalRow("Queue / messaging", data.queue)}
      <FieldRow label="Secrets manager" value={data.secrets_manager ?? "—"} />
      <Section label="Rationale">
        <p className="text-sm leading-relaxed text-foreground/85">{data.rationale ?? "—"}</p>
      </Section>
    </div>
  );
}

function DynamicInfrastructureOutput({
  data,
}: {
  data: Infrastructure & { mvp: InfraLayer[]; production: InfraLayer[] };
}) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Cloud className="h-3 w-3" /> Infrastructure
        </Badge>
      </div>
      {data.summary_bullets && data.summary_bullets.length > 0 && (
        <Section label="At a glance">
          <BulletList items={data.summary_bullets} />
        </Section>
      )}
      <div className="rounded-lg border border-border/50 bg-muted/20 p-4 space-y-4">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          MVP layers
        </h4>
        <div className="space-y-4">
          {data.mvp.map((layer, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-background/60 p-3">
              <p className="text-sm font-medium text-foreground">{layer.name}</p>
              <p className="mt-1 text-sm leading-relaxed text-foreground/85">{layer.details}</p>
              {layer.bullets && layer.bullets.length > 0 && (
                <div className="mt-2">
                  <BulletList items={layer.bullets} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-border/50 bg-muted/20 p-4 space-y-4">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          Production layers
        </h4>
        <div className="space-y-4">
          {data.production.map((layer, i) => (
            <div key={i} className="rounded-lg border border-border/60 bg-background/60 p-3">
              <p className="text-sm font-medium text-foreground">{layer.name}</p>
              <p className="mt-1 text-sm leading-relaxed text-foreground/85">{layer.details}</p>
              {layer.bullets && layer.bullets.length > 0 && (
                <div className="mt-2">
                  <BulletList items={layer.bullets} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      {data.graduation_path && (
        <Section label="MVP → production (graduation path)">
          <p className="text-sm leading-relaxed text-foreground/85 whitespace-pre-wrap">
            {data.graduation_path}
          </p>
        </Section>
      )}
    </div>
  );
}

function DeepInfrastructureOutput({ data }: { data: DeepInfra }) {
  const m = data.mvp;
  const p = data.production;
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Cloud className="h-3 w-3" /> MVP &amp; production
        </Badge>
      </div>

      <Section label="At a glance (production)">
        <FieldRow label="Hosting" value={data.hosting} />
        <FieldRow label="Inference" value={data.inference_provider} />
        {p4OptionalRow("Vector / semantic store", data.vector_store)}
        {p4OptionalRow("Queue / messaging", data.queue)}
        <FieldRow label="Secrets" value={data.secrets_manager} />
      </Section>

      <Section label="Rationale">
        <p className="text-sm leading-relaxed text-foreground/85">{data.rationale}</p>
      </Section>

      <div className="rounded-lg border border-border/50 bg-muted/20 p-4 space-y-4">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          MVP infrastructure
        </h4>
        <p className="text-sm text-foreground/90">{m.philosophy}</p>
        <div className="space-y-0 border-t border-border/40 pt-3">
          <FieldRow label="Inference &amp; models" value={m.inference_and_models} />
          <FieldRow label="Frontend" value={m.frontend_hosting} />
          <FieldRow label="Backend / API" value={m.backend_api} />
          <FieldRow label="Database" value={m.database} />
          <FieldRow label="File / object storage" value={m.file_object_storage} />
          <FieldRow label="Auth &amp; identity" value={m.auth_identity} />
          {p4OptionalRow("Vector / semantic (embeddings, RAG, hybrid search)", m.vector_search)}
          {p4OptionalRow("Async / queue", m.async_and_queue)}
          <FieldRow label="Secrets &amp; config" value={m.secrets_and_config} />
          <FieldRow label="Domain &amp; TLS" value={m.domain_and_tls} />
          <FieldRow label="Monitoring &amp; errors" value={m.monitoring_errors} />
          <FieldRow label="CI / CD" value={m.ci_cd} />
        </div>
        <Section label="Explicitly deferred to production">
          <BulletList items={m.explicitly_deferred_to_production} />
        </Section>
        <Section label="MVP tradeoffs &amp; risks">
          <BulletList items={m.mvp_risks} />
        </Section>
      </div>

      <div className="rounded-lg border border-border/50 bg-muted/20 p-4 space-y-4">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          Production infrastructure
        </h4>
        <p className="text-sm text-foreground/90">{p.philosophy}</p>
        <div className="space-y-0 border-t border-border/40 pt-3">
          <FieldRow label="Cloud / platform" value={p.primary_cloud} />
          <FieldRow label="Compute &amp; serving" value={p.compute_and_serving} />
          <FieldRow label="Database &amp; persistence" value={p.database_and_persistence} />
          <FieldRow label="Caching" value={p.caching} />
          <FieldRow label="CDN, WAF &amp; edge" value={p.cdn_waf_and_edge} />
          <FieldRow label="File / object storage" value={p.file_object_storage} />
          <FieldRow label="Auth &amp; identity" value={p.auth_identity} />
          {p4OptionalRow("Vector / semantic (as needed)", p.vector_and_search)}
          {p4OptionalRow("Messaging &amp; queue", p.messaging_and_queue)}
          <FieldRow label="Load balancing" value={p.load_balancing} />
          <FieldRow label="Autoscaling" value={p.autoscaling} />
          <FieldRow label="Network &amp; security" value={p.network_and_security} />
          <FieldRow label="CI / CD" value={p.ci_cd} />
          <FieldRow label="Secrets &amp; KMS" value={p.secrets_kms} />
          <FieldRow label="Logging, tracing, metrics" value={p.logging_tracing_metrics} />
          <FieldRow label="Backup &amp; DR" value={p.backup_and_disaster_recovery} />
          <FieldRow label="Cost governance" value={p.cost_governance} />
          <FieldRow label="Cost &amp; rate limits" value={p.cost_and_rate_limit_enforcement} />
        </div>
        <Section label="What changes from MVP">
          <BulletList items={p.what_changes_from_mvp} />
        </Section>
      </div>

      {data.graduation_path && (
        <Section label="MVP → production (graduation path)">
          <p className="text-sm leading-relaxed text-foreground/85 whitespace-pre-wrap">
            {data.graduation_path}
          </p>
        </Section>
      )}
    </div>
  );
}

export function InfrastructureOutput({ data }: { data: Infrastructure }) {
  if (isListPhase4Infrastructure(data)) {
    return <DynamicInfrastructureOutput data={data} />;
  }
  if (isDeepObjectPhase4Infrastructure(data)) {
    return <DeepInfrastructureOutput data={data} />;
  }
  return <LegacyInfrastructureOutput data={data} />;
}

/* ------------------------------------------------------------------ */
/*  P5 — Cost Model (stack line items + deterministic LLM table)     */
/* ------------------------------------------------------------------ */

function _costKindLabel(kind: CostLineItem["cost_kind"]): string {
  const m: Record<CostLineItem["cost_kind"], string> = {
    free: "Free / $0",
    variable_usage: "Usage-based",
    fixed_recurring: "Fixed (recurring)",
    one_time: "One-time",
    mixed: "Mixed",
  };
  return m[kind] ?? kind;
}

function _formatMonthlyRange(
  min: number | null | undefined,
  max: number | null | undefined,
): string {
  if (min == null && max == null) return "—";
  if (min != null && max != null && min === max) return `$${min.toFixed(2)}/mo`;
  if (min != null && max != null) return `$${min.toFixed(0)}–$${max.toFixed(0)}/mo`;
  if (min != null) return `from $${min.toFixed(2)}/mo`;
  return `up to $${max!.toFixed(2)}/mo`;
}

export function CostModelOutput({ data }: { data: CostModel }) {
  const lineItems = data.line_items?.length
    ? data.line_items
    : [];

  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <BarChart3 className="h-3 w-3" /> {data.primary_cost_driver}
        </Badge>
      </div>

      {data.stack_cost_summary ? (
        <Section label="Stack and build cost (tied to your plan)">
          <p className="text-sm leading-relaxed text-foreground/85 whitespace-pre-wrap">
            {data.stack_cost_summary}
          </p>
        </Section>
      ) : null}

      {data.mvp_getting_started_note ? (
        <Section label="Getting started (MVP budget order)">
          <p className="text-sm leading-relaxed text-foreground/85 whitespace-pre-wrap">
            {data.mvp_getting_started_note}
          </p>
        </Section>
      ) : null}

      {lineItems.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
            Tools, services, and infrastructure
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="py-2 pr-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                    Item
                  </th>
                  <th className="py-2 pr-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                    Tied to
                  </th>
                  <th className="py-2 pr-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                    Cost type
                  </th>
                  <th className="py-2 pr-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                    Est. $/mo
                  </th>
                  <th className="py-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">Notes</th>
                </tr>
              </thead>
              <tbody>
                {lineItems.map((row, i) => (
                  <tr key={i} className="border-b border-border/40">
                    <td className="py-2 pr-3 text-foreground/90 align-top">{row.item}</td>
                    <td className="py-2 pr-3 text-foreground/80 text-xs align-top whitespace-pre-wrap">
                      {row.tied_to}
                    </td>
                    <td className="py-2 pr-3 text-xs text-muted-foreground align-top">
                      {_costKindLabel(row.cost_kind)}
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs align-top">
                      {_formatMonthlyRange(row.monthly_min_usd, row.monthly_max_usd)}
                    </td>
                    <td className="py-2 text-muted-foreground text-xs align-top whitespace-pre-wrap">
                      {row.notes}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        LLM API usage (deterministic token math)
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="py-2 pr-4 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">Scenario</th>
              <th className="py-2 pr-4 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">Requests/mo</th>
              <th className="py-2 pr-4 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">Cost/mo</th>
              <th className="py-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">Notes</th>
            </tr>
          </thead>
          <tbody>
            {data.scenarios.map((s, i) => (
              <tr key={i} className="border-b border-border/40">
                <td className="py-2 pr-4 text-foreground/90">{s.label}</td>
                <td className="py-2 pr-4 font-mono text-foreground/80">
                  {s.monthly_requests.toLocaleString()}
                </td>
                <td className="py-2 pr-4 font-mono text-[oklch(0.85_0.18_150)]">
                  ${s.monthly_cost_usd.toFixed(2)}
                </td>
                <td className="py-2 text-muted-foreground text-xs">{s.notes ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Section label="Optimization opportunities">
        <BulletList items={data.optimization_opportunities} />
      </Section>

      {data.self_host_breakeven_requests_per_month != null && (
        <FieldRow
          label="Self-host breakeven"
          value={`${data.self_host_breakeven_requests_per_month.toLocaleString()} req/mo`}
        />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P6.25 — Security                                                   */
/* ------------------------------------------------------------------ */

export function SecurityOutput({ data }: { data: SecurityPlan }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="warning">
          <ShieldAlert className="h-3 w-3" /> Security plan
        </Badge>
      </div>
      <Section label="Threats">
        <BulletList items={data.threats} />
      </Section>
      <FieldRow label="PII handling" value={data.pii_handling} />
      <Section label="Prompt injection mitigations">
        <BulletList items={data.prompt_injection_mitigations} />
      </Section>
      <FieldRow label="Rate limiting" value={data.rate_limiting} />
      <FieldRow label="Auth strategy" value={data.auth_strategy} />
      <Section label="Compliance notes">
        <BulletList items={data.compliance_notes} />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P6.5 — Observability                                               */
/* ------------------------------------------------------------------ */

export function ObservabilityOutput({ data }: { data: ObservabilityPlan }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <Eye className="h-3 w-3" /> Observability
        </Badge>
      </div>
      <Section label="Metrics">
        <BulletList items={data.metrics} />
      </Section>
      <FieldRow label="Tracing tool" value={data.tracing_tool} />
      <FieldRow label="Log sink" value={data.log_sink} />
      <FieldRow label="Eval strategy" value={data.eval_strategy} />
      <Section label="Alerting">
        <BulletList items={data.alerting} />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  P7 — Scaling                                                       */
/* ------------------------------------------------------------------ */

export function ScalingOutput({ data }: { data: ScalingPlan }) {
  return (
    <div className="space-y-5 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="info">
          <TrendingUp className="h-3 w-3" /> Scaling plan
        </Badge>
      </div>
      <Section label="Bottlenecks at 10x">
        <BulletList items={data.bottlenecks_at_10x} />
      </Section>
      <Section label="Bottlenecks at 100x">
        <BulletList items={data.bottlenecks_at_100x} />
      </Section>
      <FieldRow label="Caching strategy" value={data.caching_strategy} />
      <FieldRow label="Failover strategy" value={data.failover_strategy} />
      <Section label="Cost at scale concerns">
        <BulletList items={data.cost_at_scale_concerns} />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Dispatcher — renders the right output component per phase id       */
/* ------------------------------------------------------------------ */

const RENDERERS: Record<string, React.ComponentType<{ data: unknown }>> = {
  P0: PressureTestOutput as React.ComponentType<{ data: unknown }>,
  P1: ProblemModelFitOutput as React.ComponentType<{ data: unknown }>,
  P2: ArchitectureOutput as React.ComponentType<{ data: unknown }>,
  P3: Phase3Output as React.ComponentType<{ data: unknown }>,
  P4: InfrastructureOutput as React.ComponentType<{ data: unknown }>,
  P5: CostModelOutput as React.ComponentType<{ data: unknown }>,
  "P6.25": SecurityOutput as React.ComponentType<{ data: unknown }>,
  "P6.5": ObservabilityOutput as React.ComponentType<{ data: unknown }>,
  P7: ScalingOutput as React.ComponentType<{ data: unknown }>,
};

export function PhaseOutputRenderer({
  phaseId,
  data,
}: {
  phaseId: string;
  data: unknown;
}) {
  const Renderer = RENDERERS[phaseId];
  if (!Renderer || !data) {
    return (
      <pre className="text-xs text-muted-foreground overflow-auto max-h-80 rounded-lg bg-muted/30 p-3 border border-border/40">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  }
  return <Renderer data={data} />;
}
