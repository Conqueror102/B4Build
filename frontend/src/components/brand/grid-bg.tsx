import * as React from "react";
import { cn } from "@/lib/utils";

export interface GridBgProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Add a soft violet glow blob behind the grid for hero sections. */
  glow?: boolean;
}

export function GridBg({ glow = true, className, ...props }: GridBgProps) {
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
      {...props}
    >
      <div className="absolute inset-0 grid-bg" />
      {glow && (
        <>
          <div
            className="absolute -top-40 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full opacity-40 blur-3xl"
            style={{
              background:
                "radial-gradient(60% 60% at 50% 50%, oklch(0.55 0.22 295 / 0.55), transparent 70%)",
            }}
          />
          <div
            className="absolute -top-20 left-[60%] h-[260px] w-[420px] rounded-full opacity-30 blur-3xl"
            style={{
              background:
                "radial-gradient(60% 60% at 50% 50%, oklch(0.55 0.25 340 / 0.55), transparent 70%)",
            }}
          />
        </>
      )}
    </div>
  );
}
