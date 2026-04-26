"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { Clock, Cpu, DollarSign, Download, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MetricChip } from "@/components/brand/metric-chip";
import { ChatPanel } from "@/components/plan/chat";
import { ReportPanel } from "@/components/plan/report-panel";
import { VersionHistory } from "@/components/plan/version-history";
import { PlanHistory } from "@/components/plan/plan-history";
import { usePlanStream } from "@/hooks/use-plan-stream";
import { getPlan } from "@/lib/api";
import type { FullPlan } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Status label                                                       */
/* ------------------------------------------------------------------ */

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "idle":
      return <Badge variant="outline">Ready</Badge>;
    case "connecting":
      return (
        <Badge variant="info">
          <Loader2 className="h-3 w-3 animate-spin" /> Connecting...
        </Badge>
      );
    case "streaming":
      return (
        <Badge variant="info">
          <Loader2 className="h-3 w-3 animate-spin" /> Generating...
        </Badge>
      );
    case "clarifying":
      return <Badge variant="warning">Waiting for answers</Badge>;
    case "complete":
      return <Badge variant="success">Complete</Badge>;
    case "error":
      return <Badge variant="destructive">Error</Badge>;
    default:
      return null;
  }
}

/* ------------------------------------------------------------------ */
/*  Format seconds → mm:ss                                             */
/* ------------------------------------------------------------------ */

function fmtTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function PlanPage() {
  const params = useParams<{ id: string }>();
  const planId = params.id;

  const stream = usePlanStream(planId);
  const [existingPlan, setExistingPlan] = React.useState<FullPlan | null>(null);
  const [loadingExisting, setLoadingExisting] = React.useState(true);
  const [editPrompt, setEditPrompt] = React.useState<string | undefined>();
  const hasStartedRef = React.useRef(false);
  const [conversationLoaded, setConversationLoaded] = React.useState(false);

  const handleEditRequest = React.useCallback((phaseId: string) => {
    // Convert e.g., P2 to Phase 2
    const phaseName = phaseId.startsWith("P") ? `Phase ${phaseId.slice(1)}` : phaseId;
    setEditPrompt(`I want to change ${phaseName}: `);
  }, []);

  /* ---------------------------------------------------------------- */
  /*  On mount: try to load an existing plan from backend              */
  /* ---------------------------------------------------------------- */
  React.useEffect(() => {
    let cancelled = false;

    async function load() {
      const result = await getPlan(planId);
      if (cancelled) return;

      if (result.ok && result.data?.plan) {
        setExistingPlan(result.data.plan);
      }
      setLoadingExisting(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [planId]);

  /* ---------------------------------------------------------------- */
  /*  Load conversation history                                        */
  /* ---------------------------------------------------------------- */
  React.useEffect(() => {
    if (conversationLoaded) return;
    if (loadingExisting) return;
    if (!existingPlan) return;

    let cancelled = false;

    async function loadConversation() {
      const { getConversation } = await import("@/lib/api");
      const result = await getConversation(planId);
      if (cancelled) return;

      if (result.ok && result.data?.messages) {
        // Convert backend messages to frontend format
        const messages = result.data.messages.map((msg) => ({
          id: msg.id,
          role: msg.role as "user" | "assistant" | "system",
          content: msg.content,
          timestamp: new Date(msg.created_at).getTime(),
        }));
        
        // Load messages into stream state
        // Mark as complete if the plan has an executive summary (fully synthesized)
        const isComplete = !!existingPlan?.executive_summary;
        stream.loadMessages(messages, isComplete);
      }
      setConversationLoaded(true);
    }

    loadConversation();
    return () => {
      cancelled = true;
    };
  }, [planId, loadingExisting, existingPlan, conversationLoaded, stream]);

  /* ---------------------------------------------------------------- */
  /*  If redirected from /plan/new with idea param, auto-start stream  */
  /* ---------------------------------------------------------------- */
  React.useEffect(() => {
    if (hasStartedRef.current) return;
    if (loadingExisting) return;

    // If redirected from /plan/new, we include ?idea=... and should start the stream.
    // Start even if a plan record exists, because the backend may not have synthesized it yet.
    const url = new URL(window.location.href);
    const idea = url.searchParams.get("idea");
    if (idea) {
      // Only start the stream if we don't have a complete plan already
      // This prevents re-sending the idea on page refresh
      if (!existingPlan || !existingPlan.executive_summary) {
        hasStartedRef.current = true;
        stream.startPlan(idea);
      }
      
      // Remove the idea param from URL to prevent re-triggering on refresh
      url.searchParams.delete("idea");
      window.history.replaceState({}, "", url.toString());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingExisting, existingPlan]);

  /* ---------------------------------------------------------------- */
  /*  Determine what to show                                           */
  /* ---------------------------------------------------------------- */

  // Use streamed plan if available, otherwise fall back to loaded plan
  const activePlan = stream.plan ?? existingPlan;
  const isComplete =
    stream.status === "complete" || (!!existingPlan && stream.status === "idle");

  // Build phases from stream state OR from existing plan
  const phases = React.useMemo(() => {
    if (Object.keys(stream.phases).length > 0) {
      return stream.phases;
    }

    // Reconstruct phases from existing plan
    if (!existingPlan) return {};

    const PHASE_KEYS: Record<string, string> = {
      P0: "pressure_test",
      P1: "problem_model_fit",
      P2: "architecture",
      P3: "build_buy_train",
      P4: "infrastructure",
      P5: "cost_model",
      "P6.25": "security",
      "P6.5": "observability",
      P7: "scaling",
    };

    const result: Record<string, { status: "complete"; output: unknown; title: string }> = {};
    for (const [displayId, key] of Object.entries(PHASE_KEYS)) {
      const val = (existingPlan as unknown as Record<string, unknown>)[key];
      if (val) {
        result[displayId] = {
          status: "complete",
          output: val,
          title: displayId,
        };
      }
    }
    return result;
  }, [stream.phases, existingPlan]);

  const redTeam = stream.redTeam ?? existingPlan?.red_team ?? null;

  /* ---------------------------------------------------------------- */
  /*  PDF export                                                       */
  /* ---------------------------------------------------------------- */

  function handleExportPdf() {
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/plan/${planId}/export.pdf`;
    window.open(url, "_blank");
  }

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */

  return (
    <section className="flex h-[calc(100vh-var(--header-h,64px)-var(--footer-h,48px))] flex-col">
      {/* Plan History Sidebar */}
      <PlanHistory />
      
      {/* ---- Header bar ---- */}
      <header className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <Badge mono variant="outline">
            plan
          </Badge>
          <span className="font-mono text-xs text-muted-foreground max-w-[200px] truncate">
            {planId}
          </span>
        </div>

        <StatusBadge status={isComplete ? "complete" : stream.status} />

        <div className="ml-auto flex items-center gap-1.5">
          <MetricChip variant="model" icon={<Cpu />} label="model" value="gpt-4o" />
          <MetricChip
            variant="cost"
            icon={<DollarSign />}
            label="spend"
            value={`$${(activePlan?.total_cost_usd ?? stream.costUsd).toFixed(4)}`}
          />
          <MetricChip
            variant="latency"
            icon={<Clock />}
            label="elapsed"
            value={fmtTime(stream.elapsedSec)}
          />

          {isComplete && (
            <>
              <VersionHistory planId={planId as string} />
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportPdf}
                className="ml-2"
              >
                <Download className="h-3.5 w-3.5" />
                PDF
              </Button>
            </>
          )}
        </div>
      </header>

      {/* ---- Split view: Report (left) + Chat (right) ---- */}
      <div className="flex flex-1 overflow-hidden">
        {/* Report panel */}
        <div className="flex-1 overflow-y-auto border-r border-border">
          {loadingExisting && Object.keys(phases).length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mx-auto" />
                <p className="text-sm text-muted-foreground">Loading plan...</p>
              </div>
            </div>
          ) : (
            <ReportPanel
              phases={phases}
              redTeam={redTeam}
              plan={activePlan}
              activePhaseId={stream.activePhaseId}
            activePhaseOrder={stream.activePhaseOrder}
              onEditRequest={handleEditRequest}
            />
          )}
        </div>

        {/* Chat panel */}
        <div className="w-full max-w-md shrink-0 bg-background">
          <ChatPanel
            messages={stream.messages}
            status={stream.status}
            pendingQuestions={stream.pendingQuestions}
            onSubmitAnswers={stream.submitAnswers}
            onSendIteration={stream.startPlan}
            onCancel={stream.cancel}
            editPrompt={editPrompt}
          />
        </div>
      </div>
    </section>
  );
}
