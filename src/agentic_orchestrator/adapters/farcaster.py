"""
Farcaster adapter for signal collection.

Collects signals from Farcaster (decentralized social network) via:
- Neynar API
- Warpcast public API
- Hub API
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class FarcasterAdapter(BaseAdapter):
    """
    Farcaster adapter.

    Fetches casts (posts) from Farcaster network:
    - Trending casts
    - Followed users' casts
    - Channel activity
    - Cast search
    """

    # Minimum engagement thresholds for quality filtering
    MIN_ENGAGEMENT = {
        'likes': 3,
        'recasts': 1,
        'replies': 0,
    }

    # Neynar API endpoint
    NEYNAR_API = "https://api.neynar.com/v2/farcaster"

    # Warpcast API (public endpoints)
    WARPCAST_API = "https://api.warpcast.com/v2"

    # Farcaster users to track (FIDs or usernames)
    TRACKED_USERS: List[str] = [
        "vitalik.eth",      # Vitalik Buterin
        "dwr.eth",          # Dan Romero (Warpcast founder)
        "v",                # Varun Srinivasan (Farcaster co-founder)
        "balajis.eth",      # Balaji Srinivasan
        "jessepollak",      # Jesse Pollak (Base)
        "coopahtroopa",     # Music NFTs
        "typeof.eth",       # Developer
        "horsefacts.eth",   # Ethereum dev
        "afrochicks.eth",   # Community
        "0xdesigner",       # Designer/builder
    ]

    # Channels to monitor
    TRACKED_CHANNELS: List[str] = [
        "ethereum",
        "base",
        "defi",
        "nft",
        "dev",
        "ai",
        "crypto",
        "web3",
        "founders",
        "memes",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        neynar_api_key: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.neynar_api_key = neynar_api_key or os.getenv("NEYNAR_API_KEY")

    @property
    def name(self) -> str:
        return "farcaster"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from Farcaster."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch different types of content concurrently
        tasks = [
            self._fetch_trending_casts(),
            self._fetch_channel_casts(),
        ]

        # Add user-specific fetching if API key available
        if self.neynar_api_key:
            tasks.append(self._fetch_user_casts())

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
                "users_tracked": len(self.TRACKED_USERS),
                "channels_tracked": len(self.TRACKED_CHANNELS),
                "has_neynar_api": bool(self.neynar_api_key),
            }
        )

    async def _neynar_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make a request to Neynar API."""
        if not self.neynar_api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.NEYNAR_API}/{endpoint}",
                    params=params or {},
                    headers={"api_key": self.neynar_api_key}
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            print(f"Neynar API error: {e}")

        return None

    async def _fetch_trending_casts(self) -> List[SignalData]:
        """Fetch trending casts from Farcaster."""
        signals: List[SignalData] = []

        # Try Neynar API first
        if self.neynar_api_key:
            result = await self._neynar_request(
                "feed/trending",
                {"limit": 25, "time_window": "24h"}
            )

            if result and "casts" in result:
                for cast in result["casts"]:
                    signal = self._cast_to_signal(cast, "trending")
                    if signal:
                        signals.append(signal)

        # Fallback to Warpcast public API
        if not signals:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(
                        f"{self.WARPCAST_API}/recent-casts",
                        params={"limit": 25}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        for cast in data.get("result", {}).get("casts", []):
                            signal = self._warpcast_to_signal(cast, "recent")
                            if signal:
                                signals.append(signal)

            except Exception as e:
                print(f"Warpcast API error: {e}")

        return signals

    async def _fetch_channel_casts(self) -> List[SignalData]:
        """Fetch casts from tracked channels."""
        signals: List[SignalData] = []

        if not self.neynar_api_key:
            return signals

        for channel in self.TRACKED_CHANNELS[:5]:  # Limit API calls
            result = await self._neynar_request(
                "feed/channels",
                {"channel_ids": channel, "limit": 10}
            )

            if result and "casts" in result:
                for cast in result["casts"][:5]:
                    signal = self._cast_to_signal(cast, f"channel:{channel}")
                    if signal:
                        signals.append(signal)

            await asyncio.sleep(0.3)

        return signals

    async def _fetch_user_casts(self) -> List[SignalData]:
        """Fetch casts from tracked users."""
        signals: List[SignalData] = []

        if not self.neynar_api_key:
            return signals

        for username in self.TRACKED_USERS[:5]:  # Limit API calls
            # First get user FID
            user_result = await self._neynar_request(
                "user/by_username",
                {"username": username.replace(".eth", "")}
            )

            if not user_result or "user" not in user_result:
                continue

            fid = user_result["user"].get("fid")
            if not fid:
                continue

            # Then get their casts
            cast_result = await self._neynar_request(
                "feed/user/casts",
                {"fid": fid, "limit": 5}
            )

            if cast_result and "casts" in cast_result:
                for cast in cast_result["casts"]:
                    signal = self._cast_to_signal(cast, f"user:{username}")
                    if signal:
                        signals.append(signal)

            await asyncio.sleep(0.3)

        return signals

    def _meets_engagement_threshold(
        self,
        likes: int,
        recasts: int,
        replies: int,
    ) -> bool:
        """
        Check if cast meets minimum engagement threshold.

        Returns:
            True if meets threshold (at least one metric above minimum)
        """
        # For Farcaster, require at least one metric to meet threshold
        # This is more lenient than requiring all metrics
        if likes >= self.MIN_ENGAGEMENT['likes']:
            return True
        if recasts >= self.MIN_ENGAGEMENT['recasts']:
            return True
        if replies >= self.MIN_ENGAGEMENT.get('replies', 0):
            return True

        # If none meet threshold, check combined engagement
        total_engagement = likes + (recasts * 2) + (replies * 3)
        return total_engagement >= 5  # Minimum combined score

    def _cast_to_signal(
        self,
        cast: Dict[str, Any],
        source_type: str
    ) -> Optional[SignalData]:
        """Convert Neynar cast to SignalData."""
        if not cast:
            return None

        text = cast.get("text", "")
        if not text or len(text) < 10:
            return None

        author = cast.get("author", {})
        username = author.get("username", "unknown")
        display_name = author.get("display_name", username)

        # Calculate engagement
        reactions = cast.get("reactions", {})
        likes = reactions.get("likes_count", 0)
        recasts = reactions.get("recasts_count", 0)
        replies = cast.get("replies", {}).get("count", 0)

        # Skip low-engagement casts (except for tracked users)
        if source_type.startswith("user:"):
            # More lenient for tracked users
            pass
        elif not self._meets_engagement_threshold(likes, recasts, replies):
            return None

        engagement = likes + (recasts * 2) + (replies * 3)

        # Determine category
        category = self._categorize_cast(text)

        return SignalData(
            source=self.name,
            category=category,
            title=f"@{username}: {text[:150]}",
            summary=text[:500] if len(text) > 150 else None,
            url=f"https://warpcast.com/{username}/{cast.get('hash', '')[:10]}",
            raw_data={
                "type": "farcaster_cast",
                "hash": cast.get("hash"),
                "fid": author.get("fid"),
                "username": username,
                "display_name": display_name,
                "likes": likes,
                "recasts": recasts,
                "replies": replies,
                "timestamp": cast.get("timestamp"),
                "source_type": source_type,
            },
            metadata={
                "platform": "farcaster",
                "engagement_score": engagement,
                "source_type": source_type,
            }
        )

    def _warpcast_to_signal(
        self,
        cast: Dict[str, Any],
        source_type: str
    ) -> Optional[SignalData]:
        """Convert Warpcast API cast to SignalData."""
        if not cast:
            return None

        text = cast.get("text", "")
        if not text or len(text) < 10:
            return None

        author = cast.get("author", {})
        username = author.get("username", "unknown")

        return SignalData(
            source=self.name,
            category=self._categorize_cast(text),
            title=f"@{username}: {text[:150]}",
            summary=text[:500] if len(text) > 150 else None,
            url=f"https://warpcast.com/{username}",
            raw_data={
                "type": "farcaster_cast_warpcast",
                "hash": cast.get("hash"),
                "username": username,
                "source_type": source_type,
            },
            metadata={
                "platform": "farcaster",
                "source_type": source_type,
            }
        )

    def _categorize_cast(self, text: str) -> str:
        """Categorize cast based on content."""
        text_lower = text.lower()

        crypto_keywords = [
            "ethereum", "eth", "bitcoin", "btc", "defi", "nft",
            "web3", "blockchain", "token", "crypto", "wallet",
            "base", "optimism", "arbitrum", "polygon"
        ]
        ai_keywords = [
            "ai", "gpt", "llm", "openai", "anthropic", "claude",
            "machine learning", "neural", "chatbot"
        ]

        if any(kw in text_lower for kw in crypto_keywords):
            return "crypto"
        elif any(kw in text_lower for kw in ai_keywords):
            return "ai"
        else:
            return "tech"

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        base_health["neynar_api_configured"] = bool(self.neynar_api_key)
        base_health["tracked_users"] = len(self.TRACKED_USERS)
        base_health["tracked_channels"] = len(self.TRACKED_CHANNELS)

        # Test Neynar API if available
        if self.neynar_api_key:
            try:
                result = await self._neynar_request("user/by_username", {"username": "dwr"})
                base_health["neynar_api_status"] = "connected" if result else "error"
            except Exception as e:
                base_health["neynar_api_status"] = f"error: {e}"

        return base_health
