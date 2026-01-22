"""
News API adapter for signal collection.

Collects signals from news APIs:
- NewsAPI.org
- Cryptopanic
- Messari (if available)
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class NewsAPIAdapter(BaseAdapter):
    """
    News API adapter.

    Fetches news from NewsAPI.org and Cryptopanic.
    """

    # Search queries for NewsAPI
    NEWS_QUERIES: List[Dict[str, str]] = [
        {"query": "blockchain", "category": "crypto"},
        {"query": "web3", "category": "crypto"},
        {"query": "cryptocurrency regulation", "category": "crypto"},
        {"query": "AI artificial intelligence startup", "category": "ai"},
        {"query": "machine learning", "category": "ai"},
        {"query": "metaverse", "category": "crypto"},
        {"query": "NFT gaming", "category": "crypto"},
    ]

    # Cryptopanic filters
    CRYPTOPANIC_FILTERS: List[str] = [
        "rising",
        "hot",
        "bullish",
        "bearish",
        "important",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        newsapi_key: Optional[str] = None,
        cryptopanic_key: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.newsapi_key = newsapi_key or os.getenv("NEWSAPI_KEY")
        self.cryptopanic_key = cryptopanic_key or os.getenv("CRYPTOPANIC_API_KEY")

        self.newsapi_url = "https://newsapi.org/v2"
        self.cryptopanic_url = "https://cryptopanic.com/api/v1"

    @property
    def name(self) -> str:
        return "news"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from news APIs."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch from different news sources concurrently
        tasks = []

        if self.newsapi_key:
            tasks.append(self._fetch_newsapi())

        if self.cryptopanic_key:
            tasks.append(self._fetch_cryptopanic())

        # Always fetch from free sources
        tasks.append(self._fetch_hackernews())

        if tasks:
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
                "newsapi_configured": bool(self.newsapi_key),
                "cryptopanic_configured": bool(self.cryptopanic_key),
            }
        )

    async def _fetch_newsapi(self) -> List[SignalData]:
        """Fetch from NewsAPI.org."""
        signals: List[SignalData] = []

        if not self.newsapi_key:
            return signals

        async with httpx.AsyncClient(timeout=30) as client:
            for query_config in self.NEWS_QUERIES[:3]:  # Limit to conserve API quota
                try:
                    # Get news from last 24 hours
                    from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

                    response = await client.get(
                        f"{self.newsapi_url}/everything",
                        params={
                            "q": query_config["query"],
                            "from": from_date,
                            "sortBy": "relevancy",
                            "language": "en",
                            "pageSize": 10,
                            "apiKey": self.newsapi_key
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()

                        for article in data.get("articles", []):
                            signal = SignalData(
                                source=self.name,
                                category=query_config["category"],
                                title=article.get("title", "")[:300],
                                summary=article.get("description", "")[:500] if article.get("description") else None,
                                url=article.get("url"),
                                raw_data={
                                    "type": "newsapi",
                                    "query": query_config["query"],
                                    "source_name": article.get("source", {}).get("name"),
                                    "author": article.get("author"),
                                    "published_at": article.get("publishedAt"),
                                },
                                metadata={"platform": "newsapi", "query": query_config["query"]}
                            )
                            signals.append(signal)

                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching NewsAPI for '{query_config['query']}': {e}")

        return signals

    async def _fetch_cryptopanic(self) -> List[SignalData]:
        """Fetch from Cryptopanic."""
        signals: List[SignalData] = []

        if not self.cryptopanic_key:
            return signals

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.cryptopanic_url}/posts/",
                    params={
                        "auth_token": self.cryptopanic_key,
                        "public": "true",
                        "filter": "hot",
                        "kind": "news",
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    for post in data.get("results", [])[:20]:
                        # Determine sentiment
                        votes = post.get("votes", {})
                        positive = votes.get("positive", 0)
                        negative = votes.get("negative", 0)
                        sentiment = "bullish" if positive > negative else "bearish" if negative > positive else "neutral"

                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            title=post.get("title", "")[:300],
                            summary=None,  # Cryptopanic doesn't provide summaries
                            url=post.get("url"),
                            raw_data={
                                "type": "cryptopanic",
                                "kind": post.get("kind"),
                                "domain": post.get("domain"),
                                "votes": votes,
                                "sentiment": sentiment,
                                "currencies": [c.get("code") for c in post.get("currencies", [])],
                                "created_at": post.get("created_at"),
                            },
                            metadata={"platform": "cryptopanic", "sentiment": sentiment}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching Cryptopanic: {e}")

        return signals

    async def _fetch_hackernews(self) -> List[SignalData]:
        """Fetch from Hacker News (free, no API key needed)."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get top stories
                response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")

                if response.status_code == 200:
                    story_ids = response.json()[:30]  # Top 30 stories

                    # Fetch story details
                    tasks = [
                        client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                        for story_id in story_ids[:15]  # Limit concurrent requests
                    ]
                    responses = await asyncio.gather(*tasks, return_exceptions=True)

                    for resp in responses:
                        if isinstance(resp, Exception):
                            continue
                        if resp.status_code != 200:
                            continue

                        story = resp.json()
                        if not story:
                            continue

                        title = story.get("title", "").lower()

                        # Filter for relevant stories
                        relevant_keywords = [
                            "ai", "llm", "gpt", "openai", "anthropic", "machine learning",
                            "blockchain", "crypto", "ethereum", "bitcoin", "web3", "defi",
                            "startup", "vc", "funding", "launch",
                        ]

                        if not any(kw in title for kw in relevant_keywords):
                            continue

                        # Categorize
                        category = "ai" if any(kw in title for kw in ["ai", "llm", "gpt", "openai", "anthropic", "machine learning"]) else "crypto" if any(kw in title for kw in ["blockchain", "crypto", "ethereum", "bitcoin", "web3", "defi"]) else "dev"

                        signal = SignalData(
                            source=self.name,
                            category=category,
                            title=f"HN: {story.get('title', '')}",
                            summary=None,
                            url=story.get("url") or f"https://news.ycombinator.com/item?id={story.get('id')}",
                            raw_data={
                                "type": "hackernews",
                                "hn_id": story.get("id"),
                                "score": story.get("score", 0),
                                "comments": story.get("descendants", 0),
                                "by": story.get("by"),
                                "time": story.get("time"),
                            },
                            metadata={"platform": "hackernews"}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching Hacker News: {e}")

        return signals

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        base_health["newsapi_configured"] = bool(self.newsapi_key)
        base_health["cryptopanic_configured"] = bool(self.cryptopanic_key)

        # Test Hacker News (always available)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                base_health["hackernews_status"] = "connected" if response.status_code == 200 else "error"
        except Exception as e:
            base_health["hackernews_status"] = f"error: {e}"

        return base_health
