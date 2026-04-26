import * as React from "react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon: React.ReactNode;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        "rounded-2xl border border-dashed border-border/80 bg-card/40",
        "px-6 py-16 sm:py-20",
        className,
      )}
      {...props}
    >
      <div className="relative mb-6 inline-flex h-16 w-16 items-center justify-center">
        <div
          aria-hidden
          className="absolute inset-0 rounded-2xl gradient-bg opacity-15 blur-xl"
        />
        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl border border-border/80 bg-muted/40 text-foreground/85 [&>svg]:h-7 [&>svg]:w-7">
          {icon}
        </div>
      </div>
      <h3 className="text-lg font-semibold tracking-tight text-foreground">{title}</h3>
      {description && (
        <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
