"""Tests for cost estimation."""

from __future__ import annotations

from src.llm.pricing import estimate_cost_usd


def test_gpt_4o_mini_pricing() -> None:
    cost = estimate_cost_usd(
        model="gpt-4o-mini",
        input_tokens=1_000_000,
        output_tokens=0,
    )
    assert cost == 0.15


def test_gpt_4o_pricing_with_output() -> None:
    cost = estimate_cost_usd(
        model="gpt-4o",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert cost == 12.50


def test_unknown_model_uses_default() -> None:
    cost = estimate_cost_usd(
        model="some-future-model",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost > 0


def test_cached_tokens_discount() -> None:
    cached_cost = estimate_cost_usd(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=0,
        cached_input_tokens=1000,
    )
    full_cost = estimate_cost_usd(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=0,
    )
    assert cached_cost < full_cost
