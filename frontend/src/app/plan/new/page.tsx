"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { GradientHeading } from "@/components/brand/gradient-heading";
import { PhaseCard } from "@/components/brand/phase-card";
import { Badge } from "@/components/ui/badge";
import { PLAN_PHASES } from "@/lib/types";
import { cn } from "@/lib/utils";
import { streamChat } from "@/lib/api";

const SAMPLE_IDEA =
  "An AI tool that summarizes legal contracts for non-lawyers. It should highlight risky clauses (auto-renewal, indemnity, exclusivity) and explain them in plain English. Target: small business owners signing SaaS / vendor agreements. Budget: $500/month. Expecting ~1k users in the first quarter.";

const MIN_LEN = 20;
const MAX_LEN = 2000;

export default function NewPlanPage() {
  const router = useRouter();
  const [idea, setIdea] = React.useState("");
  const [template, setTemplate] = React.useState<"full" | "mvp">("full");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const ready = idea.trim().length >= MIN_LEN && !submitting;
  const remaining = MAX_LEN - idea.length;

  const activePhaseOrder = React.useMemo(() => {
    if (template === "full") return PLAN_PHASES.map((p) => p.id);
    // MVP: skip observability + scaling by default.
    return PLAN_PHASES.filter((p) => !["P6.5", "P7"].includes(p.id)).map((p) => p.id);
  }, [template]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ready) return;

    setSubmitting(true);
    setError(null);

    try {
      // Fire the first SSE call just to get the plan_id from the "init" event,
      // then redirect. The /plan/[id] page will handle the full stream.
      const controller = new AbortController();

      for await (const event of streamChat(
        { idea: idea.trim(), active_phase_order: activePhaseOrder },
        { signal: controller.signal },
      )) {
        if (event.event === "init" && event.data.plan_id) {
          // We got our plan_id — abort this stream and redirect.
          // The plan page will re-stream from scratch or pick up state.
          controller.abort();
          const encoded = encodeURIComponent(idea.trim());
          router.replace(`/plan/${event.data.plan_id}?idea=${encoded}`);
          return;
        }

        // If clarifying questions come before init, handle edge case
        if (event.event === "clarify") {
          // Redirect with idea in search params so plan page can pick it up
          const encoded = encodeURIComponent(idea.trim());
          router.push(`/plan/new-stream?idea=${encoded}`);
          controller.abort();
          return;
        }

        if (event.event === "error") {
          setError(event.data.message ?? "Failed to start plan");
          setSubmitting(false);
          controller.abort();
          return;
        }
      }

      // If we got here without init, something went wrong
      setError("No plan ID received from server. Is the backend running?");
      setSubmitting(false);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message ?? "Network error");
        setSubmitting(false);
      }
    }
  }

  return (
    <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
      <div className="flex flex-col items-start gap-3 animate-in-fade">
        <Badge mono variant="outline">
          <Sparkles className="h-3 w-3" />
          New plan
        </Badge>
        <GradientHeading as="h1">What are you building?</GradientHeading>
        <p className="max-w-2xl text-muted-foreground">
          Describe your idea in 2-3 sentences. The advisor will ask up to{" "}
          <span className="text-foreground/90">3 clarifying questions</span> before generating the
          plan — audience, constraints, scale.
        </p>
      </div>

      <form className="mt-10 animate-in-up" onSubmit={handleSubmit}>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant={template === "full" ? "secondary" : "ghost"}
            size="sm"
            disabled={submitting}
            onClick={() => setTemplate("full")}
          >
            Full (9 phases)
          </Button>
          <Button
            type="button"
            variant={template === "mvp" ? "secondary" : "ghost"}
            size="sm"
            disabled={submitting}
            onClick={() => setTemplate("mvp")}
          >
            MVP ({activePhaseOrder.length} phases)
          </Button>
          <span className="text-xs text-muted-foreground">
            You can change this later by regenerating selected phases.
          </span>
        </div>
        <div className="flex items-baseline justify-between pb-2">
          <Label htmlFor="idea">Your idea</Label>
          <span
            className={cn(
              "font-mono text-[11px] tracking-wider",
              remaining < 0
                ? "text-[oklch(0.78_0.2_25)]"
                : remaining < 200
                  ? "text-[oklch(0.85_0.16_75)]"
                  : "text-muted-foreground/80",
            )}
          >
            {idea.length} / {MAX_LEN}
          </span>
        </div>

        <div className="relative">
          <Textarea
            id="idea"
            mono
            rows={7}
            maxLength={MAX_LEN}
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder={SAMPLE_IDEA}
            className="min-h-[180px] pr-3 leading-relaxed"
            disabled={submitting}
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 -z-10 rounded-md gradient-bg opacity-0 blur-md transition-opacity duration-300 [textarea:focus-visible+&]:opacity-30"
          />
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-[oklch(0.55_0.22_25/0.4)] bg-[oklch(0.5_0.22_25/0.1)] px-4 py-2.5 text-sm text-[oklch(0.85_0.18_25)]">
            {error}
          </div>
        )}

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Button
            type="submit"
            variant="gradient"
            size="lg"
            disabled={!ready}
            className="group"
          >
            {submitting ? (
              <>
                <Loader2 className="animate-spin" />
                Starting...
              </>
            ) : (
              <>
                Generate plan
                <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="lg"
            onClick={() => setIdea(SAMPLE_IDEA)}
            disabled={submitting}
          >
            Try a sample idea
          </Button>
          {!ready && idea.length > 0 && !submitting && (
            <span className="text-xs text-muted-foreground">
              {MIN_LEN - idea.trim().length} more characters before we can run.
            </span>
          )}
        </div>
      </form>

      {/* ---- what you'll get ---- */}
      <div className="mt-20">
        <div className="mb-5 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold tracking-tight text-foreground">
            What you&rsquo;ll get
          </h2>
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            {activePhaseOrder.length} phases
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {PLAN_PHASES.filter((p) => activePhaseOrder.includes(p.id)).map((p) => (
            <PhaseCard
              key={p.id}
              phaseId={p.id}
              title={p.title}
              description={p.blurb}
              status="pending"
            />
          ))}
        </div>

        <p className="mt-8 text-xs text-muted-foreground">
          Want to see what the output looks like first?{" "}
          <Link
            href="/sample"
            className="text-foreground/85 underline-offset-4 hover:underline"
          >
            View a sample plan &rarr;
          </Link>
        </p>
      </div>
    </section>
  );
}
