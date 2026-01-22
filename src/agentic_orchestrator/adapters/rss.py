"""
RSS Feed adapter for signal collection.

Collects signals from RSS feeds across multiple categories:
- AI/ML
- Crypto/Web3
- Finance
- Security
- Dev/Tech
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

import feedparser
import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


@dataclass
class FeedConfig:
    """RSS feed configuration."""
    url: str
    category: str
    name: str
    enabled: bool = True


class RSSAdapter(BaseAdapter):
    """
    RSS Feed adapter.

    Fetches and parses RSS feeds from multiple sources.
    """

    # Default feeds configuration
    DEFAULT_FEEDS: List[FeedConfig] = [
        # AI/ML
        FeedConfig("https://openai.com/blog/rss.xml", "ai", "OpenAI Blog"),
        FeedConfig("https://blog.google/technology/ai/rss/", "ai", "Google AI"),
        FeedConfig("https://techcrunch.com/category/artificial-intelligence/feed/", "ai", "TechCrunch AI"),
        FeedConfig("https://news.ycombinator.com/rss", "ai", "Hacker News"),
        FeedConfig("https://huggingface.co/blog/feed.xml", "ai", "Hugging Face"),
        FeedConfig("https://www.deepmind.com/blog/rss.xml", "ai", "DeepMind"),
        FeedConfig("https://bair.berkeley.edu/blog/feed.xml", "ai", "BAIR"),
        FeedConfig("https://lilianweng.github.io/index.xml", "ai", "Lil'Log"),

        # Crypto/Web3
        FeedConfig("https://www.coindesk.com/arc/outboundfeeds/rss/", "crypto", "CoinDesk"),
        FeedConfig("https://cointelegraph.com/rss", "crypto", "Cointelegraph"),
        FeedConfig("https://decrypt.co/feed", "crypto", "Decrypt"),
        FeedConfig("https://thedefiant.io/feed", "crypto", "The Defiant"),
        FeedConfig("https://cryptoslate.com/feed/", "crypto", "CryptoSlate"),
        FeedConfig("https://blog.ethereum.org/feed.xml", "crypto", "Ethereum Blog"),
        FeedConfig("https://blog.chain.link/rss/", "crypto", "Chainlink"),
        FeedConfig("https://solana.com/news/rss.xml", "crypto", "Solana"),
        FeedConfig("https://polygon.technology/blog/feed", "crypto", "Polygon"),
        FeedConfig("https://research.paradigm.xyz/feed.xml", "crypto", "Paradigm"),
        FeedConfig("https://a16zcrypto.com/feed/", "crypto", "a16z Crypto"),

        # Finance
        FeedConfig("https://www.cnbc.com/id/10001147/device/rss/rss.html", "finance", "CNBC"),
        FeedConfig("https://feeds.bloomberg.com/technology/news.rss", "finance", "Bloomberg Tech"),

        # Security
        FeedConfig("https://krebsonsecurity.com/feed/", "security", "Krebs on Security"),
        FeedConfig("https://blog.trailofbits.com/feed/", "security", "Trail of Bits"),
        FeedConfig("https://www.schneier.com/feed/atom/", "security", "Schneier"),

        # Dev/Tech
        FeedConfig("https://www.theverge.com/rss/index.xml", "dev", "The Verge"),
        FeedConfig("https://feeds.arstechnica.com/arstechnica/technology-lab", "dev", "Ars Technica"),
        FeedConfig("https://stackoverflow.blog/feed/", "dev", "Stack Overflow"),
        FeedConfig("https://github.blog/feed/", "dev", "GitHub Blog"),
        FeedConfig("https://engineering.fb.com/feed/", "dev", "Meta Engineering"),
        FeedConfig("https://netflixtechblog.com/feed", "dev", "Netflix Tech"),
        FeedConfig("https://blog.cloudflare.com/rss/", "dev", "Cloudflare"),
        FeedConfig("https://aws.amazon.com/blogs/aws/feed/", "dev", "AWS Blog"),
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        feeds: Optional[List[FeedConfig]] = None,
        custom_feeds: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.feeds = feeds or self.DEFAULT_FEEDS

        # Add custom feeds if provided
        if custom_feeds:
            for feed in custom_feeds:
                self.feeds.append(FeedConfig(
                    url=feed["url"],
                    category=feed.get("category", "other"),
                    name=feed.get("name", feed["url"]),
                    enabled=feed.get("enabled", True)
                ))

    @property
    def name(self) -> str:
        return "rss"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from all RSS feeds."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch feeds concurrently
        tasks = []
        for feed in self.feeds:
            if feed.enabled:
                tasks.append(self._fetch_feed(feed))

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
                "feeds_count": len(self.feeds),
                "enabled_feeds": len([f for f in self.feeds if f.enabled]),
                "errors_count": len(errors)
            }
        )

    async def _fetch_feed(self, feed: FeedConfig) -> List[SignalData]:
        """Fetch a single RSS feed."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(feed.url, follow_redirects=True)
                response.raise_for_status()

                # Parse feed
                parsed = feedparser.parse(response.text)

                for entry in parsed.entries[:20]:  # Limit to 20 per feed
                    # Extract published date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])

                    # Extract summary
                    summary = None
                    if hasattr(entry, 'summary'):
                        summary = self._clean_html(entry.summary)[:500]
                    elif hasattr(entry, 'description'):
                        summary = self._clean_html(entry.description)[:500]

                    signal = SignalData(
                        source=self.name,
                        category=feed.category,
                        title=entry.get('title', 'No title'),
                        summary=summary,
                        url=entry.get('link'),
                        raw_data={
                            "feed_name": feed.name,
                            "feed_url": feed.url,
                            "published": published.isoformat() if published else None,
                            "author": entry.get('author'),
                            "tags": [t.term for t in entry.get('tags', [])] if hasattr(entry, 'tags') else [],
                        },
                        collected_at=datetime.utcnow(),
                        metadata={"feed_name": feed.name}
                    )
                    signals.append(signal)

        except Exception as e:
            # Log error but don't fail the entire adapter
            print(f"Error fetching feed {feed.name}: {e}")

        return signals

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def add_feed(self, url: str, category: str, name: str) -> None:
        """Add a new feed."""
        self.feeds.append(FeedConfig(url=url, category=category, name=name))

    def remove_feed(self, url: str) -> bool:
        """Remove a feed by URL."""
        for i, feed in enumerate(self.feeds):
            if feed.url == url:
                self.feeds.pop(i)
                return True
        return False

    def get_feeds_by_category(self, category: str) -> List[FeedConfig]:
        """Get feeds by category."""
        return [f for f in self.feeds if f.category == category]

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()
        base_health.update({
            "feeds_count": len(self.feeds),
            "enabled_feeds": len([f for f in self.feeds if f.enabled]),
            "categories": list(set(f.category for f in self.feeds))
        })
        return base_health
