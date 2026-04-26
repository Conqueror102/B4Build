import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Calculator,
  ShieldHalf,
  Sparkles,
  MessageSquareText,
  ListChecks,
  Workflow,
  GitBranch,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GradientHeading } from "@/components/brand/gradient-heading";
import { GridBg } from "@/components/brand/grid-bg";
import { MetricChip } from "@/components/brand/metric-chip";

const FEATURES = [
  {
    icon: Brain,
    title: "Decision-tree reasoning",
    body: "Forces the right questions in the right order. No skipping the boring phases. Your idea gets pressure-tested before it gets architected.",
    accent: "oklch(0.6 0.22 295)",
  },
  {
    icon: ShieldHalf,
    title: "Adversarial red team",
    body: "A second model tries to break your plan before you ship — looking for missing failure modes, naive cost assumptions, and silent security gaps.",
    accent: "oklch(0.65 0.22 25)",
  },
  {
    icon: Calculator,
    title: "Deterministic cost model",
    body: "Real Python math, not LLM guesses, for what your app costs at 100, 1k, and 10k users. With a self-host break-even line.",
    accent: "oklch(0.7 0.18 150)",
  },
];

const STEPS = [
  {
    n: "01",
    icon: MessageSquareText,
    title: "Describe your idea",
    body: "A few sentences. Audience, budget, expected scale if you know it.",
  },
  {
    n: "02",
    icon: ListChecks,
    title: "Answer 3 clarifying questions",
    body: "The advisor asks only what it actually needs to make the next decision.",
  },
  {
    n: "03",
    icon: Workflow,
    title: "Get a 9-phase plan",
    body: "Architecture, build vs buy, infrastructure, cost projections, security, scaling.",
  },
  {
    n: "04",
    icon: GitBranch,
    title: "Iterate on constraints",
    body: "What if I use Claude? What if my budget is $500? Re-runs only what changed.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* ────────────── HERO ────────────── */}
      <section className="relative isolate overflow-hidden">
        <GridBg />
        <div className="relative mx-auto flex max-w-6xl flex-col items-center px-4 pb-20 pt-24 sm:px-6 sm:pt-32 lg:pt-36">
          <Badge
            mono
            variant="outline"
            className="animate-in-fade border-white/12 bg-background/40 backdrop-blur"
          >
            <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full gradient-bg" />
            v0.1 · in development
          </Badge>

          <GradientHeading
            as="h1"
            className="mt-6 max-w-4xl text-center animate-in-up delay-100"
            highlight="one decision at a time."
          >
            From idea to production,
          </GradientHeading>

          <p className="animate-in-up delay-200 mt-7 max-w-2xl text-center text-lg leading-relaxed text-muted-foreground sm:text-xl">
            A conversational advisor that walks you through the{" "}
            <span className="text-foreground/90">9 phases</span> of building an AI app —
            pressure-test, architecture, build vs buy, cost, security, scaling — grounded in
            your specific constraints, with a red team trying to break it.
          </p>

          <div className="animate-in-up delay-300 mt-10 flex flex-wrap items-center justify-center gap-3">
            <Button asChild variant="gradient" size="lg" className="group">
              <Link href="/plan/new">
                Start a plan
                <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
              </Link>
            </Button>
            <Button asChild variant="ghost" size="lg">
              <Link href="/sample">See sample plan</Link>
            </Button>
          </div>

          <div className="animate-in-up delay-400 mt-10 flex flex-wrap items-center justify-center gap-1.5 text-foreground/70">
            <MetricChip>9 phases</MetricChip>
            <MetricChip variant="model">5 LangGraph nodes</MetricChip>
            <MetricChip variant="warning">Red team built-in</MetricChip>
            <MetricChip variant="cost">Open source</MetricChip>
          </div>

          <div className="animate-in-up delay-500 mt-16 w-full max-w-5xl">
            <div className="relative aspect-video overflow-hidden rounded-2xl border border-border/60 bg-muted/30 shadow-2xl">
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-muted-foreground">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-background border border-border/50 shadow-sm">
                  <Sparkles className="h-6 w-6 text-primary" />
                </div>
                <p className="font-mono text-sm uppercase tracking-wider">Demo Video Placeholder</p>
                <p className="text-sm max-w-sm text-center">Replace this div with an `&lt;iframe&gt;` embedding a YouTube/Vimeo video, or a looping `.mp4` showcase.</p>
              </div>
            </div>
          </div>
        </div>

        {/* hairline divider with gradient nub */}
        <div className="relative mx-auto h-px max-w-6xl">
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
          <div className="absolute left-1/2 top-0 h-px w-24 -translate-x-1/2 gradient-bg opacity-80" />
        </div>
      </section>

      {/* ────────────── FEATURES ────────────── */}
      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <Sparkles className="mr-1.5 inline h-3 w-3" />
            What makes it different
          </p>
          <GradientHeading as="h2" className="mt-3">
            Not another chatbot wrapper.
          </GradientHeading>
        </div>

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <Card
                key={f.title}
                className="group relative overflow-hidden transition-transform duration-300 hover:-translate-y-1 hover:border-white/15"
              >
                {/* corner glow */}
                <div
                  aria-hidden
                  className="pointer-events-none absolute -right-20 -top-20 h-40 w-40 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-30"
                  style={{ background: f.accent }}
                />
                <CardHeader className="gap-4">
                  <div
                    className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-border/80 bg-muted/40"
                    style={{
                      boxShadow: `inset 0 0 0 1px ${f.accent}22, 0 6px 20px -6px ${f.accent}30`,
                    }}
                  >
                    <Icon className="h-5 w-5" style={{ color: f.accent }} />
                  </div>
                  <CardTitle className="text-[17px]">{f.title}</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm leading-relaxed text-muted-foreground">{f.body}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ────────────── HOW IT WORKS ────────────── */}
      <section className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            How it works
          </p>
          <GradientHeading as="h2" className="mt-3">
            Four steps. Then iterate.
          </GradientHeading>
        </div>

        <div className="relative mt-16">
          {/* connecting line at md+ */}
          <div
            aria-hidden
            className="absolute left-0 right-0 top-[44px] hidden h-px md:block"
            style={{
              background:
                "linear-gradient(to right, transparent 4%, oklch(0.22 0.005 270) 12%, oklch(0.22 0.005 270) 88%, transparent 96%)",
            }}
          />
          <ol className="relative grid gap-8 md:grid-cols-4">
            {STEPS.map((s) => {
              const Icon = s.icon;
              return (
                <li key={s.n} className="relative flex flex-col items-start">
                  <div className="relative mb-5">
                    <div
                      aria-hidden
                      className="absolute inset-0 rounded-2xl gradient-bg opacity-15 blur-xl"
                    />
                    <div className="relative flex h-[88px] w-[88px] items-center justify-center rounded-2xl border border-border bg-card">
                      <Icon className="h-7 w-7 text-foreground/85" />
                      <span className="absolute -right-2 -top-2 inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-border bg-background px-1.5 font-mono text-[11px] tracking-wider text-foreground/85">
                        {s.n}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-[15px] font-semibold tracking-tight text-foreground">
                    {s.title}
                  </h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                    {s.body}
                  </p>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      {/* ────────────── BOTTOM CTA ────────────── */}
      <section className="relative mx-auto mb-12 max-w-6xl px-4 sm:px-6">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-card/60 p-10 sm:p-16">
          <div
            aria-hidden
            className="absolute -inset-px rounded-3xl"
            style={{
              background:
                "radial-gradient(60% 100% at 50% 0%, oklch(0.55 0.22 295 / 0.18), transparent 70%), radial-gradient(60% 100% at 100% 100%, oklch(0.55 0.25 340 / 0.14), transparent 70%)",
            }}
          />
          <div className="relative flex flex-col items-center text-center">
            <GradientHeading as="h2" className="max-w-2xl" highlight="your idea?">
              Ready to pressure-test
            </GradientHeading>
            <p className="mt-4 max-w-xl text-muted-foreground">
              The advisor asks the questions you&rsquo;d otherwise figure out the hard way &mdash; at 2 AM, in
              prod, on a Saturday.
            </p>
            <Button asChild variant="gradient" size="lg" className="mt-8 group">
              <Link href="/plan/new">
                Start a plan
                <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}
