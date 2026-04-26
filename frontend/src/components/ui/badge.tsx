import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-border bg-muted text-muted-foreground",
        secondary: "border-transparent bg-white/[0.06] text-foreground/80",
        outline: "border-white/12 bg-transparent text-foreground/85",
        gradient:
          "border-transparent gradient-bg text-white shadow-[0_0_0_1px_oklch(0.7_0.2_295/0.35)]",
        success:
          "border-[oklch(0.55_0.16_150/0.35)] bg-[oklch(0.5_0.18_150/0.12)] text-[oklch(0.85_0.18_150)]",
        warning:
          "border-[oklch(0.6_0.16_75/0.4)] bg-[oklch(0.55_0.16_75/0.12)] text-[oklch(0.88_0.16_75)]",
        destructive:
          "border-[oklch(0.55_0.22_25/0.4)] bg-[oklch(0.5_0.22_25/0.12)] text-[oklch(0.85_0.18_25)]",
        info:
          "border-[oklch(0.55_0.16_230/0.4)] bg-[oklch(0.5_0.16_230/0.12)] text-[oklch(0.85_0.16_230)]",
      },
      mono: {
        true: "font-mono uppercase tracking-wider text-[10px] py-1",
        false: "",
      },
    },
    defaultVariants: {
      variant: "default",
      mono: false,
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, mono, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, mono }), className)} {...props} />;
}

export { badgeVariants };
