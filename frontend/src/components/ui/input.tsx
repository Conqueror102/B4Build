import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, type = "text", ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-10 w-full rounded-md border border-border bg-input/50 px-3 py-2",
        "text-sm text-foreground placeholder:text-muted-foreground",
        "transition-colors duration-150",
        "focus-visible:outline-none focus-visible:border-ring/60 focus-visible:bg-input/70",
        "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium",
        className,
      )}
      {...props}
    />
  );
});
