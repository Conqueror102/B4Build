"use client";

import * as React from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { FullPlan } from "@/lib/types";

export function SynthesisPanel({ plan }: { plan: FullPlan }) {
  return (
    <div className="space-y-6 animate-in-fade">
      <div className="flex items-center gap-2">
        <Badge variant="gradient">
          <Sparkles className="h-3 w-3" />
          Synthesis
        </Badge>
      </div>

      {/* Executive summary */}
      <div className="space-y-1.5">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          Executive summary
        </h4>
        <p className="text-sm leading-relaxed text-foreground/90">
          {plan.executive_summary}
        </p>
      </div>

      {/* Next steps */}
      <div className="space-y-2">
        <h4 className="text-[11px] font-mono uppercase tracking-[0.14em] text-muted-foreground">
          Recommended next steps
        </h4>
        <ol className="space-y-2">
          {plan.next_steps.map((step, i) => (
            <li
              key={i}
              className="flex gap-3 text-sm leading-relaxed text-foreground/85"
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full gradient-bg text-[10px] font-bold text-white mt-0.5">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Cost */}
      <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">
          Total generation cost:
        </span>
        <span className="font-mono text-sm text-[oklch(0.85_0.18_150)]">
          ${plan.total_cost_usd.toFixed(4)}
        </span>
      </div>
    </div>
  );
}
