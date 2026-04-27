# Backend architecture

This document explains how the AI Build Advisor backend is organized so a new
contributor can ramp up without prior LangGraph experience. It covers the
existing Phase 0 foundation **and** the Phase 1 LangGraph state machine that
generates plans.

The advisor turns a user's natural-language idea ("I want to build a chatbot
that summarizes my company's PDFs") into a structured 9-phase build plan that
includes architecture, infra, costs, security, observability, and scaling
recommendations.

---

## 1. Birds-eye view

```
                                ┌────────────────────────┐
                                │  Browser (Next.js UI)  │
                                └──────────┬─────────────┘
                                           │ HTTPS / SSE
                                           ▼
┌─────────────────────────────── FastAPI app (uvicorn) ─────────────────────────────┐
│                                                                                   │
│  /health  /ready          /api/chat (POST, SSE)        /api/plan/{id} (GET)       │
│      │                          │                              │                   │
│      ▼                          ▼                              ▼                   │
│   health.py                 chat.py ────► graph.builder ────► plan.py             │
│                                              │                                     │
│                                              ▼                                     │
│  ┌────────────────── LangGraph state machine ──────────────────┐                  │
│  │                                                             │                  │
│  │  coordinator ──► phase_worker (loops 9 phases) ──► red_team │                  │
│  │       ▲                  │                            │     │                  │
│  │       │                  │                            ▼     │                  │
│  │       └── conversation_handler            synthesizer ──► END                  │
│  │            (clarifying Qs)                                   │                  │
│  └─────────────────────────────────────────────────────────────┘                  │
│                                              │                                     │
│                                              ▼                                     │
│                                       LLMClient (chokepoint)                       │
│                                              │                                     │
│                                              ▼                                     │
│                                   OpenAI ChatCompletions API                       │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                              │
                          structlog ──► stdout (JSON in prod)
                          sentry-sdk ──► Sentry
                          tavily ──► Tavily web search (Phase 0 + Red Team)
```

Phase 1 keeps the persistence layer in-memory (a `dict` in `src/store.py`).
Phase 3 will swap that for Postgres without changing the API surface.

---

## 2. Why these tech choices

| Tool | Why |
|------|-----|
| **FastAPI** | Async, type-hinted, auto-generates OpenAPI docs; SSE works trivially via `StreamingResponse`. |
| **LangGraph** | Lets us model the advisor as a state machine of nodes that mutate a shared `TypedDict`. Easier to reason about, test, and extend than raw `if/elif` orchestration. Built-in checkpointing for Phase 4 conversational mode. |
| **Pydantic v2** | One source of truth for both wire-format validation (request bodies) and structured LLM outputs (`response_format=json_schema`). Same `BaseModel` covers both. |
| **structlog** | JSON logs in production, human-readable in dev. PII (emails) and prompt bodies are masked at the processor layer so individual log calls can't leak by accident. |
| **tenacity** | Declarative retry-with-backoff for `RateLimitError` / `APITimeoutError`. Lives in one place (`LLMClient`) rather than scattered across nodes. |
| **sentry-sdk** | Production error tracking. Initialised in `lifespan` only when a DSN is configured, so dev runs do not require a Sentry account. |
| **Tavily** | Real-time web search for Phase 0 ("has anyone built this already?") and the Red Team node ("does this proposal contradict known best practices?"). Cheaper and lower-latency than calling Google Programmable Search. |
| **tiktoken** | Local token counting for cost-cap pre-checks (currently used implicitly through the OpenAI usage response; tiktoken stays available for Phase 5 calculator). |
| **httpx** | Shared async HTTP client used by Tavily and FastAPI's own `TestClient`. |

---

## 3. File-by-file: existing Phase 0 code

### `src/settings.py`

`Settings(BaseSettings)` is the **only** place we read environment variables.
It loads from `../.env` (project root) and the OS environment. Fields are
strongly typed (`Literal["development", "staging", "production"]`, etc.) so
a typo in `APP_ENV` raises at startup instead of silently doing something
weird at runtime.

`get_settings()` is `@lru_cache(maxsize=1)` so the parsed object is built
once per process. Tests clear that cache in `conftest.py`.

Notable knobs:

- `openai_default_model` (`gpt-4o-mini`) - the cheap workhorse.
- `openai_reasoning_model` (`gpt-4o`) - upgraded model for Phase 2/3/5 + Red Team.
- `daily_openai_spend_cap` - global daily ceiling (enforced once we add a
  cost ledger; currently advisory).
