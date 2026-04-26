"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Native, accessible modal dialog. No Radix.
 * - Closes on Escape, click outside, and the X button
 * - Locks body scroll while open
 * - Focuses the first focusable element on open, restores focus on close
 */

interface DialogContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
  titleId: string;
  descId: string;
}

const DialogContext = React.createContext<DialogContextValue | null>(null);
const useDialog = () => {
  const ctx = React.useContext(DialogContext);
  if (!ctx) throw new Error("Dialog.* must be used inside a <Dialog>");
  return ctx;
};

export interface DialogProps {
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export function Dialog({ open: controlled, defaultOpen, onOpenChange, children }: DialogProps) {
  const [internal, setInternal] = React.useState(defaultOpen ?? false);
  const isControlled = controlled !== undefined;
  const open = isControlled ? (controlled as boolean) : internal;

  const setOpen = React.useCallback(
    (next: boolean) => {
      if (!isControlled) setInternal(next);
      onOpenChange?.(next);
    },
    [isControlled, onOpenChange],
  );

  const titleId = React.useId();
  const descId = React.useId();

  return (
    <DialogContext.Provider value={{ open, setOpen, titleId, descId }}>
      {children}
    </DialogContext.Provider>
  );
}

export interface DialogTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

export const DialogTrigger = React.forwardRef<HTMLButtonElement, DialogTriggerProps>(
  function DialogTrigger({ asChild, onClick, children, ...props }, ref) {
    const { setOpen } = useDialog();
    const handler = (e: React.MouseEvent<HTMLButtonElement>) => {
      onClick?.(e);
      if (!e.defaultPrevented) setOpen(true);
    };
    if (
      asChild &&
      React.isValidElement<{ onClick?: React.MouseEventHandler<HTMLElement> }>(children)
    ) {
      return React.cloneElement(children, {
        onClick: (e) => {
          children.props.onClick?.(e);
          if (!e.defaultPrevented) setOpen(true);
        },
      });
    }
    return (
      <button ref={ref} type="button" onClick={handler} {...props}>
        {children}
      </button>
    );
  },
);

export interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** When true, does not render the default close X. */
  hideClose?: boolean;
}

export const DialogContent = React.forwardRef<HTMLDivElement, DialogContentProps>(
  function DialogContent({ className, children, hideClose = false, ...props }, ref) {
    const { open, setOpen, titleId, descId } = useDialog();
    const previousFocus = React.useRef<HTMLElement | null>(null);
    const contentRef = React.useRef<HTMLDivElement | null>(null);
    // We can't call createPortal during SSR — guard on document existing.
    const canPortal = typeof document !== "undefined";

    React.useEffect(() => {
      if (!open) return;

      previousFocus.current = (document.activeElement as HTMLElement | null) ?? null;
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";

      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          setOpen(false);
        }
      };
      window.addEventListener("keydown", onKey);

      const focusTimer = window.setTimeout(() => {
        const node = contentRef.current;
        if (!node) return;
        const focusable = node.querySelector<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
        );
        (focusable ?? node).focus();
      }, 30);

      return () => {
        document.body.style.overflow = originalOverflow;
        window.removeEventListener("keydown", onKey);
        window.clearTimeout(focusTimer);
        previousFocus.current?.focus?.();
      };
    }, [open, setOpen]);

    const setRefs = React.useCallback(
      (node: HTMLDivElement | null) => {
        contentRef.current = node;
        if (typeof ref === "function") ref(node);
        else if (ref) (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
      },
      [ref],
    );

    if (!canPortal || !open) return null;

    return createPortal(
      <div
        className="fixed inset-0 z-[100] flex items-center justify-center p-4"
        style={{ animation: "overlay-in 0.18s ease-out both" }}
      >
        <div
          aria-hidden
          onClick={() => setOpen(false)}
          className="absolute inset-0 bg-black/60 backdrop-blur-md"
        />
        <div
          ref={setRefs}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          aria-describedby={descId}
          tabIndex={-1}
          className={cn(
            "relative z-10 w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl",
            "p-6 outline-none",
            className,
          )}
          style={{ animation: "dialog-in 0.22s cubic-bezier(0.16, 1, 0.3, 1) both" }}
          {...props}
        >
          {children}
          {!hideClose && (
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close dialog"
              className={cn(
                "absolute right-4 top-4 inline-flex h-7 w-7 items-center justify-center rounded-md",
                "text-muted-foreground hover:bg-white/[0.06] hover:text-foreground",
                "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
              )}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>,
      document.body,
    );
  },
);

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1.5 pb-3", className)} {...props} />;
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)}
      {...props}
    />
  );
}

export const DialogTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(function DialogTitle({ className, ...props }, ref) {
  const { titleId } = useDialog();
  return (
    <h2
      ref={ref}
      id={titleId}
      className={cn("text-lg font-semibold leading-tight tracking-tight", className)}
      {...props}
    />
  );
});

export const DialogDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(function DialogDescription({ className, ...props }, ref) {
  const { descId } = useDialog();
  return (
    <p
      ref={ref}
      id={descId}
      className={cn("text-sm text-muted-foreground leading-relaxed", className)}
      {...props}
    />
  );
});

export interface DialogCloseProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

export const DialogClose = React.forwardRef<HTMLButtonElement, DialogCloseProps>(
  function DialogClose({ asChild, onClick, children, ...props }, ref) {
    const { setOpen } = useDialog();
    if (
      asChild &&
      React.isValidElement<{ onClick?: React.MouseEventHandler<HTMLElement> }>(children)
    ) {
      return React.cloneElement(children, {
        onClick: (e) => {
          children.props.onClick?.(e);
          if (!e.defaultPrevented) setOpen(false);
        },
      });
    }
    return (
      <button
        ref={ref}
        type="button"
        onClick={(e) => {
          onClick?.(e);
          if (!e.defaultPrevented) setOpen(false);
        }}
        {...props}
      >
        {children}
      </button>
    );
  },
);
