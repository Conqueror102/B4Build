"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, Clock, FileText, Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GradientHeading } from "@/components/brand/gradient-heading";
import { getPlans } from "@/lib/api";

interface PlanSummary {
  id: string;
  title: string;
  status: string;
  total_cost_usd: number;
  created_at: string;
  updated_at: string;
}

export default function PlansPage() {
  const router = useRouter();
  const [plans, setPlans] = React.useState<PlanSummary[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;

    async function loadPlans() {
      const result = await getPlans();
      if (cancelled) return;

      if (result.ok && result.data?.plans) {
        // Sort by updated_at descending (most recent first)
        const sorted = [...result.data.plans].sort(
          (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
        setPlans(sorted);
      }
      setLoading(false);
    }

    loadPlans();
    return () => {
      cancelled = true;
    };
  }, []);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 animate-in-fade">
        <div>
          <GradientHeading as="h1">Your Plans</GradientHeading>
          <p className="mt-2 text-muted-foreground">
            View and manage all your AI architecture plans
          </p>
        </div>
        <Button
          variant="gradient"
          size="lg"
          onClick={() => router.push("/plan/new")}
          className="group"
        >
          <Plus className="h-4 w-4" />
          New Plan
        </Button>
      </div>

      {/* Plans Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mx-auto" />
            <p className="text-sm text-muted-foreground">Loading your plans...</p>
          </div>
        </div>
      ) : plans.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 px-4 text-center border border-dashed border-border rounded-xl animate-in-up">
          <FileText className="h-16 w-16 text-muted-foreground/50 mb-4" />
          <h2 className="text-xl font-semibold mb-2">No plans yet</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Create your first AI architecture plan to get started. Our advisor will guide you through
            every phase from idea to production.
          </p>
          <Button
            variant="gradient"
            size="lg"
            onClick={() => router.push("/plan/new")}
            className="group"
          >
            <Plus className="h-4 w-4" />
            Create Your First Plan
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-in-up">
          {plans.map((plan) => (
            <Link
              key={plan.id}
              href={`/plan/${plan.id}`}
              className="group block rounded-xl border border-border bg-card p-5 transition-all hover:border-border/80 hover:shadow-lg hover:-translate-y-0.5"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="text-base font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                  {plan.title || "Untitled Plan"}
                </h3>
                {plan.status === "complete" && (
                  <Badge variant="success" className="text-xs shrink-0">
                    Complete
                  </Badge>
                )}
              </div>

              <div className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Updated {formatDate(plan.updated_at)}</span>
                </div>
                
                {plan.total_cost_usd > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs">Cost:</span>
                    <span className="font-mono text-xs">
                      ${plan.total_cost_usd.toFixed(4)}
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-4 flex items-center text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                <span>View plan</span>
                <ArrowRight className="h-3 w-3 ml-1 transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