- `per_request_cost_cap` - **hard** ceiling enforced inside `LLMClient` per call.

### `src/logging_config.py`

Two custom processors:

- `_mask_emails` - regex-replaces any email address that appears in a log
  field value with `<email>`.
- `_truncate_prompts` - if a log call includes `prompt`, `completion`, or
  `messages`, the value is shortened to 200 chars or replaced with
  `<N messages, redacted>`. The full prompt is captured in LangSmith,
  not in CloudWatch.

In production we render JSON; in dev we render colored console output.

### `src/llm/pricing.py`

A small `dict[str, ModelPricing]` plus `estimate_cost_usd(model, input_tokens,
output_tokens, cached_input_tokens)`. Cached input tokens (via OpenAI prompt
caching) are billed at the discounted rate when the model supports it. Unknown
models fall back to a conservative default so we never accidentally bill at
$0/M.

### `src/llm/client.py` - the chokepoint

`LLMClient` is a thin async wrapper around `AsyncOpenAI` with two public
methods. When **`LANGCHAIN_TRACING_V2`** and **`LANGCHAIN_API_KEY`** are set in
settings (see `tracing_env.py` startup), the client is wrapped with LangSmith’s
`wrap_openai` so completions appear as traces; otherwise the raw OpenAI client is used. The two public entry points are:

- `complete(messages, ...)` - free-form completion (mostly used by the
  coordinator when it needs to ask clarifying questions).
- `complete_structured(messages, schema=MySchema, ...)` - sends the request
  with `response_format={"type": "json_schema", ...}` derived from a Pydantic
  model, then validates the response with `MySchema.model_validate_json`.
  Raises `LLMSchemaError` if the model returns malformed JSON.

Both methods funnel through `_call_with_retry`, which:

1. Logs the attempt (`llm.attempt`).
2. Retries on `RateLimitError`, `APITimeoutError`, `APIError` with
   exponential backoff (1s -> 10s, capped at `max_retries`).
