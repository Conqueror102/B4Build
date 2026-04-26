"use client";

import * as React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CostModel } from "@/lib/types";

const COLORS = [
  "oklch(0.7 0.2 295)",   // violet
  "oklch(0.7 0.25 340)",  // fuchsia
  "oklch(0.78 0.18 150)", // green
  "oklch(0.85 0.16 75)",  // amber
  "oklch(0.78 0.16 230)", // blue
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      label: string;
      monthly_cost_usd: number;
      monthly_requests: number;
      notes: string | null;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-lg">
      <p className="text-sm font-medium text-foreground">{d.label}</p>
      <p className="text-xs text-muted-foreground mt-1">
        {d.monthly_requests.toLocaleString()} requests/mo
      </p>
      <p className="text-sm font-mono mt-1" style={{ color: "oklch(0.85 0.18 150)" }}>
        ${d.monthly_cost_usd.toFixed(2)}/mo
      </p>
      {d.notes && (
        <p className="text-xs text-muted-foreground mt-1">{d.notes}</p>
      )}
    </div>
  );
}

export function CostChart({ data }: { data: CostModel }) {
  if (!data.scenarios || data.scenarios.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No cost scenarios available.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        Monthly cost by scenario
      </p>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data.scenarios}
            margin={{ top: 8, right: 8, left: 0, bottom: 8 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="oklch(1 0 0 / 6%)"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "oklch(0.7 0 0)" }}
              axisLine={{ stroke: "oklch(1 0 0 / 10%)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "oklch(0.7 0 0)" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `$${v}`}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "oklch(1 0 0 / 4%)" }}
            />
            <Bar dataKey="monthly_cost_usd" radius={[4, 4, 0, 0]}>
              {data.scenarios.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
