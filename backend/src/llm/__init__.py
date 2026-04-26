"""LLM client wrappers.

All OpenAI calls in the codebase MUST go through src.llm.client.LLMClient.
Direct openai.* calls are forbidden - the wrapper enforces guardrails:
- Timeouts
- Retries with exponential backoff
- Per-request cost cap
- Structured logging (latency, tokens, cost)
- Pydantic schema validation on outputs
"""

from .client import LLMClient, get_llm_client
from .pricing import estimate_cost_usd

__all__ = ["LLMClient", "estimate_cost_usd", "get_llm_client"]
