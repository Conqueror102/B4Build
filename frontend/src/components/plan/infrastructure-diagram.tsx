"use client";

import type { Infrastructure } from "@/lib/types";
import { MermaidBlock } from "./mermaid-block";

const MERMAID_INFRA: {
  key: "mermaid_mvp_stack" | "mermaid_production_stack" | "mermaid_mvp_to_production";
  title: string;
}[] = [
  { key: "mermaid_mvp_stack", title: "MVP stack" },
  { key: "mermaid_production_stack", title: "Production stack" },
  { key: "mermaid_mvp_to_production", title: "MVP → production" },
];

export function InfrastructureDiagram({ data }: { data: Infrastructure }) {
  const d = data as Record<string, string | undefined>;
  const blocks = MERMAID_INFRA.map(({ key, title }) => ({
    key,
    title,
    code: d[key] ?? "",
  })).filter((b) => b.code.trim().length > 0);

  if (blocks.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No infrastructure diagrams in this plan (older plan format).
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {blocks.map((b) => (
        <MermaidBlock key={b.key} title={b.title} code={b.code} />
      ))}
    </div>
  );
}
