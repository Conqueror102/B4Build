"use client";

import * as React from "react";
import { GradientHeading } from "@/components/brand/gradient-heading";

export default function HowItWorksPage() {
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    let cancelled = false;
    async function render() {
      if (!containerRef.current) return;
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#7c3aed",
            primaryTextColor: "#f5f5f5",
            lineColor: "#6b7280",
          },
          fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
        });

        const code = `
flowchart TD
    User([User Idea]) --> Coordinator
    
    subgraph Agentic Loop
        Coordinator{Coordinator Node}
        PhaseWorker[Phase Worker LLM]
        RedTeam[Red Team Critique]
        
        Coordinator -- Needs clarification --> User
        Coordinator -- Clean phase --> PhaseWorker
        Coordinator -- 9 phases done --> RedTeam
        PhaseWorker -- Output --> Coordinator
    end
    
    RedTeam --> Synthesizer[Final Synthesizer]
    Synthesizer --> Report([Comprehensive PDF])
        `;
        
        const { svg } = await mermaid.render("how-it-works-diagram", code);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (e) {
        console.error(e);
      }
    }
    render();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-24 sm:px-6 lg:px-8">
      <GradientHeading as="h1" className="text-center mb-16">
        The Architecture Behind the Advisor
      </GradientHeading>

      <div className="mb-16 rounded-xl border border-border/40 bg-muted/20 p-8 shadow-2xl">
        <h2 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4 text-center">LangGraph Node Execution Flow</h2>
        <div ref={containerRef} className="flex justify-center [&_svg]:max-w-full" />
      </div>

      <div className="grid gap-12 md:grid-cols-2">
        <div>
          <h3 className="text-xl font-semibold mb-3">1. The Intake Node</h3>
          <p className="text-muted-foreground leading-relaxed">
            The process starts when you submit a rough idea. Before doing any architecture
            work, the Intake Node evaluates if your idea is clear enough to proceed. If
            it&apos;s too vague, it halts execution and asks you exactly 3 clarifying
            questions.
          </p>
        </div>

        <div>
          <h3 className="text-xl font-semibold mb-3">2. The Coordinator</h3>
          <p className="text-muted-foreground leading-relaxed">
            The brain of the operation. The Coordinator maintains the state of the 9-phase plan. It deterministically routes execution to the Phase Worker, ensuring phase dependencies are met (e.g., Phase 5 Cost Modeling cannot run until Phase 4 Infrastructure is complete).
          </p>
        </div>

        <div>
          <h3 className="text-xl font-semibold mb-3">3. The Phase Worker</h3>
          <p className="text-muted-foreground leading-relaxed">
            A specialized prompt template executed by a frontier model (like GPT-4o or Claude 3.5 Sonnet). It is strictly constrained by JSON schema to output specific schemas (like architecture diagrams or array matrices) rather than generic chat text.
          </p>
        </div>

        <div>
          <h3 className="text-xl font-semibold mb-3">4. The Adversarial Red Team</h3>
          <p className="text-muted-foreground leading-relaxed">
            Once all 9 phases are drafted, the Coordinator hands the entire state to a separate Red Team agent. Its system prompt demands skepticism. It looks for naive assumptions, unhandled scale limitations, and security flaws, generating a critique report.
          </p>
        </div>
      </div>
    </div>
  );
}
