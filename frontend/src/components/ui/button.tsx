import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Lightweight `asChild` shim. Avoids the `@radix-ui/react-slot` install,
 * which the previous installer kept choking on. We accept exactly one
 * React element child and merge our props + className into it.
 */
function MergedSlot({
  children,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  if (!React.isValidElement(children)) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("Button(asChild) requires exactly one React element child.");
    }
    return null;
  }
  const child = children as React.ReactElement<Record<string, unknown>>;
  const childProps = (child.props ?? {}) as Record<string, unknown>;
  const mergedClassName = cn(
    props.className,
    typeof childProps.className === "string" ? childProps.className : undefined,
  );
  return React.cloneElement(child, {
    ...props,
    ...childProps,
    className: mergedClassName,
  });
}

const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "rounded-md text-sm font-medium leading-none",
    "transition-[background,color,box-shadow,transform] duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
    "select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/85",
        secondary:
          "bg-secondary text-secondary-foreground border border-border/60 hover:bg-secondary/80",
        ghost:
          "bg-transparent text-foreground/85 hover:bg-white/[0.04] hover:text-foreground",
        outline:
          "bg-transparent border border-white/10 text-foreground/90 hover:border-white/20 hover:bg-white/[0.03]",
        gradient:
          "gradient-bg text-white font-medium shadow-[0_0_0_1px_oklch(0.7_0.2_295/0.35)] hover:shadow-[0_0_0_1px_oklch(0.7_0.2_295/0.55),0_12px_40px_-12px_oklch(0.7_0.2_295/0.6),0_4px_14px_-2px_oklch(0.7_0.25_340/0.45)] hover:-translate-y-px active:translate-y-0",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        link:
          "bg-transparent text-foreground underline-offset-4 hover:underline px-0 py-0 h-auto",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        default: "h-9 px-4",
        lg: "h-11 px-6 text-base",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button({ className, variant, size, asChild = false, ...props }, ref) {
    const classes = cn(buttonVariants({ variant, size, className }));
    if (asChild) {
      return (
        <MergedSlot className={classes} {...(props as React.HTMLAttributes<HTMLElement>)} />
      );
    }
    return <button ref={ref} className={classes} {...props} />;
  },
);

export { buttonVariants };
