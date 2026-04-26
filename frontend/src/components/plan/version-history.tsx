"use client";

import * as React from "react";
import { History, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getPlanVersions } from "@/lib/api";

interface Version {
  id: string;
  version_num: number;
  notes: string | null;
  created_at: string;
}

interface VersionHistoryProps {
  planId: string;
  onSelectVersion?: (version: Version) => void;
}

export function VersionHistory({ planId, onSelectVersion }: VersionHistoryProps) {
  const [versions, setVersions] = React.useState<Version[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);

  const fetchVersions = React.useCallback(async () => {
    if (!planId) return;
    setLoading(true);
    try {
      const result = await getPlanVersions(planId);
      if (result.ok) {
        setVersions(result.data.versions.reverse()); // Latest first
      } else {
        console.error("Failed to load versions:", result.error);
      }
    } catch (err) {
      console.error("Failed to load versions:", err);
    } finally {
      setLoading(false);
    }
  }, [planId]);

  React.useEffect(() => {
    if (open && versions.length === 0) {
      fetchVersions();
    }
  }, [open, versions.length, fetchVersions]);

  if (!planId) return null;

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-2 border-border/60">
          <History className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">History</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-card border-border/60">
        <div className="px-2 py-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Plan Versions
        </div>
        {loading ? (
          <div className="flex justify-center p-4">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        ) : versions.length > 0 ? (
          versions.map((v, i) => (
            <DropdownMenuItem
              key={v.id}
              onClick={() => onSelectVersion?.(v)}
              className="flex flex-col items-start gap-1 p-2 focus:bg-muted/50 cursor-pointer"
            >
              <div className="flex items-center justify-between w-full">
                <span className="font-medium text-sm">Version {v.version_num}</span>
                {i === 0 && <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded">Latest</span>}
              </div>
              <span className="text-xs text-muted-foreground">
                {new Date(v.created_at).toLocaleString()}
              </span>
            </DropdownMenuItem>
          ))
        ) : (
          <div className="p-3 text-sm text-center text-muted-foreground">
            No versions found.
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
