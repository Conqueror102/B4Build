import * as React from "react";
import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted/70",
        // a faint top highlight so the skeleton reads as a "card-like" surface
        "shadow-[inset_0_1px_0_0_oklch(1_0_0/0.03)]",
        className,
      )}
      {...props}
    />
  );
}
