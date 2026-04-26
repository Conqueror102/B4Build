import { Check } from "lucide-react";
import { GradientHeading } from "@/components/brand/gradient-heading";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const metadata = {
  title: "Pricing | AI Build Advisor",
  description: "Simple pricing for the AI Build Advisor.",
};

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-24 sm:px-6 lg:px-8">
      <div className="text-center mb-16">
        <GradientHeading as="h1" className="mb-4">
          Free during Beta
        </GradientHeading>
        <p className="text-xl text-muted-foreground">
          Generate unlimited architecture plans while we fine-tune the agents.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Free Tier */}
        <div className="rounded-3xl border border-[oklch(0.55_0.18_295/0.45)] bg-card/60 p-8 shadow-2xl relative overflow-hidden">
          <div
            aria-hidden
            className="absolute -inset-px rounded-3xl"
            style={{
              background:
                "radial-gradient(40% 60% at 50% 0%, oklch(0.55 0.22 295 / 0.1), transparent 70%)",
            }}
          />
          <div className="relative">
            <h2 className="text-2xl font-bold mb-2">Beta Preview</h2>
            <div className="mb-6 flex items-baseline gap-1">
              <span className="text-4xl font-bold">$0</span>
              <span className="text-muted-foreground">/mo</span>
            </div>
            
            <ul className="space-y-4 mb-8 text-sm text-muted-foreground">
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-primary" />
                <span>Full 9-phase architecture generation</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-primary" />
                <span>Adversarial red-teaming</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-primary" />
                <span>PDF export and sharing</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-primary" />
                <span>Iterative "What-If" sandbox</span>
              </li>
            </ul>

            <Button asChild variant="gradient" className="w-full">
              <Link href="/plan/new">Start Building Now</Link>
            </Button>
          </div>
        </div>

        {/* Future Pro Tier */}
        <div className="rounded-3xl border border-border bg-card/30 p-8 opacity-80">
          <div className="relative">
            <div className="inline-flex items-center rounded-full border border-border/60 bg-muted px-2.5 py-0.5 text-xs font-semibold mb-4">
              Coming Soon
            </div>
            <h2 className="text-2xl font-bold mb-2">Pro Tier</h2>
            <div className="mb-6 flex items-baseline gap-1">
              <span className="text-4xl font-bold">TBD</span>
            </div>
            
            <ul className="space-y-4 mb-8 text-sm text-muted-foreground">
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-muted-foreground/50" />
                <span>Export to Terraform / Pulumi</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-muted-foreground/50" />
                <span>Export to Docker Compose</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-muted-foreground/50" />
                <span>Deep integrations with AWS/GCP</span>
              </li>
              <li className="flex items-center gap-3">
                <Check className="h-4 w-4 text-muted-foreground/50" />
                <span>Private team collaboration</span>
              </li>
            </ul>

            <Button variant="outline" className="w-full" disabled>
              Join Waitlist (Soon)
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
