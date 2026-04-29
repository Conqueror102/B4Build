# How the application works—and how it connects to the infrastructure

**Audience:** Product owners, new teammates, and anyone who wants a story-like explanation of **what the app does** and **how it rides on top of AWS**.

This pairs with [`INFRASTRUCTURE_EXPLAINED.md`](INFRASTRUCTURE_EXPLAINED.md), which focuses on **cloud boxes**. Here we focus on **user journey**, **software flow**, and **how infra and app work together**.

---

## Two “faces” of the system

| Face | Technology | Lives in AWS as |
|------|------------|-----------------|
| **Website** | Next.js (React) | **Amplify** — pages, navigation, buttons |
| **Brain API** | Python FastAPI + LangGraph | **ECS Fargate** — behind **ALB** |

They talk over **HTTPS**: the website calls the API using a **public base URL** stored as **`NEXT_PUBLIC_API_URL`** at build time for Amplify. By default this points at a **CloudFront** distribution in front of the ALB, so the browser only ever sees an HTTPS URL (`https://dxxx.cloudfront.net`) and avoids the **mixed-content** block. CloudFront talks HTTP to the ALB on the origin side — no domain or ACM certificate required.

**Note:** This repository does **not** use a variable named `NEXT_PUBLIC_APP_URL`. The **canonical URL of your web app** is usually Amplify’s default domain or a **custom domain** you add in Amplify. What we explicitly set for builds is **`NEXT_PUBLIC_API_URL`** so the browser knows **where the API lives** — the **CloudFront** URL by default, or your later `https://api...` domain once you set `api_fqdn` + `enable_https_listener`.

---

## Diagram: from user click to answer

```mermaid
sequenceDiagram
  participant User
  participant Browser
  participant Amplify as Amplify_Next.js
  participant CF as CloudFront_HTTPS
  participant ALB as Load_balancer
  participant API as ECS_FastAPI
  participant Graph as LangGraph
  participant LLM as OpenAI
  participant DB as Postgres
  participant SM as Secrets_Manager

  User->>Browser: Types idea clicks Send
  Browser->>Amplify: Load app shell
  Amplify->>Browser: Pages JS CSS
  Browser->>CF: POST api chat SSE over HTTPS
  CF->>ALB: Forward over HTTP origin
  ALB->>API: Forward request
  API->>SM: Keys already in container env
  API->>Graph: Run advisor graph
  loop Each phase
    Graph->>LLM: Structured prompts
    LLM-->>Graph: Text JSON
  end
  Graph->>DB: Save plan checkpoints
  Graph-->>API: Stream events
  API-->>ALB: SSE chunks
  ALB-->>CF: Stream
  CF-->>Browser: Stream over HTTPS
  Browser-->>User: Live report chat
```

---

## What the product does (non-technical)

1. The user describes a **software or AI product idea** in plain language.
2. The system runs a **multi-step “advisor”** that breaks work into **phases** (for example: is the idea viable, architecture, tools, infrastructure, cost, security, etc.).
3. Along the way it may ask **clarifying questions**, run a **red team** critique, and end with a **structured plan** the user can read and export.
4. Progress can be **streamed** to the browser so the user sees updates as they happen.

---

## How the frontend works (Amplify + Next.js)

- **Amplify** hosts the built Next.js app.
- Important env vars for the **build** (set in Amplify / Terraform) include:
  - **`NEXT_PUBLIC_API_URL`** — base URL for all browser calls to your API. Defaults to the **CloudFront** URL Terraform creates (`https://dxxx.cloudfront.net`); falls back to ALB-HTTPS (when a custom `api_fqdn` is set) or ALB-HTTP (local/dev only).
  - **`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`** (if you use Clerk) — safe to expose in the browser; **not** the secret key.
- **Clerk’s secret key** for server-side auth can be supplied to Amplify from **Secrets Manager** in Terraform so server components or SSR can validate users—**never** put that secret in `NEXT_PUBLIC_*`.

When the user submits a chat, the frontend opens a **streaming connection** (Server-Sent Events) to **`/api/chat`** on the API URL. That is why the API must be reachable from the user’s browser over **HTTPS** with the page origin allowed by **CORS** — Terraform passes the allow-list to the ECS task as **`CORS_ALLOW_ORIGINS`** (the Pydantic Settings value `cors_allow_origins`), and `CORSMiddleware` uses `allow_credentials=True`, so wildcards are not allowed.

---

