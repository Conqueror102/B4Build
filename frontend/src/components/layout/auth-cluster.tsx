"use client";

import {
  SignInButton,
  SignUpButton,
  UserButton,
  useAuth,
} from "@clerk/nextjs";
import { Button } from "@/components/ui/button";

/**
 * Client-only auth controls. Clerk v7 dropped the `<SignedIn>` /
 * `<SignedOut>` slot components, so we gate on `useAuth().isSignedIn`
 * directly. While Clerk is still resolving (`isLoaded` is false) we
 * render a stable-width skeleton so the header doesn't flicker.
 */
export function AuthCluster() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <div
        aria-hidden
        className="h-8 w-[140px] rounded-md bg-muted/40 animate-pulse"
      />
    );
  }

  if (isSignedIn) {
    return (
      <UserButton
        appearance={{
          elements: {
            avatarBox:
              "h-8 w-8 ring-1 ring-border hover:ring-[oklch(0.65_0.2_295)]/60 transition-shadow",
          },
        }}
      />
    );
  }

  return (
    <>
      <SignInButton mode="modal">
        <Button variant="ghost" size="sm">
          Sign in
        </Button>
      </SignInButton>
      <SignUpButton mode="modal">
        <Button variant="gradient" size="sm">
          Sign up
        </Button>
      </SignUpButton>
    </>
  );
}
