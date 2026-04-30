"""Phase 3 — Tools, managed services, and GitHub-backed open source.

Uses live GitHub search results when available. Output is ``ToolsOpenSourcePhase``
(no build/buy/train enum).
"""

from __future__ import annotations

from typing import Any

from ._shared import render_intake, render_prior_outputs

SYSTEM = """You are the "Phase 3 — Tools & open source" advisor.

Your job is to identify ALL tools, services, libraries, and open-source projects needed to build this product.

Return ONE JSON object (not markdown) with EXACTLY these top-level keys:
- search_context (object; required)
- github_recommendations (list; may be empty)
- managed_tools (list, at least one item)
- integration_summary (string)

## search_context (required object)
Fields:
- query_used: string or null (GitHub query that was run)
- repo_count_returned: integer (how many repos appear in the user message below)
- total_count_estimate: integer or null (GitHub total_count if inferable)
- search_note: short string or null (e.g. "no results", "rate limited", "OK")

## github_recommendations
Each item MUST have: name (owner/repo), url, stars (number), why_relevant,
how_to_integrate, license (string or null), license_risks, last_updated (string).

When the user message lists GitHub repos: prioritize those. Rank and explain the
best 1-5 for THIS product. If the list is empty, set github_recommendations to []
and explain in search_note and integration_summary.

## managed_tools
**CRITICAL**: Be comprehensive! Include ALL tools/services needed for THIS specific idea.

Consider these common categories (but don't limit yourself to them):
- **AI/ML APIs**: OpenAI, Anthropic, Cohere, Hugging Face, Replicate, etc.
- **Authentication**: Clerk, Auth0, Supabase Auth, Firebase Auth, NextAuth, etc.
- **Database**: Supabase, PlanetScale, Neon, MongoDB Atlas, Postgres, etc.
- **Storage**: S3, Cloudinary, UploadThing, Vercel Blob, etc.
- **Payments**: Stripe, Paddle, LemonSqueezy, PayPal, etc.
- **Email**: Resend, SendGrid, Postmark, AWS SES, etc.
- **Hosting/Infrastructure**: Vercel, Railway, Fly.io, AWS, Render, etc.
- **Monitoring**: Sentry, LogRocket, Datadog, BetterStack, etc.
- **Analytics**: PostHog, Mixpanel, Plausible, Amplitude, etc.
- **Search**: Algolia, Meilisearch, Typesense, Elasticsearch, etc.
- **Vector DB**: Pinecone, Weaviate, Qdrant, Chroma, etc.
- **Communication**: Twilio, SendGrid, Slack API, Discord API, etc.
- **Media Processing**: Cloudinary, Mux, FFmpeg, ImageKit, etc.
- **Scheduling**: Inngest, Trigger.dev, Temporal, BullMQ, etc.
- **Real-time**: Pusher, Ably, Socket.io, Supabase Realtime, etc.
- **Domain-specific**: Any specialized tools for the specific use case

**Adapt to the idea**: If building a video app, include video tools. If building a fintech app, include compliance tools.
If building a game, include game engines. Think about what THIS specific product actually needs.

Each item: name, category, role_in_app, rationale, product_url (string or null).

Minimum: THREE managed_tools entries (AI API + hosting + at least one more relevant to the idea).
Be specific about which tier/plan makes sense for the budget and scale.

## integration_summary
2-5 sentences tying chosen repos + tools to Phase 0-2 context. Explain how they work together.
No generic filler - be specific about the integration points.

Do NOT output build/buy/fine_tune enums or candidate_vendors-only lists from the old format."""


def build_prompt(
    state: dict[str, Any],
    *,
    github_repos: list[dict[str, Any]] | None = None,
    github_query: str = "",
    github_total_count: int = 0,
) -> list[dict[str, Any]]:
    intake = render_intake(state)
    prior = render_prior_outputs(state, include=["phase_0", "phase_1", "phase_2"])

    user_msg_parts = [
        f"{intake}\n\n",
        f"Prior phase outputs:\n{prior}\n\n",
    ]

    if "phase_2" not in (state.get("phase_outputs", {}) or {}):
        user_msg_parts.append(
            "Note: Phase 2 (architecture) output is not available (may have been skipped).\n\n"
        )

    repos = github_repos or []
    user_msg_parts.append(
        f"GitHub search: query_used={github_query!r}, "
        f"total_count_estimate={github_total_count}, "
        f"repos_in_prompt={len(repos)}.\n\n"
    )

    if repos:
        user_msg_parts.append("Repositories returned by search (analyze these first):\n")
        for repo in repos:
            user_msg_parts.append(
                f"- {repo['name']} ({repo['stars']} stars)\n"
                f"  URL: {repo['url']}\n"
                f"  Description: {repo.get('description', 'N/A')}\n"
                f"  Language: {repo.get('language', 'N/A')}\n"
                f"  License: {repo.get('license', 'Unknown')}\n"
                f"  Last updated: {repo['last_updated']}\n"
                f"  Topics: {', '.join(repo.get('topics', []))}\n\n"
            )
    else:
        user_msg_parts.append(
            "No GitHub repositories were returned for this query. "
            "Still fill managed_tools and integration_summary from the idea and prior phases; "
            "set github_recommendations to [].\n\n"
        )

    user_msg_parts.append(
        "Produce the JSON. Be opinionated: name concrete tools and repos, not vague categories."
    )

    user_msg = "".join(user_msg_parts)

    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
