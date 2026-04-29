# Backend - AI Build Advisor

Python 3.12 + FastAPI + LangGraph orchestration. Managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
uv sync
cp ../.env.example ../.env  # then fill in OPENAI_API_KEY etc.
```

### WSL + `JSONDecodeError` / broken `requests.compat`

That error means **`requests/compat.py` is truncated or wrong** (middle of the file replaced with empty `pass` blocks). It happens when the **`requests` wheel was extracted badly** — often from **`/mnt/c/`** installs, but **also if uv’s download cache has a bad copy**.

Do this **once** from `backend/` (same shell for all exports):

```bash
export UV_LINK_MODE=copy
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/ai-build-advisor-backend"

uv cache clean
rm -rf .venv "$UV_PROJECT_ENVIRONMENT"

uv sync
uv pip install --force-reinstall --no-cache "requests==2.33.1"

uv run python -c "from requests.compat import JSONDecodeError; print('ok')"
uv run uvicorn src.main:app --reload --host localhost --port 8000
```

Keep `UV_PROJECT_ENVIRONMENT` (and optionally `UV_LINK_MODE`) whenever you use `uv` here, or set them in [direnv](https://direnv.net/) `.envrc`.

## Run

```bash
uv run uvicorn src.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive API docs.

## Layout

```
src/
  main.py           FastAPI app entry
  settings.py       Pydantic settings (env-driven)
  logging_config.py structlog configuration
  llm/
    client.py       LLMClient wrapper (timeout, retry, cost cap, structured output)
    pricing.py      Per-model token pricing for cost computation
  api/
    health.py       /health and /ready
    chat.py         /api/chat (Phase 1+)
    plan.py         /api/plan/{id} (Phase 1+)
  graph/            LangGraph nodes + state (Phase 1+)
  prompts/          Per-phase prompt templates (Phase 1+)
  schemas/          Pydantic output schemas per phase (Phase 1+)
  tools/            Web search, calculator, etc. (Phase 1+)
  db/               SQLAlchemy models + Alembic (Phase 3+)
tests/              pytest suite
```

## Common tasks

```bash
uv run pytest                    # tests
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy src                  # typecheck
```

## Architecture notes

- **Every** LLM call goes through `src/llm/client.py`. Never call the OpenAI SDK directly elsewhere.
- **Every** phase's output is a Pydantic schema. No free-form JSON parsing.
- **Cost guardrails**: per-request and daily-spend caps enforced in `LLMClient`.
- LangGraph state machine is in `src/graph/builder.py` (Phase 1+).
