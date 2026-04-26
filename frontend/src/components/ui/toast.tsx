"use client";

import { Toaster as SonnerToaster, toast } from "sonner";

/** Re-export sonner with a single, dark-themed Toaster the app can drop into the layout. */
export { toast };

export function Toaster() {
  return (
    <SonnerToaster
      theme="dark"
      position="bottom-right"
      richColors
      closeButton
      toastOptions={{
        style: {
          background: "oklch(0.09 0.005 270)",
          border: "1px solid oklch(0.18 0.005 270)",
          color: "oklch(0.97 0 0)",
          fontFamily: "var(--font-sans)",
        },
      }}
    />
  );
}
