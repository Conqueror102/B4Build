"use client";

import * as React from "react";
import { ShieldAlert, AlertTriangle, Info, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { RedTeamCritique, RedTeamFinding } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Severity helpers                                                   */
/* ------------------------------------------------------------------ */

const SEVERITY_CONFIG: Record<
  string,
  {
    variant: "destructive" | "warning" | "info" | "default";
    icon: React.ReactNode;
    order: number;
  }
> = {
  critical: {
    variant: "destructive",
    icon: <AlertCircle className="h-3 w-3" />,
    order: 0,
  },
  high: {
    variant: "destructive",
    icon: <AlertTriangle className="h-3 w-3" />,
    order: 1,
  },
  medium: {
    variant: "warning",
    icon: <AlertTriangle className="h-3 w-3" />,
    order: 2,
  },
  low: {
    variant: "info",
    icon: <Info className="h-3 w-3" />,
    order: 3,
  },
};

function getSeverityConfig(severity: string) {
  return (
    SEVERITY_CONFIG[severity.toLowerCase()] ?? {
      variant: "default" as const,
      icon: <Info className="h-3 w-3" />,
      order: 4,
    }
  );
}

/* ------------------------------------------------------------------ */
/*  Finding card                                                       */
/* ------------------------------------------------------------------ */

function FindingCard({ finding }: { finding: RedTeamFinding }) {
  const config = getSeverityConfig(finding.severity);
  return (
    <Card className="bg-card/50">
      <CardHeader className="gap-2 pb-1">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={config.variant}>
            {config.icon}
            {finding.severity}
          </Badge>
          <Badge variant="outline" mono className="text-[10px]">
            {finding.phase_id}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm leading-relaxed text-foreground/90">
          {finding.concern}
        </p>
        <div className="rounded-lg bg-muted/30 border border-border/40 p-2.5">
          <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
            Suggested mitigation
          </p>
          <p className="text-sm text-foreground/80">
            {finding.suggested_mitigation}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Main panel                                                         */
/* ------------------------------------------------------------------ */

export function RedTeamPanel({ critique }: { critique: RedTeamCritique }) {
  // Sort findings by severity (critical first)
  const sorted = React.useMemo(
    () =>
      [...critique.findings].sort(
        (a, b) =>
          getSeverityConfig(a.severity).order -
          getSeverityConfig(b.severity).order,
      ),
    [critique.findings],
  );

  const confidenceVariant =
    critique.overall_confidence === "high"
      ? "success"
      : critique.overall_confidence === "medium"
        ? "warning"
        : "destructive";

  return (
    <div className="space-y-5 animate-in-fade">
      {/* Header metrics */}
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant="destructive">
          <ShieldAlert className="h-3 w-3" />
          Red Team
        </Badge>
        <Badge variant={confidenceVariant as "success" | "warning" | "destructive"}>
          Confidence: {critique.overall_confidence}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {critique.findings.length} finding{critique.findings.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm leading-relaxed text-foreground/85">
        {critique.summary}
      </p>

      {/* Findings */}
      <div className="space-y-3">
        {sorted.map((finding, i) => (
          <FindingCard key={i} finding={finding} />
        ))}
      </div>
    </div>
  );
}
