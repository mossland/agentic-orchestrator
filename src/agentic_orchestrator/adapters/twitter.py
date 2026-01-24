"""
Twitter/X adapter for signal collection.

Collects signals from Twitter/X using multiple Nitter RSS instances
for improved reliability and redundancy.
"""

import asyncio
import os
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

import httpx
import feedparser

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class TwitterAdapter(BaseAdapter):
    """
    Twitter/X adapter using Nitter RSS pool.

    Features:
    - Multiple Nitter instance fallback
    - Tracked accounts for crypto/Web3 influencers
    - Keyword-based search (where supported)
    - Rate limiting and retry logic
    """

    # Minimum engagement thresholds for quality filtering
    # Note: Nitter RSS doesn't provide engagement metrics,
    # so these only apply to Twitter API access
    MIN_ENGAGEMENT = {
        'likes': 5,
        'retweets': 2,
        'replies': 0,
    }

    # Twitter/X accounts to monitor (crypto/Web3/AI influencers)
    TRACKED_ACCOUNTS: List[str] = [
        # Mossland related
        "MosslandMOC",
        # Ethereum / Web3 leaders
        "VitalikButerin",
        "punk6529",
        "cz_binance",
        "SBF_FTX",  # Historical reference
        # Crypto analysts
        "MessariCrypto",
        "DefiLlama",
        "DeFiPrime",
        "hasufl",
        # AI / Tech
        "OpenAI",
        "AnthropicAI",
        "ylecun",
        "kaborinho",
        # VCs and projects
        "a16zcrypto",
        "paradigm",
        "polyaborian",
        # News
        "CoinDesk",
        "Cointelegraph",
        "TheBlock__",
    ]

    # Keywords to track for Mossland relevance
    TRACKED_KEYWORDS: List[str] = [
        "mossland",
        "MOC token",
        "metaverse AR",
        "web3 gaming",
        "DeFi yield",
        "NFT utility",
        "DAO governance",
        "AI agent",
        "LLM blockchain",
    ]

    # Nitter instances (public RSS proxies)
    NITTER_INSTANCES: List[str] = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org",
        "nitter.1d4.us",
        "nitter.kavin.rocks",
        "nitter.unixfox.eu",
        "nitter.domain.glass",
        "nitter.namazso.eu",
        "nitter.hu",
        "nitter.it",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        twitter_bearer_token: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.twitter_bearer_token = twitter_bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        self._working_instances: List[str] = []
        self._last_instance_check: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "twitter"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from Twitter/X via Nitter."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Refresh working instances periodically
        await self._refresh_working_instances()

        # Fetch from accounts
        account_signals = await self._fetch_accounts()
        signals.extend(account_signals)

        # If we have Twitter API access, also search keywords
        if self.twitter_bearer_token:
            keyword_signals = await self._search_keywords_api()
            signals.extend(keyword_signals)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "accounts_tracked": len(self.TRACKED_ACCOUNTS),
                "working_instances": len(self._working_instances),
                "has_api_access": bool(self.twitter_bearer_token),
            }
        )

    async def _refresh_working_instances(self) -> None:
        """Check which Nitter instances are working."""
        # Only refresh every 30 minutes
        if (
            self._last_instance_check
            and (datetime.utcnow() - self._last_instance_check).seconds < 1800
        ):
            return

        working = []
        async with httpx.AsyncClient(timeout=10) as client:
            for instance in self.NITTER_INSTANCES:
                try:
                    # Test with a simple request
                    response = await client.get(
                        f"https://{instance}/VitalikButerin/rss",
                        follow_redirects=True
                    )
                    if response.status_code == 200 and len(response.text) > 100:
                        working.append(instance)
                except Exception:
                    continue

        if working:
            self._working_instances = working
        else:
            # Fallback to all instances if none work
            self._working_instances = self.NITTER_INSTANCES[:3]

        self._last_instance_check = datetime.utcnow()

    async def _fetch_accounts(self) -> List[SignalData]:
        """Fetch tweets from tracked accounts via Nitter RSS."""
        signals: List[SignalData] = []

        if not self._working_instances:
            self._working_instances = self.NITTER_INSTANCES[:3]

        async with httpx.AsyncClient(timeout=30) as client:
            # Shuffle accounts to distribute load
            accounts = self.TRACKED_ACCOUNTS.copy()
            random.shuffle(accounts)

            for account in accounts[:15]:  # Limit to 15 accounts per run
                # Try multiple instances
                for instance in random.sample(
                    self._working_instances,
                    min(3, len(self._working_instances))
                ):
                    try:
                        response = await client.get(
                            f"https://{instance}/{account}/rss",
                            follow_redirects=True
                        )

                        if response.status_code == 200:
                            parsed = feedparser.parse(response.text)

                            for entry in parsed.entries[:5]:  # Latest 5 tweets
                                # Extract tweet content
                                title = entry.get("title", "")[:280]
                                description = self._clean_html(
                                    entry.get("description", "")
                                )[:500]

                                # Determine category based on content
                                category = self._categorize_tweet(title + " " + description)

                                # Calculate relevance score
                                relevance = self._calculate_relevance(
                                    title + " " + description
                                )

                                signal = SignalData(
                                    source=self.name,
                                    category=category,
                                    title=f"@{account}: {title}",
                                    summary=description if description != title else None,
                                    url=entry.get("link"),
                                    raw_data={
                                        "type": "tweet",
                                        "account": account,
                                        "nitter_instance": instance,
                                        "published": entry.get("published"),
                                    },
                                    metadata={
                                        "platform": "twitter",
                                        "account": account,
                                        "relevance_score": relevance,
                                    }
                                )
                                signals.append(signal)

                            break  # Success, move to next account

                    except Exception as e:
                        print(f"Error fetching @{account} from {instance}: {e}")
                        continue

                # Rate limiting
                await asyncio.sleep(0.5)

        return signals

    async def _search_keywords_api(self) -> List[SignalData]:
        """Search for keywords using Twitter API v2 (if available)."""
        signals: List[SignalData] = []

        if not self.twitter_bearer_token:
            return signals

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Build search query
                query = " OR ".join(f'"{kw}"' for kw in self.TRACKED_KEYWORDS[:5])
                query += " -is:retweet lang:en"

                response = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    params={
                        "query": query,
                        "max_results": 20,
                        "tweet.fields": "created_at,author_id,public_metrics",
                    },
                    headers={
                        "Authorization": f"Bearer {self.twitter_bearer_token}"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    for tweet in data.get("data", []):
                        metrics = tweet.get("public_metrics", {})

                        # Skip low-engagement tweets
                        if not self._meets_engagement_threshold(metrics):
                            continue

                        signal = SignalData(
                            source=self.name,
                            category="crypto",  # Keywords are crypto-focused
                            title=tweet.get("text", "")[:280],
                            url=f"https://twitter.com/i/web/status/{tweet.get('id')}",
                            raw_data={
                                "type": "tweet_api",
                                "tweet_id": tweet.get("id"),
                                "author_id": tweet.get("author_id"),
                                "metrics": metrics,
                                "likes": metrics.get("like_count", 0),
                                "retweets": metrics.get("retweet_count", 0),
                            },
                            metadata={
                                "platform": "twitter",
                                "source_type": "keyword_search",
                            }
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error searching Twitter API: {e}")

        return signals

    def _meets_engagement_threshold(
        self,
        metrics: Dict[str, Any],
    ) -> bool:
        """
        Check if tweet meets minimum engagement threshold.

        Args:
            metrics: Public metrics from Twitter API

        Returns:
            True if meets threshold
        """
        likes = metrics.get('like_count', 0) or 0
        retweets = metrics.get('retweet_count', 0) or 0
        replies = metrics.get('reply_count', 0) or 0

        # Check individual thresholds
        if likes >= self.MIN_ENGAGEMENT['likes']:
            return True
        if retweets >= self.MIN_ENGAGEMENT['retweets']:
            return True

        # Check combined engagement
        total = likes + (retweets * 2) + replies
        return total >= 8  # Minimum combined score

    def _categorize_tweet(self, content: str) -> str:
        """Categorize tweet based on content."""
        content_lower = content.lower()

        crypto_keywords = [
            "ethereum", "bitcoin", "defi", "nft", "web3", "blockchain",
            "token", "crypto", "wallet", "staking", "yield", "airdrop"
        ]
        ai_keywords = [
            "ai", "gpt", "llm", "openai", "anthropic", "claude",
            "machine learning", "neural", "chatbot", "agent"
        ]

        if any(kw in content_lower for kw in crypto_keywords):
            return "crypto"
        elif any(kw in content_lower for kw in ai_keywords):
            return "ai"
        else:
            return "tech"

    def _calculate_relevance(self, content: str) -> float:
        """Calculate relevance score for Mossland (0-10)."""
        score = 0.0
        content_lower = content.lower()

        # Direct Mossland mentions
        if "mossland" in content_lower or "moc" in content_lower:
            score += 5.0

        # Related topics
        relevance_keywords = {
            "metaverse": 2.0,
            "ar ": 1.5,  # Augmented reality
            "nft": 1.0,
            "gaming": 1.0,
            "web3": 1.0,
            "defi": 0.5,
            "dao": 0.5,
        }

        for keyword, weight in relevance_keywords.items():
            if keyword in content_lower:
                score += weight

        return min(score, 10.0)

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        base_health["twitter_api_configured"] = bool(self.twitter_bearer_token)
        base_health["tracked_accounts"] = len(self.TRACKED_ACCOUNTS)
        base_health["tracked_keywords"] = len(self.TRACKED_KEYWORDS)
        base_health["working_nitter_instances"] = len(self._working_instances)

        return base_health
