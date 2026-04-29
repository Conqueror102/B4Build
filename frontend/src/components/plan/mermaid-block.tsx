"use client";

import * as React from "react";

/** LLMs often wrap Mermaid in markdown fences despite schema instructions. */
function sanitizeMermaidCode(raw: string): string {
  let s = raw.trim();
  if (s.startsWith("```")) {
    s = s.replace(/^```(?:mermaid)?\s*\n?/i, "").replace(/\n?```\s*$/i, "");
  }
  return s.trim();
}

let mermaidInitialized = false;

export function MermaidBlock({ title, code }: { title: string; code: string }) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    const cleaned = sanitizeMermaidCode(code);

    async function render() {
      if (!containerRef.current) return;
      try {
        const mermaid = (await import("mermaid")).default;
        if (!mermaidInitialized) {
          mermaid.initialize({
            startOnLoad: false,
            securityLevel: "loose",
            theme: "dark",
            themeVariables: {
              primaryColor: "#7c3aed",
              primaryTextColor: "#f5f5f5",
              lineColor: "#6b7280",
              secondaryColor: "#1e1b4b",
              tertiaryColor: "#18181b",
            },
            fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
          });
          mermaidInitialized = true;
        }

        const { svg } = await mermaid.render(
          `m-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          cleaned,
        );
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
        if (!cancelled) setError(false);
      } catch (e) {
        console.error("[MermaidBlock] render failed", title, e);
        if (!cancelled) setError(true);
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [code, title]);

  if (error) {
    const shown = sanitizeMermaidCode(code);
    return (
      <div className="space-y-2">
        <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
          {title} (raw — Mermaid could not parse; check browser console)
        </p>
        <pre className="text-xs text-muted-foreground rounded-lg bg-muted/30 p-3 border border-border/40 overflow-auto whitespace-pre-wrap">
          {shown}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <div
        ref={containerRef}
        className="overflow-auto rounded-lg border border-border/40 bg-muted/20 p-4 [&_svg]:max-w-full"
      />
    </div>
  );
}
