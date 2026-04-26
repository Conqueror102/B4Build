# AI Build Advisor

A conversational AI advisor that walks engineers and founders through every decision of building an AI application — from idea validation to production deployment to scaling.

> Status: under active development. See [the build plan](.cursor/plans/) for the phased roadmap.

## What it does

Given an AI product idea, the advisor produces a complete, interactive build plan covering:

| Phase | Question Answered |
|---|---|
| 0. Idea Pressure-Test | Should you even build this? |
| 1. Problem-Model Fit | What AI capability solves this? Is it production-ready? |
| 2. Architecture | How do you structure the system? |
| 3. Build vs. Buy vs. Train | What's your path to the model? |
| 4. Infrastructure & Hosting | Where does it run? |
| 5. Cost Modeling | What does it cost now vs. later? |
| 6.25. Security & Compliance | Is it protected? |
| 6.5. Observability & Metrics | How do you know it's working? |
| 7. Scaling Path | How do you grow without going broke? |

Plus a **Synthesizer** that compiles the plan and a **Red Team** that attacks it for fatal flaws. The conversation iteration layer lets users ask "what if I use Claude instead?" and have only the affected phases re-run.

## Architecture

Five-node LangGraph state machine:

```
Coordinator (router) -> Phase Worker (polymorphic, runs all 9 phases)
                     -> Conversation Handler (intent classification + impact analysis)
                     -> Synthesizer (final report)
                     -> Red Team (adversarial critique)
```

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, LangGraph, OpenAI SDK, Pydantic, SQLAlchemy, Postgres |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind, Zod, Clerk |
| Infra | AWS (Fargate, RDS, Redis, ALB, Amplify), Terraform |
| Tooling | uv (Python), pnpm (Node), Docker, GitHub Actions |

## Repository layout

```
backend/   Python + FastAPI + LangGraph
frontend/  Next.js
infra/     Terraform (shared, envs/dev)
evals/     Golden eval dataset + promptfoo configs
```

## Local development

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md).

```bash
# Backend
cd backend
uv sync
uv run uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
pnpm install
pnpm dev
```
