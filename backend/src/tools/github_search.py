"""GitHub repository search tool for finding relevant open-source projects."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import httpx
from pydantic import BaseModel, Field

from ..logging_config import get_logger
from ..settings import get_settings

logger = get_logger(__name__)


def _resolve_github_token() -> str | None:
    """Prefer Settings (loads ``GITHUB_TOKEN`` from ``.env``); fall back to raw ``os.environ``."""
    t = (get_settings().github_token or "").strip()
    if t:
        return t
    legacy = (os.getenv("GITHUB_TOKEN") or "").strip()
    return legacy or None


class GitHubRepo(BaseModel):
    """A GitHub repository result."""

    name: str = Field(description="Repository name (owner/repo)")
    url: str = Field(description="GitHub URL")
    description: str | None = Field(description="Repository description")
    stars: int = Field(description="Number of stars")
    language: str | None = Field(description="Primary programming language")
    last_updated: str = Field(description="Last update date")
    license: str | None = Field(description="License type")
    topics: list[str] = Field(default_factory=list, description="Repository topics/tags")


class GitHubSearchResult(BaseModel):
    """Result from GitHub search."""

    repos: list[GitHubRepo] = Field(default_factory=list)
    total_count: int = Field(default=0)
    query: str = Field(default="")


async def search_github_repos(
    query: str,
    *,
    max_results: int = 10,
    min_stars: int = 50,
    updated_within_months: int = 12,
) -> GitHubSearchResult:
    """Search GitHub for relevant repositories.

    Args:
        query: Search query (e.g., "contract analysis NLP")
        max_results: Maximum number of results to return (default 10)
        min_stars: Minimum number of stars (default 50)
        updated_within_months: Only include repos updated within this many months (default 12)

    Returns:
        GitHubSearchResult with list of repositories
    """
    # Build the search query with filters
    cutoff_date = datetime.now() - timedelta(days=updated_within_months * 30)
    date_filter = cutoff_date.strftime("%Y-%m-%d")

    # GitHub search query format
    search_query = f"{query} stars:>={min_stars} pushed:>={date_filter}"

    # GitHub API endpoint
    url = "https://api.github.com/search/repositories"
    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }

    github_token = _resolve_github_token()
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Build-Advisor",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            repos = []
            for item in data.get("items", []):
                repo = GitHubRepo(
                    name=item["full_name"],
                    url=item["html_url"],
                    description=item.get("description"),
                    stars=item["stargazers_count"],
                    language=item.get("language"),
                    last_updated=item["updated_at"],
                    license=item.get("license", {}).get("spdx_id") if item.get("license") else None,
                    topics=item.get("topics", []),
                )
                repos.append(repo)

            logger.info(
                "github_search.success",
                query=query,
                total_count=data.get("total_count", 0),
                returned=len(repos),
            )

            return GitHubSearchResult(
                repos=repos,
                total_count=data.get("total_count", 0),
                query=search_query,
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.error("github_search.rate_limited", query=query)
            # Return empty result on rate limit
            return GitHubSearchResult(query=search_query)
        logger.error("github_search.http_error", query=query, status=e.response.status_code)
        raise
    except Exception as e:
        logger.error("github_search.failed", query=query, error=str(e))
        raise


def build_search_query(idea: str, architecture_pattern: str | None = None) -> str:
    """Build a GitHub search query from the user's idea and architecture.

    Args:
        idea: User's project idea
        architecture_pattern: Architecture pattern from Phase 2 (e.g., "rag", "fine-tuning")

    Returns:
        Search query string
    """
    # Extract key terms from the idea
    query_parts = []

    # Add architecture pattern if available
    if architecture_pattern:
        if architecture_pattern.lower() == "rag":
            query_parts.append("RAG retrieval augmented generation")
        elif "fine-tun" in architecture_pattern.lower():
            query_parts.append("fine-tuning LLM")
        elif "agent" in architecture_pattern.lower():
            query_parts.append("AI agent")
        else:
            query_parts.append(architecture_pattern)

    # Add common AI/ML terms
    query_parts.append("AI")

    # Limit to first 100 chars of idea to avoid overly long queries
    idea_snippet = idea[:100]
    query_parts.append(idea_snippet)

    return " ".join(query_parts)
