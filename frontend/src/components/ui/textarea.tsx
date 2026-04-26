import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Render the textarea with the monospace font (good for code / ideas). */
  mono?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea({ className, mono = false, ...props }, ref) {
    return (
      <textarea
        ref={ref}
        className={cn(
          "flex min-h-[120px] w-full rounded-md border border-border bg-input/50 px-3.5 py-3",
          "text-sm leading-relaxed text-foreground placeholder:text-muted-foreground",
          "transition-colors duration-150 resize-y",
          "focus-visible:outline-none focus-visible:border-ring/60 focus-visible:bg-input/70",
          "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-0",
          "disabled:cursor-not-allowed disabled:opacity-50",
          mono && "font-mono text-[13px]",
          className,
        )}
        {...props}
      />
    );
  },
);
