"""LLMClient - the single chokepoint for every OpenAI call.

Why: enforces guardrails (timeout, retry, cost cap, logging, schema validation)
in one place so individual nodes can't bypass them.

Usage:
    client = get_llm_client()
    result: MySchema = await client.complete_structured(
        messages=[...],
        schema=MySchema,
        model="gpt-4o-mini",
        request_id="...",
        phase="phase_1",
    )
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any, TypeVar

from openai import APIError, AsyncOpenAI, RateLimitError
from openai import APITimeoutError as OpenAITimeoutError
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..logging_config import get_logger
from ..settings import get_settings
from .pricing import estimate_cost_usd

logger = get_logger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def _openai_json_schema_strip_ref_siblings(node: Any) -> None:
    """In-place: JSON Schema objects with ``$ref`` may not include other keys (e.g. ``description``)
    when using OpenAI ``response_format`` strict json_schema — Pydantic v2 often emits
    ``{\"$ref\": \"...\", \"description\": \"...\"}`` for nested model fields. Strip siblings.
    """
    if isinstance(node, dict):
        if "$ref" in node and len(node) > 1:
            ref = node["$ref"]
            node.clear()
            node["$ref"] = ref
        for v in node.values():
            _openai_json_schema_strip_ref_siblings(v)
    elif isinstance(node, list):
        for x in node:
            _openai_json_schema_strip_ref_siblings(x)


class LLMCostCapExceededError(Exception):
    """Raised when an estimated/actual cost exceeds per_request_cost_cap."""


class LLMSchemaError(Exception):
    """Raised when LLM output does not validate against the requested Pydantic schema."""


class LLMClient:
    """Async OpenAI wrapper with guardrails.

    All methods accept a `request_id` and `phase` to enable per-request
    structured logging across the LangGraph state machine.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str,
        timeout_seconds: float,
        max_retries: int,
        per_request_cost_cap_usd: float,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.per_request_cost_cap_usd = per_request_cost_cap_usd

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        request_id: str,
        phase: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Plain completion (free-form). Returns the parsed message dict + metadata.

        Most callers should prefer complete_structured() with a Pydantic schema.
        """
        chosen_model = model or self.default_model
        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        return await self._call_with_retry(
            kwargs=kwargs,
            request_id=request_id,
            phase=phase,
            response_format=None,
        )

    async def complete_structured(
        self,
        messages: list[dict[str, Any]],
        *,
        schema: type[SchemaT],
        request_id: str,
        phase: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> SchemaT:
        """Completion with Pydantic schema enforcement.

        Uses OpenAI's response_format=json_schema for guaranteed shape.
        Raises LLMSchemaError if the result fails validation.
        """
        chosen_model = model or self.default_model
        json_schema = schema.model_json_schema()
        _openai_json_schema_strip_ref_siblings(json_schema)

        # Pydantic may emit a top-level $ref schema. OpenAI strict json_schema mode
        # requires the *root* schema to explicitly set additionalProperties=false.
        # If the root is a $ref into $defs, inline that referenced definition.
        if "$ref" in json_schema and isinstance(json_schema.get("$defs"), dict):
            ref = json_schema["$ref"]
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                def_name = ref.split("/")[-1]
                target = json_schema["$defs"].get(def_name)
                if isinstance(target, dict):
                    json_schema = {**target, "$defs": json_schema["$defs"]}

        json_schema["additionalProperties"] = False
        # OpenAI's strict json_schema mode requires `required` to list every key in `properties`.
        # Optional fields should still be present as keys, but can be `null` per their schema.
        if isinstance(json_schema.get("properties"), dict):
            json_schema["required"] = list(json_schema["properties"].keys())
        
        # Also set additionalProperties=false for all nested object schemas in $defs
        if isinstance(json_schema.get("$defs"), dict):
            for def_schema in json_schema["$defs"].values():
                if isinstance(def_schema, dict) and def_schema.get("type") == "object":
                    def_schema["additionalProperties"] = False
                    if isinstance(def_schema.get("properties"), dict):
                        def_schema["required"] = list(def_schema["properties"].keys())

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": json_schema,
                "strict": True,
            },
        }

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format,
        }

        result = await self._call_with_retry(
            kwargs=kwargs,
            request_id=request_id,
            phase=phase,
            response_format=schema.__name__,
        )

        content = result["content"]
        if not content:
            raise LLMSchemaError(f"Empty response from model for schema {schema.__name__}")

        try:
            return schema.model_validate_json(content)
        except ValidationError as exc:
            logger.error(
                "llm.schema_validation_failed",
                request_id=request_id,
                phase=phase,
                schema=schema.__name__,
                errors=exc.errors()[:5],
            )
            raise LLMSchemaError(
                f"Output did not validate against {schema.__name__}: {exc}"
            ) from exc

    async def _call_with_retry(
        self,
        *,
        kwargs: dict[str, Any],
        request_id: str,
        phase: str | None,
        response_format: str | None,
    ) -> dict[str, Any]:
        """Single call wrapped in retry + logging + cost-cap guardrails."""
        model = kwargs["model"]
        start = time.perf_counter()

        retrying = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((RateLimitError, OpenAITimeoutError, APIError)),
            reraise=True,
        )

        attempt_count = 0
        completion = None
        async for attempt in retrying:
            with attempt:
                attempt_count += 1
                logger.debug(
                    "llm.attempt",
                    request_id=request_id,
                    phase=phase,
                    model=model,
                    attempt=attempt_count,
                )
                completion = await self._client.chat.completions.create(**kwargs)

        if completion is None:
            raise RuntimeError("LLM call did not produce a completion")

        elapsed_ms = (time.perf_counter() - start) * 1000

        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cached_tokens = 0
        if usage and getattr(usage, "prompt_tokens_details", None):
            cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0) or 0

        cost = estimate_cost_usd(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_tokens,
        )

        if cost > self.per_request_cost_cap_usd:
            logger.warning(
                "llm.cost_cap_exceeded",
                request_id=request_id,
                phase=phase,
                model=model,
                cost_usd=cost,
                cap_usd=self.per_request_cost_cap_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            raise LLMCostCapExceededError(
                f"Request cost ${cost:.4f} exceeds cap ${self.per_request_cost_cap_usd:.4f}"
            )

        message = completion.choices[0].message
        finish_reason = completion.choices[0].finish_reason

        logger.info(
            "llm.completed",
            request_id=request_id,
            phase=phase,
            model=model,
            attempts=attempt_count,
            elapsed_ms=round(elapsed_ms, 1),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            cost_usd=cost,
            finish_reason=finish_reason,
            response_format=response_format,
        )

        from ..services.spend_ledger import record_openai_spend_from_llm

        try:
            await record_openai_spend_from_llm(float(cost))
        except Exception:
            logger.exception("llm.spend_ledger_record_failed", request_id=request_id)

        return {
            "content": message.content,
            "tool_calls": message.tool_calls,
            "finish_reason": finish_reason,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "cost_usd": cost,
            "elapsed_ms": elapsed_ms,
        }


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Singleton accessor for LLMClient."""
    settings = get_settings()
    return LLMClient(
        api_key=settings.openai_api_key,
        default_model=settings.openai_default_model,
        timeout_seconds=settings.llm_default_timeout_seconds,
        max_retries=settings.llm_max_retries,
        per_request_cost_cap_usd=settings.per_request_cost_cap,
    )
