"""OpenAI model pricing (USD per 1M tokens).

Update periodically. Used to compute per-request cost for guardrails and observability.
Pricing as of late 2025; confirm against https://openai.com/api/pricing.
"""

from __future__ import annotations

from dataclasses import dataclass

PRICE_PER_M_TOKENS_USD = 1_000_000


@dataclass(frozen=True)
class ModelPricing:
    input_per_m: float
    output_per_m: float
    cached_input_per_m: float | None = None


PRICING: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(input_per_m=2.50, output_per_m=10.00, cached_input_per_m=1.25),
    "gpt-4o-mini": ModelPricing(input_per_m=0.15, output_per_m=0.60, cached_input_per_m=0.075),
    "gpt-4-turbo": ModelPricing(input_per_m=10.00, output_per_m=30.00),
    "gpt-3.5-turbo": ModelPricing(input_per_m=0.50, output_per_m=1.50),
    "o1-preview": ModelPricing(input_per_m=15.00, output_per_m=60.00),
    "o1-mini": ModelPricing(input_per_m=3.00, output_per_m=12.00),
}

DEFAULT_PRICING = ModelPricing(input_per_m=2.50, output_per_m=10.00)


def estimate_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
) -> float:
    """Compute USD cost for a single LLM call."""
    pricing = PRICING.get(model)
    if pricing is None:
        normalized = model.split(":", 1)[0].split("/", 1)[-1]
        pricing = PRICING.get(normalized, DEFAULT_PRICING)

    billable_input = max(input_tokens - cached_input_tokens, 0)

    cost = (
        billable_input * pricing.input_per_m + output_tokens * pricing.output_per_m
    ) / PRICE_PER_M_TOKENS_USD

    if cached_input_tokens and pricing.cached_input_per_m is not None:
        cost += (cached_input_tokens * pricing.cached_input_per_m) / PRICE_PER_M_TOKENS_USD

    return round(cost, 6)