## How the backend works (ECS + FastAPI)

Inside each **ECS task**:

1. **FastAPI** receives HTTP requests.
2. **`/api/chat`** runs a **LangGraph** “state machine”: nodes such as **coordinator**, **phase_worker**, **red_team**, **synthesizer**, etc.
3. Every serious call to the AI goes through **one** module, **`LLMClient`**, which talks to **OpenAI** with guardrails (timeouts, retries, cost caps).
4. **Postgres** stores plans, users, spend, and **checkpoints** so long conversations can resume.
5. **Redis** supports rate limiting and similar fast operations.
6. **Structured logging** goes to CloudWatch; **optional Sentry** catches errors; **optional LangSmith** can trace LLM calls when configured.

So: **infrastructure** gives you a **stable place to run** the container; **application code** decides **what happens** inside that container.

---

## Diagram: LangGraph inside the API (simplified)

```mermaid
flowchart TB
  subgraph browser [Browser]
    UI[Next.js UI]
  end

  subgraph ecs [ECS container]
    API[FastAPI]
    CHAT["/api/chat SSE"]
    G[LangGraph]
    CO[Coordinator]
    PW[Phase worker]
    RT[Red team]
    SYN[Synthesizer]
    LLM[LLMClient to OpenAI]
    API --> CHAT --> G
    G --> CO
    CO --> PW
    PW --> CO
    CO --> RT
    RT --> SYN
    PW --> LLM
    RT --> LLM
    SYN --> LLM
  end

  subgraph data [Data layer]
    PG[(Postgres)]
    R[(Redis)]
  end

  UI -->|"HTTPS SSE"| API
  G --> PG
  API --> R
```

The graph **loops** through phases until the plan is complete or the user must answer questions. That is why one `/api/chat` session can last a while and **stream** many events.

---

## How infrastructure and application connect (cheat sheet)

| App need | Infra piece |
|----------|-------------|
| Run Python API 24/7 | **ECS Fargate** + **ALB** |
| Hide database from internet | **Private subnets** + **RDS** |
| Fast session/rate data | **Redis** in VPC |
| Keep PDFs off the app server | **S3** + IAM role on the task |
| Call OpenAI / Tavily | **NAT Gateway** outbound + **Secrets Manager** keys |
| Ship new backend code | **ECR** image + **GitHub Actions** deploy |
| Ship frontend | **Amplify** build from Git |
| HTTPS for API (no domain) | **CloudFront** in front of ALB (`*.cloudfront.net` cert) |
| HTTPS for API (custom domain) | **ACM** cert + ALB 443 listener (after DNS validation) |
| Allow Amplify origin to call API | **`CORS_ALLOW_ORIGINS`** env on the ECS task (set via `var.cors_allow_origins`) |

---

## End-to-end story (one paragraph)

A person opens your **Amplify** site, which was built from your **GitHub** repo. Their browser loads **JavaScript** that knows **`NEXT_PUBLIC_API_URL`** (the **CloudFront** URL by default). When they start a plan, the browser opens a **streaming connection** to **CloudFront**, which forwards over HTTP to your **load balancer**, which sends traffic to a **healthy ECS task** running **FastAPI**. That task validates the page **Origin** against **`CORS_ALLOW_ORIGINS`**, uses **keys from Secrets Manager**, runs the **LangGraph** advisor, reads and writes **Postgres** (and sometimes **Redis**), may call **OpenAI** and **Tavily** over the internet via **NAT**, and streams results back through the same path until the user sees a finished **plan**—with logs in **CloudWatch** and optional **Sentry** / **LangSmith** for operations.

---

## LangGraph and the nine phases (detailed)

For **breakdown diagrams** of LangGraph nodes, routing, and the fixed phase order (P0–P7, red team, synthesizer), see **[`LANGGRAPH_AND_PHASES_EXPLAINED.md`](LANGGRAPH_AND_PHASES_EXPLAINED.md)**.

---

## Related reading

- Cloud-focused overview: [`INFRASTRUCTURE_EXPLAINED.md`](INFRASTRUCTURE_EXPLAINED.md)
- **LangGraph topology + phase table + conveyor-belt diagram:** [`LANGGRAPH_AND_PHASES_EXPLAINED.md`](LANGGRAPH_AND_PHASES_EXPLAINED.md)
- Backend details for developers: [`../backend/ARCHITECTURE.md`](../backend/ARCHITECTURE.md)
- Bring-up steps: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
