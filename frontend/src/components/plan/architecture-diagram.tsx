"use client";

import * as React from "react";
import type { Architecture, ArchitectureComponent } from "@/lib/types";
import { MermaidBlock } from "./mermaid-block";

const MERMAID_BLOCKS: { key: keyof Pick<
  Architecture,
  | "mermaid_system_architecture"
  | "mermaid_request_data_flow"
  | "mermaid_erd"
  | "mermaid_deployment"
  | "mermaid_ui_component_tree"
>; title: string }[] = [
  { key: "mermaid_system_architecture", title: "System architecture" },
  { key: "mermaid_request_data_flow", title: "Request / data flow" },
  { key: "mermaid_erd", title: "ERD" },
  { key: "mermaid_deployment", title: "Deployment" },
  { key: "mermaid_ui_component_tree", title: "UI component tree" },
];

function mermaidFromComponents(components: ArchitectureComponent[] | undefined): string | null {
  if (!components?.length) return null;
  const lines: string[] = ["flowchart LR"];
  for (let i = 0; i < components.length; i++) {
    const name = String(components[i].name).replace(/["\n]/g, " ");
    lines.push(`  C${i}["${name}"]`);
  }
  for (let i = 0; i < components.length - 1; i++) {
    lines.push(`  C${i} --> C${i + 1}`);
  }
  return lines.join("\n");
}

/**
 * Renders multiple Mermaid diagrams from Phase 2 output.
 * Falls back to a simple flowchart from components (legacy) or a short message.
 */
export function ArchitectureDiagram({ data }: { data: Architecture }) {
  const blocks = MERMAID_BLOCKS.map(({ key, title }) => ({
    title,
    code: data[key] ?? "",
  })).filter((b) => b.code.trim().length > 0);

  if (blocks.length > 0) {
    return (
      <div className="space-y-6">
        {blocks.map((b) => (
          <MermaidBlock key={b.title} title={b.title} code={b.code} />
        ))}
      </div>
    );
  }

  const fallback = mermaidFromComponents(
    (data as unknown as { components?: ArchitectureComponent[] }).components,
  );
  if (fallback) {
    return (
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground">
          Mermaid was not included in this saved plan; showing a simple component view.
        </p>
        <MermaidBlock title="Components (inferred)" code={fallback} />
      </div>
    );
  }

  return (
    <p className="text-sm text-muted-foreground">
      No architecture diagrams for this plan.
    </p>
  );
}
