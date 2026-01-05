"""
RSS/Atom feed fetching and parsing.

Fetches news articles from configured RSS feeds and converts them
to FeedItem objects for trend analysis.
"""

import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from ..utils.config import Config, load_config
from ..utils.logging import get_logger
from .models import FeedConfig, FeedItem

logger = get_logger(__name__)


class FeedFetcher:
    """
    Fetches and parses RSS/Atom feeds.

    Handles multiple feed sources with error recovery and rate limiting.
    """

    # Time period mappings in hours
    PERIOD_HOURS = {
        "24h": 24,
        "1w": 24 * 7,
        "1m": 24 * 30,
    }

    def __init__(
        self,
        config: Config | None = None,
        client: httpx.Client | None = None,
    ):
        """
        Initialize feed fetcher.

        Args:
            config: Configuration object. Loads default if not provided.
            client: Optional httpx client for reuse.
        """
        self.config = config or load_config()
        self._client = client
        self._feed_configs: list[FeedConfig] | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-loaded HTTP client."""
        if self._client is None:
            timeout = self.config.get("trends", "fetch", "timeout_seconds", default=30)
            user_agent = self.config.get(
                "trends", "fetch", "user_agent", default="Agentic-Orchestrator/1.0"
            )
            self._client = httpx.Client(
                timeout=timeout,
                headers={"User-Agent": user_agent},
                follow_redirects=True,
            )
        return self._client

    @property
    def feed_configs(self) -> list[FeedConfig]:
        """Load and cache feed configurations."""
        if self._feed_configs is None:
            self._feed_configs = self._load_feed_configs()
        return self._feed_configs

    def _load_feed_configs(self) -> list[FeedConfig]:
        """Load feed configurations from config.yaml."""
        configs = []
        feeds_config = self.config.get("trends", "feeds", default={})

        if not feeds_config:
            logger.warning("No feeds configured in config.yaml")
            return configs

        for category, feeds in feeds_config.items():
            if not isinstance(feeds, list):
                continue
            for feed_data in feeds:
                try:
                    configs.append(FeedConfig.from_dict(feed_data, category))
                except (KeyError, TypeError) as e:
                    logger.warning(f"Invalid feed config in category '{category}': {e}")

        logger.info(f"Loaded {len(configs)} feed configurations")
        return configs

    def fetch_all_feeds(self) -> list[FeedItem]:
        """
        Fetch all configured feeds.

        Skips failed feeds gracefully and continues with available data.

        Returns:
            List of FeedItem objects from all feeds.
        """
        all_items: list[FeedItem] = []
        failed_feeds: list[tuple[str, str]] = []
        success_feeds: list[tuple[str, int]] = []

        logger.info(f"Starting to fetch {len(self.feed_configs)} configured feeds...")

        for feed_config in self.feed_configs:
            try:
                items = self.fetch_feed(feed_config)
                all_items.extend(items)
                success_feeds.append((feed_config.name, len(items)))
                logger.info(f"  ✓ {feed_config.name}: {len(items)} items")
            except Exception as e:
                error_msg = str(e)[:100]
                failed_feeds.append((feed_config.name, error_msg))
                logger.error(f"  ✗ {feed_config.name}: {error_msg}")

        logger.info(
            f"Feed fetch summary: {len(success_feeds)} succeeded, {len(failed_feeds)} failed"
        )
        if failed_feeds:
            logger.warning(f"Failed feeds: {[f[0] for f in failed_feeds]}")

        # Remove duplicates by URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            if item.link not in seen_urls:
                seen_urls.add(item.link)
                unique_items.append(item)

        logger.info(
            f"Fetched {len(unique_items)} unique items from "
            f"{len(self.feed_configs) - len(failed_feeds)}/{len(self.feed_configs)} feeds"
        )

        return unique_items

    def fetch_feed(self, feed_config: FeedConfig) -> list[FeedItem]:
        """
        Fetch a single feed.

        Args:
            feed_config: Feed configuration.

        Returns:
            List of FeedItem objects from this feed.

        Raises:
            Exception: If feed cannot be fetched or parsed.
        """
        max_retries = self.config.get("trends", "fetch", "max_retries", default=3)

        for attempt in range(max_retries):
            try:
                # Fetch the feed content
                response = self.client.get(feed_config.url)
                response.raise_for_status()

                # Parse with feedparser
                feed = feedparser.parse(response.text)

                if feed.bozo and not feed.entries:
                    raise ValueError(f"Feed parse error: {feed.bozo_exception}")

                # Convert to FeedItem objects
                items = []
                for entry in feed.entries:
                    try:
                        item = self._parse_entry(entry, feed_config)
                        if item:
                            items.append(item)
                    except Exception as e:
                        logger.debug(f"Skipping entry in {feed_config.name}: {e}")
                        continue

                return items

            except httpx.HTTPError:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.debug(
                        f"Retry {attempt + 1}/{max_retries} for {feed_config.name} "
                        f"after {wait_time}s"
                    )
                    time.sleep(wait_time)
                else:
                    raise

        return []

    def _parse_entry(
        self,
        entry: dict[str, Any],
        feed_config: FeedConfig,
    ) -> FeedItem | None:
        """
        Parse a single feed entry into a FeedItem.

        Args:
            entry: Feedparser entry dictionary.
            feed_config: Feed configuration for source/category.

        Returns:
            FeedItem or None if entry is invalid.
        """
        # Get title
        title = entry.get("title", "").strip()
        if not title:
            return None

        # Get link
        link = entry.get("link", "")
        if not link:
            return None

        # Get published date
        published = self._parse_date(entry)
        if not published:
            # Use current time if no date available
            published = datetime.utcnow()

        # Get summary/description
        summary = ""
        if "summary" in entry:
            summary = entry["summary"]
        elif "description" in entry:
            summary = entry["description"]
        elif "content" in entry and entry["content"]:
            summary = entry["content"][0].get("value", "")

        # Clean HTML from summary
        summary = self._clean_html(summary)

        # Truncate long summaries
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return FeedItem(
            title=title,
            link=link,
            published=published,
            summary=summary,
            source=feed_config.name,
            category=feed_config.category,
        )

    def _parse_date(self, entry: dict[str, Any]) -> datetime | None:
        """
        Parse date from feed entry.

        Tries multiple date fields and formats.
        """
        # Try structured date first
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            parsed = entry.get(field)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except (TypeError, ValueError):
                    continue

        # Try string date fields
        for field in ["published", "updated", "created", "date"]:
            date_str = entry.get(field)
            if date_str:
                try:
                    return parsedate_to_datetime(date_str)
                except (TypeError, ValueError):
                    pass
                try:
                    # ISO format fallback
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except (TypeError, ValueError):
                    continue

        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re

        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        clean = re.sub(r"\s+", " ", clean)
        # Decode common entities
        clean = clean.replace("&nbsp;", " ")
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&#39;", "'")

        return clean.strip()

    def filter_by_period(
        self,
        items: list[FeedItem],
        period: str,
    ) -> list[FeedItem]:
        """
        Filter items by time period.

        Args:
            items: List of feed items.
            period: Time period (24h, 1w, 1m).

        Returns:
            Filtered list of items within the time period.
        """
        hours = self.PERIOD_HOURS.get(period, 24)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        now = datetime.utcnow()

        filtered = [item for item in items if item.published >= cutoff]

        logger.info(
            f"Period filter [{period}]: {len(filtered)}/{len(items)} items "
            f"(cutoff: {cutoff.strftime('%Y-%m-%d %H:%M')} UTC)"
        )

        if len(filtered) == 0 and len(items) > 0:
            oldest = min(items, key=lambda x: x.published)
            newest = max(items, key=lambda x: x.published)
            logger.warning(
                f"All items filtered out! Article date range: "
                f"{oldest.published.strftime('%Y-%m-%d %H:%M')} ~ "
                f"{newest.published.strftime('%Y-%m-%d %H:%M')} UTC"
            )

        return filtered

    def group_by_category(
        self,
        items: list[FeedItem],
    ) -> dict[str, list[FeedItem]]:
        """
        Group items by category.

        Args:
            items: List of feed items.

        Returns:
            Dictionary mapping category to list of items.
        """
        groups: dict[str, list[FeedItem]] = {}
        for item in items:
            if item.category not in groups:
                groups[item.category] = []
            groups[item.category].append(item)
        return groups

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "FeedFetcher":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