3. Computes USD cost from the `usage` block.
4. Raises `LLMCostCapExceededError` if the actual cost exceeds
   `per_request_cost_cap_usd` (so a runaway prompt can't burn $50).
5. Logs `llm.completed` with `request_id`, `phase`, model, latency, tokens,
   and cost.

`get_llm_client()` is also `@lru_cache` so all nodes share a single
underlying HTTP client (TLS keep-alive, connection pool).

### `src/api/health.py`

Two endpoints used by load balancers and `kubectl`:

- `GET /health` - liveness; returns 200 if the process is alive.
- `GET /ready` - readiness; today identical to `/health`, will check Postgres
  in Phase 3 and Redis in Phase 5.

### `src/main.py`

Tiny app factory. The `lifespan` async context manager runs once per process:
it configures structlog, initialises Sentry if a DSN is present, logs the
startup banner, and yields. Routers are wired in `create_app()`.

---

## 4. Why every LLM call goes through `LLMClient`

A single chokepoint gives us guardrails that would be tedious to enforce
node-by-node:

1. **Timeouts** - one place to set the OpenAI client timeout.
2. **Retries** - tenacity policy in one place; nodes don't have to know about
   `RateLimitError`.
3. **Cost cap** - per-request hard cap is computed *after* the call from the
   real `usage` block, so a single bad prompt can never silently cost more
   than the cap (the call is allowed to complete, but we raise before the
   caller can use the result; this trades one wasted call for a hard guarantee
   that the cap is honoured).
4. **Schema validation** - `complete_structured` returns a *typed*
   `BaseModel` instance. Nodes never parse JSON by hand.
5. **Logging** - every call emits the same structured `llm.completed` event
   with `request_id` + `phase`, so tracing a single conversation is grep-able.
6. **Test seam** - `LLMClient` is the one symbol tests need to mock to
   exercise the entire graph offline.

If a node ever calls `openai.*` directly, the linter rule will reject it (we
will add this in CI when the Phase 1 graph stabilises).

---

## 5. The 5-node LangGraph design (covers all 9 advisor phases)

The advisor has nine analytical phases (0 through 7, including `6.25` for
security and `6.5` for observability), but encoding nine separate graph nodes
would mean nine near-identical functions. Instead we have **five** structural
nodes and let them route over the nine phases:

| Node | Responsibility |
|------|---------------|
| `coordinator` | Decides what to do next given current `AdvisorState`. If the user hasn't answered clarifying questions yet, jump to `conversation_handler`. If any phase output is missing, route to `phase_worker` for that phase. If everything is filled in, route to `red_team`. |
| `conversation_handler` | (Phase 1: stub) Asks the user clarifying questions. Phase 4 will turn this into a multi-turn refinement loop. |
| `phase_worker` | Polymorphic worker. Reads `state.current_phase`, looks up `(prompt_builder, output_schema, model_tier, tools)` from `src.prompts.PHASE_REGISTRY`, calls `LLMClient.complete_structured`, writes the typed result into `state.phase_outputs[phase_id]`. |
| `red_team` | Adversarial critique pass. Re-reads all phase outputs and produces a `RedTeamCritique` listing risks, contradictions, missing concerns. Uses the reasoning model. |
| `synthesizer` | Compiles a `FullPlan` from all phase outputs + the red team critique into the response shape the frontend renders. |

The graph itself is wired so that `phase_worker -> coordinator -> phase_worker`
is the inner loop until every phase is done; then control flows to `red_team`,
`synthesizer`, and `END`.

```
START ──► coordinator ──► conversation_handler ──► END   (clarify path)
              │
              ├──► phase_worker ──► coordinator (loop: 0,1,2,3,4,5,6.25,6.5,7)
              │
              └──► red_team ──► synthesizer ──► END
```

This keeps the graph small (easy to read, easy to test) while letting us add
new phases by registering one entry in `src.prompts.PHASE_REGISTRY`.

### Per-phase model selection

Cheap (`gpt-4o-mini`):
- Phase 0 (pressure test), Phase 1 (problem-model fit), Phase 4 (infra),
  Phase 6.25 (security checklist), Phase 6.5 (observability), Phase 7 (scaling).

Reasoning (`gpt-4o`):
- Phase 2 (architecture), Phase 3 (build/buy/train), Phase 5 (cost model),
  Red Team.

### Deterministic Phase 5 cost calc

Phase 5 numbers must not be hallucinated. `src/tools/cost_calculator.py`
runs the math in pure Python given (model, monthly volume, avg input/output
tokens, optional self-host GPU $/hr). The Phase 5 prompt receives the
deterministic table as part of its input and is instructed to produce
narrative + recommendations only, not numbers.

---

## 6. Request lifecycle: HTTP -> graph -> LLM -> response

```
1. POST /api/chat  { idea, clarifying_answers?, plan_id? }
       │
2. api/chat.py creates an initial AdvisorState and a request_id.
       │
3. graph.builder.build_graph().astream_events(state) starts:
       │
4.   coordinator decides next node.
       │
5.   phase_worker for current_phase:
        a. PHASE_REGISTRY[phase_id] gives (prompt_builder, schema, model_tier).
        b. messages = prompt_builder(state)
        c. result = await LLMClient.complete_structured(messages, schema=...)
        d. state.phase_outputs[phase_id] = result
        e. yield SSE event { event: phase_complete, phase_id, data }
       │
6.   Loop until all 9 phases done.
       │
7.   red_team -> RedTeamCritique -> SSE.
       │
8.   synthesizer -> FullPlan -> SSE { event: done, plan_id }.
       │
9. store.put(plan_id, FullPlan) so /api/plan/{id} can fetch it later.
```

Every node call is wrapped in try/except so a single failure becomes an
`error` SSE event rather than crashing the stream. The `request_id` is
included in every structured log line so a single conversation is greppable
end-to-end.

---

## 7. How to extend: adding a new phase

Suppose you want to add a "Phase 8: deployment topology".

1. Add `DeploymentTopology(BaseModel)` to `src/schemas/phases.py`.
2. Create `src/prompts/phase_8_deployment.py` with `build_prompt(state)`.
3. Register in `src/prompts/__init__.py`:
   ```python
   PHASE_REGISTRY["phase_8"] = PhaseSpec(
       prompt_builder=phase_8_deployment.build_prompt,
       output_schema=DeploymentTopology,
       model_tier="default",
   )
   PHASE_ORDER.append("phase_8")
   ```
4. Add the field to `FullPlan` in `src/schemas/plan.py`.
5. Add a test that mocks `LLMClient.complete_structured` to return a valid
   `DeploymentTopology` and asserts it ends up in the final plan.

No graph changes required - the polymorphic `phase_worker` and `coordinator`
loop pick up the new entry automatically.
