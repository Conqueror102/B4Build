"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Native, ARIA-compliant Tabs. No Radix.
 *
 * Usage:
 *   <Tabs defaultValue="p0">
 *     <TabsList>
 *       <TabsTrigger value="p0">P0</TabsTrigger>
 *       ...
 *     </TabsList>
 *     <TabsContent value="p0">...</TabsContent>
 *   </Tabs>
 */

interface TabsContextValue {
  value: string;
  setValue: (value: string) => void;
  baseId: string;
  registerTrigger: (value: string, el: HTMLButtonElement | null) => void;
  triggers: React.MutableRefObject<Map<string, HTMLButtonElement>>;
  orientation: "horizontal" | "vertical";
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabs() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("Tabs.* must be used inside a <Tabs> root");
  return ctx;
}

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  orientation?: "horizontal" | "vertical";
}

export function Tabs({
  defaultValue,
  value: controlled,
  onValueChange,
  orientation = "horizontal",
  className,
  children,
  ...props
}: TabsProps) {
  const baseId = React.useId();
  const [internal, setInternal] = React.useState<string>(defaultValue ?? "");
  const triggers = React.useRef<Map<string, HTMLButtonElement>>(new Map());

  const isControlled = controlled !== undefined;
  const value = isControlled ? (controlled as string) : internal;

  const setValue = React.useCallback(
    (next: string) => {
      if (!isControlled) setInternal(next);
      onValueChange?.(next);
    },
    [isControlled, onValueChange],
  );

  const registerTrigger = React.useCallback(
    (val: string, el: HTMLButtonElement | null) => {
      if (el) triggers.current.set(val, el);
      else triggers.current.delete(val);
    },
    [],
  );

  return (
    <TabsContext.Provider
      value={{ value, setValue, baseId, registerTrigger, triggers, orientation }}
    >
      <div
        data-orientation={orientation}
        className={cn("flex flex-col gap-4", className)}
        {...props}
      >
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  function TabsList({ className, ...props }, ref) {
    const { orientation } = useTabs();
    return (
      <div
        ref={ref}
        role="tablist"
        aria-orientation={orientation}
        className={cn(
          "relative flex items-stretch gap-1 overflow-x-auto",
          "border-b border-border",
          "no-scrollbar",
          className,
        )}
        {...props}
      />
    );
  },
);

export interface TabsTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  function TabsTrigger({ value, className, children, ...props }, ref) {
    const ctx = useTabs();
    const isActive = ctx.value === value;
    const localRef = React.useRef<HTMLButtonElement | null>(null);

    const setRefs = React.useCallback(
      (node: HTMLButtonElement | null) => {
        localRef.current = node;
        ctx.registerTrigger(value, node);
        if (typeof ref === "function") ref(node);
        else if (ref) (ref as React.MutableRefObject<HTMLButtonElement | null>).current = node;
      },
      [ctx, value, ref],
    );

    const onKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
      const order = Array.from(ctx.triggers.current.keys());
      const i = order.indexOf(value);
      if (i < 0) return;

      const move = (next: number) => {
        const target = ctx.triggers.current.get(order[next]);
        if (target) {
          target.focus();
          ctx.setValue(order[next]);
        }
      };

      const horiz = ctx.orientation === "horizontal";
      const nextKey = horiz ? "ArrowRight" : "ArrowDown";
      const prevKey = horiz ? "ArrowLeft" : "ArrowUp";

      if (e.key === nextKey) {
        e.preventDefault();
        move((i + 1) % order.length);
      } else if (e.key === prevKey) {
        e.preventDefault();
        move((i - 1 + order.length) % order.length);
      } else if (e.key === "Home") {
        e.preventDefault();
        move(0);
      } else if (e.key === "End") {
        e.preventDefault();
        move(order.length - 1);
      }
    };

    return (
      <button
        ref={setRefs}
        type="button"
        role="tab"
        id={`${ctx.baseId}-tab-${value}`}
        aria-controls={`${ctx.baseId}-panel-${value}`}
        aria-selected={isActive}
        tabIndex={isActive ? 0 : -1}
        data-state={isActive ? "active" : "inactive"}
        onClick={() => ctx.setValue(value)}
        onKeyDown={onKeyDown}
        className={cn(
          "relative inline-flex items-center justify-center whitespace-nowrap",
          "px-3.5 py-2.5 -mb-px",
          "text-sm font-medium leading-none",
          "text-muted-foreground hover:text-foreground/90",
          "transition-colors duration-150 outline-none",
          "focus-visible:text-foreground",
          "data-[state=active]:text-foreground",
          // gradient bottom-border on active
          "after:pointer-events-none after:absolute after:inset-x-2 after:bottom-0 after:h-[2px] after:rounded-full",
          "after:opacity-0 after:scale-x-50 after:gradient-bg after:transition-all after:duration-300",
          "data-[state=active]:after:opacity-100 data-[state=active]:after:scale-x-100",
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  /** Keep mounted when inactive (defaults to false). */
  forceMount?: boolean;
}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  function TabsContent(
    { value, forceMount = false, className, children, ...props },
    ref,
  ) {
    const ctx = useTabs();
    const isActive = ctx.value === value;
    if (!isActive && !forceMount) return null;
    return (
      <div
        ref={ref}
        role="tabpanel"
        id={`${ctx.baseId}-panel-${value}`}
        aria-labelledby={`${ctx.baseId}-tab-${value}`}
        hidden={!isActive}
        tabIndex={0}
        className={cn(
          "outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:rounded-lg",
          isActive && "animate-in-fade",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);
