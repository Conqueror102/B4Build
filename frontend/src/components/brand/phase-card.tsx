import * as React from "react";
import { AlertCircle, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type PhaseStatus = "pending" | "running" | "complete" | "error";

export interface PhaseCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** e.g. "P0", "P6.25" */
  phaseId: string;
  title: string;
  description?: string;
  status?: PhaseStatus;
  /** Inline metric chips (rendered after the title row). */
  metrics?: React.ReactNode;
  onEditRequest?: () => void;
  children?: React.ReactNode;
}

const STATUS_LABEL: Record<PhaseStatus, string> = {
  pending: "Pending",
  running: "Running",
  complete: "Complete",
  error: "Error",
};

function StatusIcon({ status }: { status: PhaseStatus }) {
  switch (status) {
    case "complete":
      return <CheckCircle2 className="h-4 w-4 text-[oklch(0.78_0.18_150)]" />;
    case "running":
      return (
        <Loader2 className="h-4 w-4 animate-spin text-[oklch(0.78_0.16_230)]" />
      );
    case "error":
      return <AlertCircle className="h-4 w-4 text-[oklch(0.78_0.2_25)]" />;
    case "pending":
    default:
      return <Circle className="h-4 w-4 text-muted-foreground/60" />;
  }
}

export function PhaseCard({
  phaseId,
  title,
  description,
  status = "pending",
  metrics,
  onEditRequest,
  className,
  children,
  ...props
}: PhaseCardProps) {
  const isComplete = status === "complete";
  return (
    <Card
      className={cn(
        "group relative overflow-hidden",
        "transition-[transform,border-color,box-shadow] duration-300",
        "hover:-translate-y-0.5",
        isComplete && "hover:border-[oklch(0.55_0.18_295/0.45)]",
        className,
      )}
      {...props}
    >
      {/* hairline gradient on top edge for completed phases */}
      {isComplete && (
        <div
          aria-hidden
          className="absolute inset-x-0 top-0 h-px gradient-bg opacity-70"
        />
      )}
      <CardHeader className="gap-3">
        <div className="flex items-center gap-2.5">
          <Badge
            mono
            variant={isComplete ? "gradient" : "outline"}
            className="h-5 px-1.5 leading-none"
          >
            {phaseId}
          </Badge>
          <h3 className="text-[15px] font-semibold tracking-tight text-foreground flex items-center gap-2">
            {title}
            {isComplete && onEditRequest && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEditRequest();
                }}
                className="inline-flex items-center gap-1 text-[10px] uppercase font-mono tracking-wider text-muted-foreground hover:text-primary transition-colors bg-muted/50 hover:bg-muted px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100"
                title={`Request edit for ${title}`}
              >
                Edit
              </button>
            )}
          </h3>
          <span className="ml-auto inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
            <StatusIcon status={status} />
            {STATUS_LABEL[status]}
          </span>
        </div>
        {description && (
          <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        )}
        {metrics && <div className="flex flex-wrap gap-1.5 pt-0.5">{metrics}</div>}
      </CardHeader>
      {children && <CardContent className="pt-0">{children}</CardContent>}
    </Card>
  );
}
