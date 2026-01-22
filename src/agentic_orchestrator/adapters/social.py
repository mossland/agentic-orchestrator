"""
Social Media adapter for signal collection.

Collects signals from social platforms:
- Reddit (via API)
- Twitter/X (via Nitter RSS)
- Farcaster (via public API)
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import httpx
import feedparser

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class SocialMediaAdapter(BaseAdapter):
    """
    Social Media adapter.

    Fetches signals from Reddit, Twitter (via Nitter), and Farcaster.
    """

    # Subreddits to monitor
    SUBREDDITS: List[str] = [
        "ethereum",
        "cryptocurrency",
        "defi",
        "web3",
        "nft",
        "CryptoTechnology",
        "ethdev",
        "solana",
        "MachineLearning",
        "LocalLLaMA",
        "artificial",
    ]

    # Twitter/X accounts to monitor (via Nitter)
    TWITTER_ACCOUNTS: List[str] = [
        "VitalikButerin",
        "caborinho",
        "punk6529",
        "MessariCrypto",
        "DefiLlama",
        "a16zcrypto",
        "hasufl",
    ]

    # Nitter instances
    NITTER_INSTANCES: List[str] = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.reddit_client_id = reddit_client_id or os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = reddit_client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self._reddit_token: Optional[str] = None
        self._reddit_token_expires: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "social"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from social media."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch from different platforms concurrently
        tasks = [
            self._fetch_reddit(),
            self._fetch_twitter_nitter(),
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
                "subreddits_count": len(self.SUBREDDITS),
                "twitter_accounts_count": len(self.TWITTER_ACCOUNTS),
            }
        )

    async def _get_reddit_token(self) -> Optional[str]:
        """Get Reddit API token."""
        if not self.reddit_client_id or not self.reddit_client_secret:
            return None

        # Check if token is still valid
        if self._reddit_token and self._reddit_token_expires:
            if datetime.utcnow() < self._reddit_token_expires:
                return self._reddit_token

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=(self.reddit_client_id, self.reddit_client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"User-Agent": "Agentic-Orchestrator/0.4.0"}
                )
                response.raise_for_status()
                data = response.json()

                self._reddit_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._reddit_token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)

                return self._reddit_token

        except Exception as e:
            print(f"Error getting Reddit token: {e}")
            return None

    async def _fetch_reddit(self) -> List[SignalData]:
        """Fetch signals from Reddit."""
        signals: List[SignalData] = []

        # Try API first, fall back to RSS
        token = await self._get_reddit_token()

        if token:
            signals = await self._fetch_reddit_api(token)
        else:
            signals = await self._fetch_reddit_rss()

        return signals

    async def _fetch_reddit_api(self, token: str) -> List[SignalData]:
        """Fetch Reddit using API."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for subreddit in self.SUBREDDITS:
                try:
                    response = await client.get(
                        f"https://oauth.reddit.com/r/{subreddit}/hot",
                        params={"limit": 10},
                        headers={
                            "Authorization": f"Bearer {token}",
                            "User-Agent": "Agentic-Orchestrator/0.4.0"
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        for post in data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})

                            # Determine category
                            category = self._categorize_subreddit(subreddit)

                            signal = SignalData(
                                source=self.name,
                                category=category,
                                title=f"r/{subreddit}: {post_data.get('title', '')[:200]}",
                                summary=post_data.get("selftext", "")[:500] if post_data.get("selftext") else None,
                                url=f"https://reddit.com{post_data.get('permalink', '')}",
                                raw_data={
                                    "type": "reddit",
                                    "subreddit": subreddit,
                                    "score": post_data.get("score", 0),
                                    "num_comments": post_data.get("num_comments", 0),
                                    "author": post_data.get("author"),
                                    "created_utc": post_data.get("created_utc"),
                                },
                                metadata={"platform": "reddit", "subreddit": subreddit}
                            )
                            signals.append(signal)

                    # Rate limit
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching r/{subreddit}: {e}")

        return signals

    async def _fetch_reddit_rss(self) -> List[SignalData]:
        """Fetch Reddit using RSS (fallback)."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for subreddit in self.SUBREDDITS[:5]:  # Limit without API
                try:
                    response = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/hot.rss",
                        headers={"User-Agent": "Agentic-Orchestrator/0.4.0"},
                        follow_redirects=True
                    )

                    if response.status_code == 200:
                        parsed = feedparser.parse(response.text)

                        for entry in parsed.entries[:10]:
                            category = self._categorize_subreddit(subreddit)

                            signal = SignalData(
                                source=self.name,
                                category=category,
                                title=f"r/{subreddit}: {entry.get('title', '')[:200]}",
                                summary=self._clean_html(entry.get("summary", ""))[:500] if entry.get("summary") else None,
                                url=entry.get("link"),
                                raw_data={
                                    "type": "reddit_rss",
                                    "subreddit": subreddit,
                                },
                                metadata={"platform": "reddit", "subreddit": subreddit}
                            )
                            signals.append(signal)

                    await asyncio.sleep(1)  # Be nice to Reddit

                except Exception as e:
                    print(f"Error fetching r/{subreddit} RSS: {e}")

        return signals

    async def _fetch_twitter_nitter(self) -> List[SignalData]:
        """Fetch Twitter/X via Nitter RSS."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for account in self.TWITTER_ACCOUNTS[:5]:  # Limit
                # Try different Nitter instances
                for instance in self.NITTER_INSTANCES:
                    try:
                        response = await client.get(
                            f"https://{instance}/{account}/rss",
                            follow_redirects=True
                        )

                        if response.status_code == 200:
                            parsed = feedparser.parse(response.text)

                            for entry in parsed.entries[:5]:
                                signal = SignalData(
                                    source=self.name,
                                    category="crypto",  # Most followed accounts are crypto-related
                                    title=f"@{account}: {entry.get('title', '')[:200]}",
                                    summary=self._clean_html(entry.get("description", ""))[:500],
                                    url=entry.get("link"),
                                    raw_data={
                                        "type": "twitter",
                                        "account": account,
                                        "nitter_instance": instance,
                                    },
                                    metadata={"platform": "twitter", "account": account}
                                )
                                signals.append(signal)

                            break  # Success, move to next account

                    except Exception as e:
                        print(f"Error fetching @{account} from {instance}: {e}")
                        continue

                await asyncio.sleep(1)

        return signals

    def _categorize_subreddit(self, subreddit: str) -> str:
        """Categorize based on subreddit name."""
        subreddit_lower = subreddit.lower()

        if subreddit_lower in ["ethereum", "cryptocurrency", "defi", "web3", "nft", "ethdev", "solana", "cryptotechnology"]:
            return "crypto"
        elif subreddit_lower in ["machinelearning", "localllama", "artificial"]:
            return "ai"
        else:
            return "other"

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        base_health["reddit_api_configured"] = bool(self.reddit_client_id and self.reddit_client_secret)
        base_health["subreddits"] = len(self.SUBREDDITS)
        base_health["twitter_accounts"] = len(self.TWITTER_ACCOUNTS)

        return base_health
