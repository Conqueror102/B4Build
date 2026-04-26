"""Deterministic cost projections for Phase 5.

The Phase 5 prompt MUST consume the table this module produces and is
explicitly instructed not to invent its own numbers. That keeps cost figures
reproducible and lets us test them.

Inputs:
- A list of ``CostCalculatorInput`` describing each scenario (pilot, growth,
  scale).
- Optional self-host GPU $/hr if the user is considering running their own
  inference (e.g. an L40S on Runpod ~ $1.10/hr).

Outputs:
- Per-scenario, per-provider monthly cost.
- A naive "self-hosted breakeven" point (where API spend equals GPU rental
  for that scenario's volume).

Pricing comes from ``src.llm.pricing.PRICING`` so the numbers stay in sync
with the LLM cost-cap math. Anthropic / Mistral are estimated at 1.0x and
0.5x of GPT-4o pricing respectively (rough industry observation).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..llm.pricing import DEFAULT_PRICING, PRICE_PER_M_TOKENS_USD, PRICING

GPT_4O = "gpt-4o"
GPT_4O_MINI = "gpt-4o-mini"

CLAUDE_MULTIPLIER_OF_GPT4O = 1.0
MISTRAL_MULTIPLIER_OF_GPT4O = 0.5


@dataclass(frozen=True)
class CostCalculatorInput:
    """One scenario the user wants priced."""

    label: str
    monthly_requests: int
    avg_input_tokens: int
    avg_output_tokens: int
    self_host_gpu_usd_per_hour: float | None = None


@dataclass(frozen=True)
class ProviderCost:
    """Cost for one provider in one scenario."""

    provider: str
    monthly_cost_usd: float


@dataclass(frozen=True)
class CostCalculatorResult:
    """Output for one scenario across all providers."""

    label: str
    monthly_requests: int
    avg_input_tokens: int
    avg_output_tokens: int
    providers: list[ProviderCost]
    self_host_breakeven_requests_per_month: int | None


def _api_cost(model: str, monthly_requests: int, in_tokens: int, out_tokens: int) -> float:
    """Cost (USD) of running one scenario through a hosted API."""
    pricing = PRICING.get(model, DEFAULT_PRICING)
    per_request = (
        in_tokens * pricing.input_per_m + out_tokens * pricing.output_per_m
    ) / PRICE_PER_M_TOKENS_USD
    return round(per_request * monthly_requests, 2)


def _self_host_cost(gpu_usd_per_hour: float) -> float:
    """Naive: assume one GPU rented 24x7 for one month (~730 hours)."""
    return round(gpu_usd_per_hour * 730, 2)


def _self_host_breakeven_requests(
    gpu_usd_per_hour: float,
    in_tokens: int,
    out_tokens: int,
    reference_model: str = GPT_4O_MINI,
) -> int | None:
    """How many monthly requests at gpt-4o-mini pricing equals the GPU bill.

    Returns None if either side of the math is zero/undefined.
    """
    monthly_gpu = _self_host_cost(gpu_usd_per_hour)
    pricing = PRICING.get(reference_model, DEFAULT_PRICING)
    per_request = (
        in_tokens * pricing.input_per_m + out_tokens * pricing.output_per_m
    ) / PRICE_PER_M_TOKENS_USD
    if per_request <= 0:
        return None
    return int(monthly_gpu / per_request)


def calculate_costs(scenarios: list[CostCalculatorInput]) -> list[CostCalculatorResult]:
    """Run the cost math for each scenario. Pure function, deterministic."""
    out: list[CostCalculatorResult] = []
    for s in scenarios:
        gpt4o = _api_cost(GPT_4O, s.monthly_requests, s.avg_input_tokens, s.avg_output_tokens)
        gpt4o_mini = _api_cost(
            GPT_4O_MINI, s.monthly_requests, s.avg_input_tokens, s.avg_output_tokens
        )

        providers = [
            ProviderCost(provider="openai_gpt_4o", monthly_cost_usd=gpt4o),
            ProviderCost(provider="openai_gpt_4o_mini", monthly_cost_usd=gpt4o_mini),
            ProviderCost(
                provider="anthropic_claude_estimate",
                monthly_cost_usd=round(gpt4o * CLAUDE_MULTIPLIER_OF_GPT4O, 2),
            ),
            ProviderCost(
                provider="mistral_estimate",
                monthly_cost_usd=round(gpt4o * MISTRAL_MULTIPLIER_OF_GPT4O, 2),
            ),
        ]

        breakeven: int | None = None
        if s.self_host_gpu_usd_per_hour:
            providers.append(
                ProviderCost(
                    provider="self_host_gpu",
                    monthly_cost_usd=_self_host_cost(s.self_host_gpu_usd_per_hour),
                )
            )
            breakeven = _self_host_breakeven_requests(
                s.self_host_gpu_usd_per_hour,
                s.avg_input_tokens,
                s.avg_output_tokens,
            )

        out.append(
            CostCalculatorResult(
                label=s.label,
                monthly_requests=s.monthly_requests,
                avg_input_tokens=s.avg_input_tokens,
                avg_output_tokens=s.avg_output_tokens,
                providers=providers,
                self_host_breakeven_requests_per_month=breakeven,
            )
        )
    return out


def format_for_prompt(results: list[CostCalculatorResult]) -> str:
    """Render the deterministic table as a markdown string the LLM can quote."""
    lines = ["| Scenario | Provider | Monthly cost (USD) |", "|---|---|---|"]
    for r in results:
        for p in r.providers:
            lines.append(f"| {r.label} | {p.provider} | ${p.monthly_cost_usd:,.2f} |")
    return "\n".join(lines)
