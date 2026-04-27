"use client";

import * as React from "react";
import { streamChat } from "@/lib/api";
import type {
  ChatRequest,
  FullPlan,
  RedTeamCritique,
  SseEvent,
} from "@/lib/types";
import type { PhaseStatus } from "@/components/brand/phase-card";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface ClarifyingQuestion {
  id: string;
  text: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

export type StreamStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "clarifying"
  | "complete"
  | "error";

export interface PhaseState {
  status: PhaseStatus;
  output: unknown | null;
  title: string;
}

export interface PlanStreamState {
  /** Unique plan id (from backend "init" event) */
  planId: string | null;
  /** Active phase ids for this run (display ids like "P2") */
  activePhaseOrder: string[] | null;
  /** Current stream status */
  status: StreamStatus;
  /** Accumulated chat messages */
  messages: ChatMessage[];
  /** Status + output per phase id (e.g. "phase_0", "phase_1") */
  phases: Record<string, PhaseState>;
  /** Clarifying questions waiting for answers */
  pendingQuestions: ClarifyingQuestion[];
  /** Red team critique once available */
  redTeam: RedTeamCritique | null;
  /** Final synthesized plan */
  plan: FullPlan | null;
  /** Diffs generated during an iteration */
  diff: unknown[] | null;
  /** Error message if any */
  error: string | null;
  /** Running cost (updated per phase_complete event) */
  costUsd: number;
  /** Elapsed time in seconds since stream started */
  elapsedSec: number;
  /** Which phase is currently running */
  activePhaseId: string | null;
}

/* ------------------------------------------------------------------ */
/*  Phase-id normalization                                             */
/* ------------------------------------------------------------------ */

/** Map backend phase ids (phase_0, phase_6_25) → display ids (P0, P6.25) */
const PHASE_MAP: Record<string, string> = {
  phase_0: "P0",
  phase_1: "P1",
  phase_2: "P2",
  phase_3: "P3",
  phase_4: "P4",
  phase_5: "P5",
  phase_6_25: "P6.25",
  "phase_6.25": "P6.25",
  phase_6_5: "P6.5",
  "phase_6.5": "P6.5",
  phase_7: "P7",
};

function normalizePhaseId(raw: string | undefined | null): string {
  if (!raw) return "";
  return PHASE_MAP[raw] ?? raw;
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function usePlanStream(initialPlanId?: string | null) {
  const [state, setState] = React.useState<PlanStreamState>({
    planId: initialPlanId ?? null,
    activePhaseOrder: null,
    status: "idle",
    messages: [],
    phases: {},
    pendingQuestions: [],
    redTeam: null,
    plan: null,
    diff: null,
    error: null,
    costUsd: 0,
    elapsedSec: 0,
    activePhaseId: null,
  });

  const abortRef = React.useRef<AbortController | null>(null);
  const timerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = React.useRef<number>(0);

  /* Clean up on unmount */
  React.useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  /** Start the elapsed-seconds timer */
  const startTimer = React.useCallback(() => {
    startTimeRef.current = Date.now();
    timerRef.current = setInterval(() => {
      setState((prev) => ({
        ...prev,
        elapsedSec: Math.round((Date.now() - startTimeRef.current) / 1000),
      }));
    }, 1000);
  }, []);

  const stopTimer = React.useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  /** Send a new idea to the backend */
  const startPlan = React.useCallback(
    async (idea: string, opts?: { activePhaseOrder?: string[] | null }) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState((prev) => ({
        ...prev,
        status: "connecting",
        error: null,
        diff: null,
        messages: [
          ...prev.messages,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: idea,
            timestamp: Date.now(),
          },
        ],
      }));

      startTimer();

      const body: ChatRequest = {
        idea,
        plan_id: state.planId,
        active_phase_order: opts?.activePhaseOrder ?? undefined,
      };

      try {
        for await (const event of streamChat(body, {
          signal: controller.signal,
        })) {
          if (controller.signal.aborted) break;
          handleEvent(event);
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: (err as Error).message ?? "Stream failed",
          }));
        }
      } finally {
        stopTimer();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [state.planId],
  );

  /** Submit answers to clarifying questions */
  const submitAnswers = React.useCallback(
    async (answers: Record<string, string>) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const idea =
        state.messages.find((m) => m.role === "user")?.content ?? "";

      setState((prev) => ({
        ...prev,
        status: "connecting",
        pendingQuestions: [],
        error: null,
        messages: [
          ...prev.messages,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: Object.values(answers).join("\n"),
            timestamp: Date.now(),
          },
        ],
      }));

      startTimer();

      const body: ChatRequest = {
        idea,
        clarifying_answers: answers,
        plan_id: state.planId,
      };

      try {
        for await (const event of streamChat(body, {
          signal: controller.signal,
        })) {
          if (controller.signal.aborted) break;
          handleEvent(event);
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: (err as Error).message ?? "Stream failed",
          }));
        }
      } finally {
        stopTimer();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [state.planId, state.messages],
  );

  /** Cancel the current stream */
  const cancel = React.useCallback(() => {
    abortRef.current?.abort();
    stopTimer();
    setState((prev) => ({ ...prev, status: "idle" }));
  }, [stopTimer]);

  /** Load messages from conversation history */
  const loadMessages = React.useCallback((messages: ChatMessage[], isComplete = false) => {
    setState((prev) => ({
      ...prev,
      messages: messages,
      status: isComplete ? "complete" : prev.status,
    }));
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Event handlers                                                   */
  /* ---------------------------------------------------------------- */

  function handleEvent(event: SseEvent) {
    switch (event.event) {
      case "init":
        setState((prev) => ({
          ...prev,
          planId: event.data.plan_id,
          activePhaseOrder: Array.isArray(event.data.active_phase_order)
            ? event.data.active_phase_order.map((p) => normalizePhaseId(p))
            : prev.activePhaseOrder,
          status: "streaming",
        }));
        break;

      case "phase_start": {
        // phase_id is on the SSE root (see api chat._sse), not in data
        const pid = normalizePhaseId(event.phase_id);
        if (!pid) break;
        setState((prev) => ({
          ...prev,
          activePhaseId: pid,
          phases: {
            ...prev.phases,
            [pid]: {
              status: "running",
              output: null,
              title: event.data.title ?? pid,
            },
          },
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `Running ${event.data.title ?? pid}...`,
              timestamp: Date.now(),
            },
          ],
        }));
        break;
      }

      case "phase_complete": {
        const pid = normalizePhaseId(event.phase_id);
        if (!pid) break;
        setState((prev) => ({
          ...prev,
          activePhaseId: null,
          phases: {
            ...prev.phases,
            [pid]: {
              status: "complete",
              output: event.data.output ?? null,
              title:
                event.data.title ??
                prev.phases[pid]?.title ??
                pid,
            },
          },
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `${event.data.title ?? pid} complete.`,
              timestamp: Date.now(),
            },
          ],
        }));
        break;
      }

      case "clarify":
        setState((prev) => {
          const raw = (event.data as { questions?: unknown }).questions;
          const arr = Array.isArray(raw) ? raw : [];
          const mapped = arr
            .map((q) => {
              const o = q as { id?: string; key?: string; text?: string; question?: string };
              return {
                id: String(o.id ?? o.key ?? ""),
                text: String(o.text ?? o.question ?? ""),
              };
            })
            .filter((q) => q.id && q.text);
          return {
            ...prev,
            status: "clarifying",
            pendingQuestions: mapped,
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content:
                "I have a few clarifying questions before I can generate your plan:",
              timestamp: Date.now(),
            },
          ],
          };
        });
        break;

      case "red_team":
        setState((prev) => ({
          ...prev,
          redTeam:
            (event.data.critique as RedTeamCritique) ?? null,
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: "Red team critique complete.",
              timestamp: Date.now(),
            },
          ],
        }));
        break;

      case "synthesizer":
        setState((prev) => ({
          ...prev,
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: "Synthesizing your final plan...",
              timestamp: Date.now(),
            },
          ],
        }));
        break;

      case "done":
        setState((prev) => ({
          ...prev,
          status: "complete",
          plan: (event.data.plan as FullPlan) ?? prev.plan,
          planId:
            (event.data as Record<string, unknown>).plan_id as string ??
            prev.planId,
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content:
                "Your plan is ready! Browse the phases in the report panel.",
              timestamp: Date.now(),
            },
          ],
        }));
        break;

      case "diff":
        setState((prev) => {
          const d = event.data as { diff?: unknown[] };
          const diffArray = d.diff;
          if (!Array.isArray(diffArray) || diffArray.length === 0) return prev;

          // Format diffs for chat display
          const summary = diffArray
            .map((item) => {
              const row = item as { op?: string; path: string };
              const op = row.op === "add" ? "Added" : row.op === "remove" ? "Removed" : "Updated";
              const path = String(row.path ?? "")
                .replace(/\//g, " → ")
                .replace(/^ → /, "");
              return `• ${op}: ${path}`;
            })
            .join("\n");

          return {
            ...prev,
            diff: diffArray,
            messages: [
              ...prev.messages,
              {
                id: crypto.randomUUID(),
                role: "system",
                content: `Applied changes:\n${summary}`,
                timestamp: Date.now(),
              },
            ],
          };
        });
        break;

      case "chat_reply":
        setState((prev) => ({
          ...prev,
          status: "complete",
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: String(
                (event.data as { message?: unknown }).message ?? ""
              ),
              timestamp: Date.now(),
            },
          ],
        }));
        break;

      case "error":
        setState((prev) => ({
          ...prev,
          status: "error",
          error: event.data.message ?? "Unknown error",
          messages: [
            ...prev.messages,
            {
              id: crypto.randomUUID(),
              role: "system",
              content: `Error: ${event.data.message}`,
              timestamp: Date.now(),
            },
          ],
        }));
        break;
    }
  }

  return {
    ...state,
    startPlan,
    submitAnswers,
    cancel,
    loadMessages,
  };
}
