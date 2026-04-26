import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const chipVariants = cva(
  "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[11px] tracking-tight whitespace-nowrap transition-colors",
  {
    variants: {
      variant: {
        default: "border-border bg-muted/60 text-foreground/80",
        model:
          "border-[oklch(0.55_0.18_295/0.4)] bg-[oklch(0.5_0.2_295/0.10)] text-[oklch(0.85_0.15_295)]",
        cost:
          "border-[oklch(0.5_0.18_150/0.4)] bg-[oklch(0.45_0.18_150/0.10)] text-[oklch(0.85_0.18_150)]",
        latency:
          "border-[oklch(0.5_0.16_230/0.4)] bg-[oklch(0.45_0.16_230/0.10)] text-[oklch(0.85_0.16_230)]",
        warning:
          "border-[oklch(0.55_0.16_75/0.4)] bg-[oklch(0.5_0.16_75/0.10)] text-[oklch(0.88_0.16_75)]",
        error:
          "border-[oklch(0.55_0.22_25/0.4)] bg-[oklch(0.5_0.22_25/0.10)] text-[oklch(0.85_0.18_25)]",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface MetricChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chipVariants> {
  icon?: React.ReactNode;
  label?: string;
  value?: React.ReactNode;
}

export function MetricChip({
  className,
  variant,
  icon,
  label,
  value,
  children,
  ...props
}: MetricChipProps) {
  return (
    <span className={cn(chipVariants({ variant }), className)} {...props}>
      {icon && <span className="[&>svg]:h-3 [&>svg]:w-3 opacity-80">{icon}</span>}
      {label && (
        <span className="uppercase tracking-[0.12em] text-foreground/55 text-[10px]">
          {label}
        </span>
      )}
      {value !== undefined ? (
        <span className="text-foreground/90">{value}</span>
      ) : (
        children
      )}
    </span>
  );
}
