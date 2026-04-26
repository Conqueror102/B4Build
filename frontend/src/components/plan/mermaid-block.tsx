"use client";

import * as React from "react";

export function MermaidBlock({ title, code }: { title: string; code: string }) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState(false);

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
            secondaryColor: "#1e1b4b",
            tertiaryColor: "#18181b",
          },
          fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
        });

        const { svg } = await mermaid.render(`m-${Date.now()}-${title.slice(0, 8)}`, code);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
        if (!cancelled) setError(false);
      } catch {
        if (!cancelled) setError(true);
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [code, title]);

  if (error) {
    return (
      <div className="space-y-2">
        <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
          {title} (raw)
        </p>
        <pre className="text-xs text-muted-foreground rounded-lg bg-muted/30 p-3 border border-border/40 overflow-auto whitespace-pre-wrap">
          {code}
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
