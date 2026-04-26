"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Lightweight hover tooltip. No Radix, no portal.
 * Wraps its child in a span that owns hover/focus events; the child can be
 * any element (button, link, icon).
 */

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  delay?: number;
  className?: string;
}

const POSITIONS: Record<NonNullable<TooltipProps["side"]>, string> = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
};

export function Tooltip({
  content,
  children,
  side = "top",
  delay = 150,
  className,
}: TooltipProps) {
  const [open, setOpen] = React.useState(false);
  const timerRef = React.useRef<number | null>(null);
  const id = React.useId();

  const show = React.useCallback(() => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => setOpen(true), delay);
  }, [delay]);

  const hide = React.useCallback(() => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    setOpen(false);
  }, []);

  React.useEffect(
    () => () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    },
    [],
  );

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      aria-describedby={open ? id : undefined}
    >
      {children}
      {open && (
        <span
          role="tooltip"
          id={id}
          className={cn(
            "pointer-events-none absolute z-50 rounded-md",
            "border border-border bg-popover px-2 py-1",
            "text-xs leading-tight text-foreground/90",
            "shadow-lg whitespace-nowrap",
            "animate-in-fade",
            POSITIONS[side],
            className,
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}
