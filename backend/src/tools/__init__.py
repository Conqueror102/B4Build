"""Deterministic tools the graph nodes can call.

Tools live here when they should NOT be implemented by an LLM. The cost
calculator is the canonical example: numbers must be reproducible, so the
math is plain Python and the LLM only consumes the table.
"""

from .cost_calculator import (
    CostCalculatorInput,
    CostCalculatorResult,
    ProviderCost,
    calculate_costs,
)
from .web_search import WebSearchResult, search_web

__all__ = [
    "CostCalculatorInput",
    "CostCalculatorResult",
    "ProviderCost",
    "WebSearchResult",
    "calculate_costs",
    "search_web",
]
