"""Cost calculator must be deterministic and match published OpenAI pricing."""

from __future__ import annotations

from src.tools.cost_calculator import CostCalculatorInput, calculate_costs, format_for_prompt


def test_gpt_4o_mini_one_million_input_tokens_costs_15_cents() -> None:
    """1M input tokens (one request, no output) at gpt-4o-mini = $0.15.

    PRICING in src/llm/pricing.py says:
      gpt-4o-mini: input $0.15/M, output $0.60/M
    """
    results = calculate_costs(
        [
            CostCalculatorInput(
                label="1M input only",
                monthly_requests=1,
                avg_input_tokens=1_000_000,
                avg_output_tokens=0,
            )
        ]
    )
    assert len(results) == 1
    by_provider = {p.provider: p.monthly_cost_usd for p in results[0].providers}
    assert by_provider["openai_gpt_4o_mini"] == 0.15


def test_gpt_4o_pricing_matches_table() -> None:
    """1M input + 1M output at gpt-4o = 2.50 + 10.00 = $12.50."""
    results = calculate_costs(
        [
            CostCalculatorInput(
                label="1M+1M",
                monthly_requests=1,
                avg_input_tokens=1_000_000,
                avg_output_tokens=1_000_000,
            )
        ]
    )
    by_provider = {p.provider: p.monthly_cost_usd for p in results[0].providers}
    assert by_provider["openai_gpt_4o"] == 12.50


def test_self_host_breakeven_is_computed_when_gpu_provided() -> None:
    results = calculate_costs(
        [
            CostCalculatorInput(
                label="self-host scenario",
                monthly_requests=1_000_000,
                avg_input_tokens=2_000,
                avg_output_tokens=400,
                self_host_gpu_usd_per_hour=1.10,
            )
        ]
    )
    r = results[0]
    assert r.self_host_breakeven_requests_per_month is not None
    assert r.self_host_breakeven_requests_per_month > 0
    by_provider = {p.provider: p.monthly_cost_usd for p in r.providers}
    assert "self_host_gpu" in by_provider
    assert by_provider["self_host_gpu"] == round(1.10 * 730, 2)


def test_calculator_is_deterministic() -> None:
    inputs = [
        CostCalculatorInput(
            label="x",
            monthly_requests=12345,
            avg_input_tokens=987,
            avg_output_tokens=654,
        )
    ]
    a = calculate_costs(inputs)
    b = calculate_costs(inputs)
    assert a == b


def test_format_for_prompt_contains_table_header() -> None:
    results = calculate_costs(
        [
            CostCalculatorInput(
                label="P",
                monthly_requests=10,
                avg_input_tokens=1,
                avg_output_tokens=1,
            )
        ]
    )
    table = format_for_prompt(results)
    assert "| Scenario | Provider |" in table
    assert "| P | openai_gpt_4o |" in table
