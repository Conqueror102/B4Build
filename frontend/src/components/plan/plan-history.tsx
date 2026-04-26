"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Plus, Clock, FileText, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { getPlans } from "@/lib/api";

interface PlanSummary {
  id: string;
  title: string;
  status: string;
  total_cost_usd: number;
  created_at: string;
  updated_at: string;
}

export function PlanHistory() {
  const params = useParams();
  const router = useRouter();
  const currentPlanId = params?.id as string | undefined;
  
  const [plans, setPlans] = React.useState<PlanSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [isOpen, setIsOpen] = React.useState(false);

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
    <>
      {/* Toggle button - always visible */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-20 z-50 shadow-lg"
      >
        {isOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <span className="ml-1 text-xs">Plans</span>
      </Button>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full w-80 bg-background border-r border-border z-40 transition-transform duration-300",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-sm font-semibold tracking-tight">Your Plans</h2>
            <Button
              variant="gradient"
              size="sm"
              onClick={() => router.push("/plan/new")}
              className="group"
            >
              <Plus className="h-3.5 w-3.5" />
              New
            </Button>
          </div>

          {/* Plans list */}
          <div className="flex-1 overflow-y-auto p-2">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <p className="text-sm text-muted-foreground">Loading plans...</p>
              </div>
            ) : plans.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <FileText className="h-12 w-12 text-muted-foreground/50 mb-3" />
                <p className="text-sm text-muted-foreground mb-4">
                  No plans yet. Create your first plan to get started!
                </p>
                <Button
                  variant="gradient"
                  size="sm"
                  onClick={() => router.push("/plan/new")}
                >
                  <Plus className="h-3.5 w-3.5" />
                  Create Plan
                </Button>
              </div>
            ) : (
              <div className="space-y-1">
                {plans.map((plan) => {
                  const isActive = plan.id === currentPlanId;
                  return (
                    <Link
                      key={plan.id}
                      href={`/plan/${plan.id}`}
                      className={cn(
                        "block rounded-lg p-3 transition-colors hover:bg-muted/50",
                        isActive && "bg-muted border border-border"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="text-sm font-medium line-clamp-2 flex-1">
                          {plan.title || "Untitled Plan"}
                        </h3>
                        {isActive && (
                          <Badge variant="outline" className="text-xs shrink-0">
                            Active
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{formatDate(plan.updated_at)}</span>
                        {plan.status === "complete" && (
                          <Badge variant="success" className="text-xs ml-auto">
                            Complete
                          </Badge>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Overlay when sidebar is open */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
