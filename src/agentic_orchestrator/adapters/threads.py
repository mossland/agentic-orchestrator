"""
Threads adapter for signal collection.

Collects signals from Meta Threads by scraping public profile pages.
No authentication required - extracts embedded JSON data from HTML.
"""

import asyncio
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


class ThreadsAdapter(BaseAdapter):
    """
    Meta Threads adapter using public web scraping.

    Fetches public profile pages and extracts thread posts from
    embedded JSON data in <script type="application/json"> tags.
    """

    TRACKED_ACCOUNTS: List[str] = [
        "choi.openai",
        "unclejobs.ai",
        "feelfree_ai",
    ]

    def __init__(self, config: Optional[AdapterConfig] = None):
        super().__init__(config or AdapterConfig(timeout=60))

    @property
    def name(self) -> str:
        return "threads"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from Threads via public profile pages."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        async with httpx.AsyncClient(
            timeout=30,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
        ) as client:
            for account in self.TRACKED_ACCOUNTS:
                try:
                    account_signals = await self._fetch_account(client, account)
                    signals.extend(account_signals)
                except Exception as e:
                    errors.append(f"@{account}: {str(e)[:100]}")
                    logger.warning(f"Error fetching @{account}: {e}")

                await asyncio.sleep(0.5)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0 or len(errors) == 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "accounts_tracked": len(self.TRACKED_ACCOUNTS),
                "accounts_with_errors": len(errors),
            }
        )

    async def _fetch_account(
        self, client: httpx.AsyncClient, account: str
    ) -> List[SignalData]:
        """Fetch threads from a single account's public profile page."""
        signals: List[SignalData] = []

        url = f"https://www.threads.net/@{account}"
        response = await client.get(url)

        if response.status_code != 200:
            logger.warning(f"Threads @{account}: HTTP {response.status_code}")
            return signals

        html = response.text
        posts = self._extract_posts_from_html(html)

        for post in posts[:5]:
            try:
                signal = self._post_to_signal(account, post)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.debug(f"Error parsing thread from @{account}: {e}")

        return signals

    def _extract_posts_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract thread posts from embedded JSON in script tags."""
        posts: List[Dict[str, Any]] = []
        seen_codes: set = set()

        json_blocks = re.findall(
            r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )

        for block in json_blocks:
            if "thread_items" not in block:
                continue
            try:
                data = json.loads(block)
                items = self._find_thread_items(data)
                for item in items:
                    post = item.get("post", {}) if isinstance(item, dict) else {}
                    caption = post.get("caption", {})
                    text = caption.get("text", "") if isinstance(caption, dict) else ""
                    code = post.get("code", "")

                    if text and isinstance(text, str) and len(text) >= 10:
                        if code and code in seen_codes:
                            continue
                        if code:
                            seen_codes.add(code)
                        posts.append({
                            "text": text,
                            "code": code,
                            "id": post.get("id") or post.get("pk"),
                            "like_count": post.get("like_count", 0),
                        })
            except (json.JSONDecodeError, ValueError):
                continue

        return posts

    def _find_thread_items(self, data: Any, depth: int = 0) -> List[Dict]:
        """Recursively find all thread_items lists in nested JSON."""
        results: List[Dict] = []
        if depth > 20:
            return results

        if isinstance(data, dict):
            if "thread_items" in data and isinstance(data["thread_items"], list):
                results.extend(data["thread_items"])
            for v in data.values():
                results.extend(self._find_thread_items(v, depth + 1))
        elif isinstance(data, list):
            for item in data:
                results.extend(self._find_thread_items(item, depth + 1))

        return results

    def _post_to_signal(self, account: str, post: Dict[str, Any]) -> Optional[SignalData]:
        """Convert a parsed post dict into a SignalData."""
        text = post.get("text", "").strip()
        if not text or len(text) < 10:
            return None

        title_text = text[:80].replace("\n", " ")
        if len(text) > 80:
            title_text += "..."
        title = f"@{account}: {title_text}"

        code = post.get("code", "")
        url = f"https://www.threads.net/@{account}/post/{code}" if code else None

        category = self._categorize_content(text)
        relevance = self._calculate_relevance(text)

        return SignalData(
            source=self.name,
            category=category,
            title=title,
            summary=text[:500] if len(text) > 80 else None,
            url=url,
            raw_data={
                "type": "thread",
                "account": account,
                "thread_id": post.get("id"),
                "code": code,
                "likes": post.get("like_count", 0),
            },
            metadata={
                "platform": "threads",
                "account": account,
                "relevance_score": relevance,
            }
        )

    def _categorize_content(self, content: str) -> str:
        """Categorize content based on keywords."""
        content_lower = content.lower()

        ai_keywords = [
            "ai", "gpt", "llm", "openai", "anthropic", "claude",
            "machine learning", "neural", "chatbot", "agent",
            "deep learning", "transformer", "gemini", "copilot",
        ]
        crypto_keywords = [
            "ethereum", "bitcoin", "defi", "nft", "web3", "blockchain",
            "token", "crypto", "wallet", "staking", "yield", "airdrop",
            "solana", "mossland",
        ]

        if any(kw in content_lower for kw in ai_keywords):
            return "ai"
        elif any(kw in content_lower for kw in crypto_keywords):
            return "crypto"
        else:
            return "tech"

    def _calculate_relevance(self, content: str) -> float:
        """Calculate relevance score for Mossland (0-10)."""
        score = 0.0
        content_lower = content.lower()

        if "mossland" in content_lower or "moc" in content_lower:
            score += 5.0

        relevance_keywords = {
            "metaverse": 2.0,
            "ar ": 1.5,
            "nft": 1.0,
            "gaming": 1.0,
            "web3": 1.0,
            "defi": 0.5,
            "dao": 0.5,
            "ai agent": 1.5,
        }

        for keyword, weight in relevance_keywords.items():
            if keyword in content_lower:
                score += weight

        return min(score, 10.0)

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()
        base_health["tracked_accounts"] = len(self.TRACKED_ACCOUNTS)
        base_health["accounts"] = self.TRACKED_ACCOUNTS
        return base_health
