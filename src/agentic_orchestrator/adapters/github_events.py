"""
GitHub Events adapter for signal collection.

Collects signals from GitHub:
- Trending repositories
- Releases from watched repos
- Discussions and issues activity
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class GitHubEventsAdapter(BaseAdapter):
    """
    GitHub Events adapter.

    Fetches trending repos, releases, and activity from GitHub.
    """

    # Repositories to watch for releases and activity
    WATCHED_REPOS: List[str] = [
        # AI/ML
        "openai/openai-python",
        "langchain-ai/langchain",
        "huggingface/transformers",
        "anthropics/anthropic-sdk-python",
        "ollama/ollama",
        "ggerganov/llama.cpp",

        # Web3/Crypto
        "ethereum/go-ethereum",
        "solana-labs/solana",
        "paradigmxyz/reth",
        "foundry-rs/foundry",
        "alloy-rs/alloy",
        "wevm/viem",
        "wagmi-dev/wagmi",
        "ethereum/EIPs",

        # Infrastructure
        "vercel/next.js",
        "denoland/deno",
        "oven-sh/bun",

        # Tools
        "anthropics/claude-code",
    ]

    # Topics to search for trending
    TRENDING_TOPICS: List[str] = [
        "web3",
        "defi",
        "nft",
        "ai-agents",
        "llm",
        "blockchain",
        "smart-contracts",
        "ethereum",
        "solana",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        github_token: Optional[str] = None,
        watched_repos: Optional[List[str]] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.watched_repos = watched_repos or self.WATCHED_REPOS
        self.base_url = "https://api.github.com"

    @property
    def name(self) -> str:
        return "github"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Agentic-Orchestrator/0.4.0"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    async def fetch(self) -> AdapterResult:
        """Fetch signals from GitHub."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch different types of GitHub data concurrently
        tasks = [
            self._fetch_trending_repos(),
            self._fetch_releases(),
            self._fetch_topic_repos(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif isinstance(result, list):
                signals.extend(result)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "watched_repos": len(self.watched_repos),
                "topics_count": len(self.TRENDING_TOPICS),
            }
        )

    async def _fetch_trending_repos(self) -> List[SignalData]:
        """Fetch trending repositories."""
        signals: List[SignalData] = []

        try:
            # GitHub doesn't have an official trending API,
            # so we search for recently created popular repos
            since_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            query = f"created:>{since_date} stars:>100"

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 20
                    },
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                for repo in data.get("items", []):
                    signal = SignalData(
                        source=self.name,
                        category="dev",
                        title=f"Trending: {repo['full_name']} ({repo['stargazers_count']} stars)",
                        summary=repo.get("description", "")[:500],
                        url=repo["html_url"],
                        raw_data={
                            "type": "trending",
                            "repo": repo["full_name"],
                            "stars": repo["stargazers_count"],
                            "forks": repo["forks_count"],
                            "language": repo.get("language"),
                            "topics": repo.get("topics", []),
                            "created_at": repo.get("created_at"),
                        },
                        metadata={"subtype": "trending"}
                    )
                    signals.append(signal)

        except Exception as e:
            print(f"Error fetching trending repos: {e}")

        return signals

    async def _fetch_releases(self) -> List[SignalData]:
        """Fetch recent releases from watched repos."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            tasks = []
            for repo in self.watched_repos:
                tasks.append(self._fetch_repo_releases(client, repo))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    signals.extend(result)

        return signals

    async def _fetch_repo_releases(
        self,
        client: httpx.AsyncClient,
        repo: str
    ) -> List[SignalData]:
        """Fetch releases for a single repo."""
        signals: List[SignalData] = []

        try:
            response = await client.get(
                f"{self.base_url}/repos/{repo}/releases",
                params={"per_page": 3},
                headers=self._get_headers()
            )

            if response.status_code == 200:
                releases = response.json()

                for release in releases:
                    # Only include recent releases (last 7 days)
                    published = datetime.fromisoformat(
                        release["published_at"].replace("Z", "+00:00")
                    )
                    if datetime.now().astimezone() - published > timedelta(days=7):
                        continue

                    # Determine category based on repo
                    category = self._categorize_repo(repo)

                    signal = SignalData(
                        source=self.name,
                        category=category,
                        title=f"Release: {repo} {release['tag_name']}",
                        summary=release.get("body", "")[:500] if release.get("body") else None,
                        url=release["html_url"],
                        raw_data={
                            "type": "release",
                            "repo": repo,
                            "tag": release["tag_name"],
                            "name": release.get("name"),
                            "prerelease": release.get("prerelease", False),
                            "published_at": release["published_at"],
                        },
                        metadata={"subtype": "release"}
                    )
                    signals.append(signal)

        except Exception as e:
            print(f"Error fetching releases for {repo}: {e}")

        return signals

    async def _fetch_topic_repos(self) -> List[SignalData]:
        """Fetch popular repos by topic."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for topic in self.TRENDING_TOPICS[:5]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        f"{self.base_url}/search/repositories",
                        params={
                            "q": f"topic:{topic}",
                            "sort": "updated",
                            "order": "desc",
                            "per_page": 5
                        },
                        headers=self._get_headers()
                    )

                    if response.status_code == 200:
                        data = response.json()

                        for repo in data.get("items", []):
                            # Determine category
                            category = "crypto" if topic in ["web3", "defi", "nft", "blockchain", "ethereum", "solana", "smart-contracts"] else "ai"

                            signal = SignalData(
                                source=self.name,
                                category=category,
                                title=f"Active: {repo['full_name']} (topic: {topic})",
                                summary=repo.get("description", "")[:500],
                                url=repo["html_url"],
                                raw_data={
                                    "type": "topic_repo",
                                    "topic": topic,
                                    "repo": repo["full_name"],
                                    "stars": repo["stargazers_count"],
                                    "updated_at": repo.get("updated_at"),
                                },
                                metadata={"subtype": "topic", "topic": topic}
                            )
                            signals.append(signal)

                    # Rate limit protection
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching topic {topic}: {e}")

        return signals

    def _categorize_repo(self, repo: str) -> str:
        """Categorize a repo based on its name/path."""
        repo_lower = repo.lower()

        if any(x in repo_lower for x in ["ethereum", "solana", "web3", "blockchain", "defi", "nft", "foundry", "alloy", "viem", "wagmi"]):
            return "crypto"
        elif any(x in repo_lower for x in ["openai", "anthropic", "langchain", "huggingface", "llm", "ollama"]):
            return "ai"
        elif any(x in repo_lower for x in ["security", "audit"]):
            return "security"
        else:
            return "dev"

    def add_watched_repo(self, repo: str) -> None:
        """Add a repo to watch."""
        if repo not in self.watched_repos:
            self.watched_repos.append(repo)

    def remove_watched_repo(self, repo: str) -> bool:
        """Remove a repo from watch list."""
        if repo in self.watched_repos:
            self.watched_repos.remove(repo)
            return True
        return False

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        # Check GitHub API access
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/rate_limit",
                    headers=self._get_headers()
                )
                if response.status_code == 200:
                    rate_limit = response.json()
                    base_health["rate_limit"] = {
                        "remaining": rate_limit["resources"]["core"]["remaining"],
                        "limit": rate_limit["resources"]["core"]["limit"],
                        "reset": rate_limit["resources"]["core"]["reset"],
                    }
                    base_health["api_status"] = "connected"
                else:
                    base_health["api_status"] = "error"
        except Exception as e:
            base_health["api_status"] = f"error: {e}"

        base_health["watched_repos"] = len(self.watched_repos)
        return base_health
