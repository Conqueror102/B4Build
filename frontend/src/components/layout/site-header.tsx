import * as React from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { AuthCluster } from "./auth-cluster";

const NAV_LINKS = [
  { href: "/plans", label: "My Plans" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/sample", label: "Sample" },
  { href: "/pricing", label: "Pricing" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/65 backdrop-blur-xl supports-[backdrop-filter]:bg-background/55">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-6 px-4 sm:px-6">
        <Logo />

        <nav className="hidden flex-1 items-center justify-center gap-1 sm:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-white/[0.04] hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:ml-0">
          <Button
            asChild
            variant="gradient"
            size="sm"
            className="group"
          >
            <Link href="/plan/new">
              <Plus className="h-3.5 w-3.5" />
              New Plan
            </Link>
          </Button>
          <AuthCluster />
        </div>
      </div>
    </header>
  );
}
