import * as React from "react";
import { cn } from "@/lib/utils";

type HeadingTag = "h1" | "h2" | "h3" | "h4";

const SIZE_FOR: Record<HeadingTag, string> = {
  h1: "text-4xl sm:text-5xl md:text-6xl leading-[1.05] tracking-[-0.025em] font-semibold",
  h2: "text-3xl sm:text-4xl leading-[1.1] tracking-[-0.022em] font-semibold",
  h3: "text-2xl sm:text-3xl leading-[1.15] tracking-[-0.02em] font-semibold",
  h4: "text-xl sm:text-2xl leading-[1.2] tracking-[-0.018em] font-semibold",
};

export interface GradientHeadingProps
  extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: HeadingTag;
  /** Render the gradient on only part of the heading. Pass a string and it will be appended after a space, gradient-styled. */
  highlight?: React.ReactNode;
}

export function GradientHeading({
  as: Tag = "h2",
  className,
  highlight,
  children,
  ...props
}: GradientHeadingProps) {
  return (
    <Tag
      className={cn(SIZE_FOR[Tag], "text-foreground", className)}
      {...props}
    >
      {highlight ? (
        <>
          {children}
          {children ? " " : null}
          <span className="gradient-text">{highlight}</span>
        </>
      ) : (
        <span className="gradient-text">{children}</span>
      )}
    </Tag>
  );
}
