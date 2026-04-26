"use client";

import * as React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PhaseCard } from "@/components/brand/phase-card";
import { Skeleton } from "@/components/ui/skeleton";
import { PhaseOutputRenderer } from "./phase-output";
import { ArchitectureDiagram } from "./architecture-diagram";
import { InfrastructureDiagram } from "./infrastructure-diagram";
import { CostChart } from "./cost-chart";
import { RedTeamPanel } from "./red-team-panel";
import { SynthesisPanel } from "./synthesis-panel";
import { PLAN_PHASES } from "@/lib/types";
import type { FullPlan, RedTeamCritique, Architecture, CostModel, Infrastructure } from "@/lib/types";
import type { PhaseState } from "@/hooks/use-plan-stream";

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface ReportPanelProps {
  phases: Record<string, PhaseState>;
  redTeam: RedTeamCritique | null;
  plan: FullPlan | null;
  activePhaseId: string | null;
  activePhaseOrder?: string[] | null;
  onEditRequest?: (phaseId: string) => void;
}

/* ------------------------------------------------------------------ */
/*  Loading skeleton for pending phase                                 */
/* ------------------------------------------------------------------ */

function PhaseSkeleton() {
  return (
    <div className="space-y-3 pt-2">
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-[92%]" />
      <Skeleton className="h-3 w-[78%]" />
      <Skeleton className="h-3 w-[88%]" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Extra phase-specific visualizations                                */
/* ------------------------------------------------------------------ */

function ExtraVisuals({
  phaseId,
  output,
}: {
  phaseId: string;
  output: unknown;
}) {
  if (phaseId === "P2" && output) {
    return (
      <div className="mt-5 border-t border-border/40 pt-5">
        <ArchitectureDiagram data={output as Architecture} />
      </div>
    );
  }
  if (phaseId === "P4" && output) {
    return (
      <div className="mt-5 border-t border-border/40 pt-5">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground mb-3">
          Diagrams
        </h4>
        <InfrastructureDiagram data={output as Infrastructure} />
      </div>
    );
  }
  if (phaseId === "P5" && output) {
    return (
      <div className="mt-5 border-t border-border/40 pt-5">
        <CostChart data={output as CostModel} />
      </div>
    );
  }
  return null;
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export function ReportPanel({
  phases,
  redTeam,
  plan,
  activePhaseId,
  activePhaseOrder,
  onEditRequest,
}: ReportPanelProps) {
  const phaseList = React.useMemo(() => {
    if (!activePhaseOrder || activePhaseOrder.length === 0) return PLAN_PHASES;
    const allowed = new Set(activePhaseOrder);
    return PLAN_PHASES.filter((p) => allowed.has(p.id));
  }, [activePhaseOrder]);

  // Find the first non-complete phase to default to, or the active one
  const defaultTab =
    activePhaseId ??
    phaseList.find((p) => phases[p.id]?.status !== "complete")?.id ??
    phaseList[0]?.id ??
    PLAN_PHASES[0].id;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight text-foreground">
          Report
        </h2>
        <span className="font-mono text-[11px] text-muted-foreground">
          {Object.values(phases).filter((p) => p.status === "complete").length} / {phaseList.length} phases
        </span>
      </div>

      {/* Tabs */}
      <div className="flex-1 overflow-y-auto">
        <Tabs defaultValue={defaultTab} className="px-4 pt-4 pb-8">
          <TabsList className="flex-wrap">
            {phaseList.map((p) => {
              const ps = phases[p.id];
              const isActive = ps?.status === "running";
              const isDone = ps?.status === "complete";
              return (
                <TabsTrigger key={p.id} value={p.id}>
                  <span className="flex items-center gap-1.5">
                    {isActive && (
                      <span className="h-1.5 w-1.5 rounded-full bg-[oklch(0.78_0.16_230)] animate-pulse" />
                    )}
                    {isDone && (
                      <span className="h-1.5 w-1.5 rounded-full bg-[oklch(0.78_0.18_150)]" />
                    )}
                    {p.id}
                  </span>
                </TabsTrigger>
              );
            })}
            <TabsTrigger value="red-team">Red Team</TabsTrigger>
            <TabsTrigger value="synthesis">Synthesis</TabsTrigger>
          </TabsList>

          {/* Phase tab panels */}
          {phaseList.map((p) => {
            const ps = phases[p.id];
            return (
              <TabsContent key={p.id} value={p.id} className="pt-4">
                <PhaseCard
                  phaseId={p.id}
                  title={p.title}
                  description={p.blurb}
                  status={ps?.status ?? "pending"}
                  onEditRequest={onEditRequest ? () => onEditRequest(p.id) : undefined}
                >
                  {ps?.status === "complete" && ps.output ? (
                    <>
                      <PhaseOutputRenderer phaseId={p.id} data={ps.output} />
                      <ExtraVisuals phaseId={p.id} output={ps.output} />
                    </>
                  ) : ps?.status === "running" ? (
                    <PhaseSkeleton />
                  ) : (
                    <p className="text-xs text-muted-foreground pt-2">
                      Waiting for this phase to run...
                    </p>
                  )}
                </PhaseCard>
              </TabsContent>
            );
          })}

          {/* Red Team */}
          <TabsContent value="red-team" className="pt-4">
            <PhaseCard
              phaseId="RT"
              title="Red-team critique"
              status={redTeam ? "complete" : "pending"}
            >
              {redTeam ? (
                <RedTeamPanel critique={redTeam} />
              ) : (
                <p className="text-xs text-muted-foreground pt-2">
                  Adversarial findings will appear after the red team pass.
                </p>
              )}
            </PhaseCard>
          </TabsContent>

          {/* Synthesis */}
          <TabsContent value="synthesis" className="pt-4">
            <PhaseCard
              phaseId="\u03A3"
              title="Executive synthesis"
              status={plan ? "complete" : "pending"}
            >
              {plan ? (
                <SynthesisPanel plan={plan} />
              ) : (
                <p className="text-xs text-muted-foreground pt-2">
                  Executive summary and next steps will appear once all phases complete.
                </p>
              )}
            </PhaseCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
