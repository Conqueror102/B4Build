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
        Search query string optimized for GitHub search
    """
    # Extract key technical terms (remove common words)
    stop_words = {
        "a", "an", "the", "for", "to", "of", "in", "on", "at", "by", "with",
        "that", "this", "it", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "should",
        "could", "may", "might", "must", "can", "i", "you", "we", "they",
        "my", "your", "our", "their", "app", "application", "tool", "system",
        "build", "create", "make", "develop"
    }
    
    # Extract meaningful keywords from idea
    words = idea.lower().split()
    keywords = [w.strip(".,!?;:") for w in words if w.strip(".,!?;:") not in stop_words and len(w) > 3]
    
    # Take top 3-5 most relevant keywords
    query_parts = keywords[:5]
    
    # Add architecture-specific terms
    if architecture_pattern:
        pattern_lower = architecture_pattern.lower()
        if "rag" in pattern_lower:
            query_parts.insert(0, "RAG")
            query_parts.insert(1, "vector-search")
        elif "fine-tun" in pattern_lower:
            query_parts.insert(0, "fine-tuning")
            query_parts.insert(1, "LLM")
        elif "agent" in pattern_lower:
            query_parts.insert(0, "agent")
            query_parts.insert(1, "LLM")
        elif "pipeline" in pattern_lower:
            query_parts.insert(0, "pipeline")
    
    # Limit to 5-6 keywords for best results
    return " ".join(query_parts[:6])
