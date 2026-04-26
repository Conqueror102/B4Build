import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export interface LogoProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Hide the wordmark and only show the monogram. */
  iconOnly?: boolean;
  /** Wrap the logo in a Next.js Link to "/". Defaults to true. */
  asLink?: boolean;
}

export function Logo({
  iconOnly = false,
  asLink = true,
  className,
  ...props
}: LogoProps) {
  const inner = (
    <div className={cn("inline-flex items-center gap-2.5", className)} {...props}>
      <Monogram className="h-7 w-7 shrink-0" />
      {!iconOnly && (
        <span className="flex flex-col leading-none">
          <span className="text-[15px] font-semibold tracking-tight text-foreground">
            AI Build Advisor
          </span>
          <span className="mt-0.5 text-[10px] uppercase tracking-[0.16em] text-muted-foreground/80 font-mono">
            Plan before you ship
          </span>
        </span>
      )}
    </div>
  );

  if (asLink) {
    return (
      <Link
        href="/"
        className="group inline-flex outline-none focus-visible:ring-2 focus-visible:ring-ring/50 rounded-md"
      >
        {inner}
      </Link>
    );
  }
  return inner;
}

function Monogram({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
    >
      <defs>
        <linearGradient id="ab-grad" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="oklch(0.7 0.2 295)" />
          <stop offset="100%" stopColor="oklch(0.7 0.25 340)" />
        </linearGradient>
        <linearGradient id="ab-fill" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="oklch(0.16 0.04 295)" />
          <stop offset="100%" stopColor="oklch(0.13 0.05 340)" />
        </linearGradient>
      </defs>
      <rect
        x="1.25"
        y="1.25"
        width="29.5"
        height="29.5"
        rx="8"
        fill="url(#ab-fill)"
        stroke="url(#ab-grad)"
        strokeWidth="1.5"
      />
      {/* Diagonal split */}
      <path
        d="M5 26 L26 5"
        stroke="url(#ab-grad)"
        strokeWidth="1.25"
        strokeLinecap="round"
        opacity="0.6"
      />
      {/* Stylized "A" peak */}
      <path
        d="M9 22 L13.5 9.5 L18 22 M10.6 18.5 H16.4"
        stroke="url(#ab-grad)"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* "B" stem */}
      <path
        d="M21.5 22 V9.5 H24 a3 3 0 0 1 0 6 H21.5 a3.2 3.2 0 0 1 0 6.5 H21"
        stroke="url(#ab-grad)"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
