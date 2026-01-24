"""
Signal aggregator for collecting and processing signals from all adapters.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

from ..adapters.base import BaseAdapter, AdapterResult, SignalData
from ..adapters.rss import RSSAdapter
from ..adapters.github_events import GitHubEventsAdapter
from ..adapters.onchain import OnChainAdapter
from ..adapters.social import SocialMediaAdapter
from ..adapters.news import NewsAPIAdapter
from ..db.connection import db
from ..db.models import Signal
from ..db.repositories import SignalRepository
from .scorer import SignalScorer

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    Aggregates signals from all adapters.

    Features:
    - Parallel fetching from all adapters
    - Deduplication
    - Scoring
    - Database persistence
    """

    def __init__(
        self,
        adapters: Optional[List[BaseAdapter]] = None,
        scorer: Optional[SignalScorer] = None,
    ):
        self.adapters = adapters or self._default_adapters()
        self.scorer = scorer or SignalScorer()
        self._last_collection: Optional[datetime] = None

    def _default_adapters(self) -> List[BaseAdapter]:
        """Create default adapters."""
        return [
            RSSAdapter(),
            GitHubEventsAdapter(),
            OnChainAdapter(),
            SocialMediaAdapter(),
            NewsAPIAdapter(),
        ]

    async def collect_all(
        self,
        save_to_db: bool = True,
        deduplicate: bool = True,
    ) -> List[SignalData]:
        """
        Collect signals from all enabled adapters.

        Args:
            save_to_db: Whether to save signals to database
            deduplicate: Whether to remove duplicate signals

        Returns:
            List of collected signals
        """
        all_signals: List[SignalData] = []
        results: List[AdapterResult] = []

        # Fetch from all adapters in parallel
        tasks = []
        for adapter in self.adapters:
            if adapter.is_enabled():
                tasks.append(adapter.fetch_with_retry())

        adapter_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in adapter_results:
            if isinstance(result, AdapterResult):
                results.append(result)
                if result.success:
                    all_signals.extend(result.signals)
            elif isinstance(result, Exception):
                print(f"Adapter error: {result}")

        # Deduplicate
        if deduplicate:
            all_signals = self._deduplicate(all_signals)

        # Score signals
        all_signals = self.scorer.score_batch(all_signals)

        # Sort by score
        all_signals.sort(key=lambda s: getattr(s, 'score', 0) if hasattr(s, 'score') else 0, reverse=True)

        # Save to database
        if save_to_db:
            await self._save_to_db(all_signals)

        self._last_collection = datetime.utcnow()

        return all_signals

    async def collect_from_adapter(
        self,
        adapter_name: str,
        save_to_db: bool = True,
    ) -> List[SignalData]:
        """Collect signals from a specific adapter."""
        for adapter in self.adapters:
            if adapter.name == adapter_name and adapter.is_enabled():
                result = await adapter.fetch_with_retry()

                if result.success:
                    signals = self.scorer.score_batch(result.signals)

                    if save_to_db:
                        await self._save_to_db(signals)

                    return signals

        return []

    def _deduplicate(self, signals: List[SignalData]) -> List[SignalData]:
        """Remove duplicate signals based on content hash."""
        seen: Dict[str, SignalData] = {}

        for signal in signals:
            # Create hash from title and URL
            content = f"{signal.title}:{signal.url or ''}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            if content_hash not in seen:
                seen[content_hash] = signal

        return list(seen.values())

    async def _translate_to_korean(self, text: str) -> Optional[str]:
        """Translate text to Korean using Claude API."""
        if not text or len(text.strip()) < 5:
            return None

        try:
            from ..llm.router import HybridLLMRouter

            router = HybridLLMRouter()
            prompt = f"""Translate the following English text to Korean.
Keep the translation natural and concise. Only return the Korean translation, nothing else.

Text: {text}

Korean translation:"""

            response = await router.route_request(
                prompt=prompt,
                prefer_claude=True,  # Use Claude for better translation quality
                max_tokens=500,
            )

            if response and response.content:
                return response.content.strip()

        except Exception as e:
            logger.warning(f"Translation failed: {e}")

        return None

    async def _save_to_db(self, signals: List[SignalData]) -> int:
        """Save signals to database with Korean translations."""
        saved_count = 0

        with db.session() as session:
            repo = SignalRepository(session)

            for signal in signals:
                try:
                    # Check if signal already exists (by content hash)
                    existing = session.query(Signal).filter(
                        Signal.id == signal.id
                    ).first()

                    if not existing:
                        # Translate title and summary to Korean
                        title_ko = await self._translate_to_korean(signal.title)
                        summary_ko = await self._translate_to_korean(signal.summary) if signal.summary else None

                        repo.create({
                            "id": signal.id,
                            "source": signal.source,
                            "category": signal.category,
                            "title": signal.title,
                            "title_ko": title_ko,
                            "summary": signal.summary,
                            "summary_ko": summary_ko,
                            "url": signal.url,
                            "raw_data": signal.raw_data,
                            "score": getattr(signal, 'score', 0.0),
                            "topics": signal.metadata.get("topics", []),
                            "collected_at": signal.collected_at,
                        })
                        saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving signal: {e}")

        return saved_count

    async def get_recent_signals(
        self,
        hours: int = 24,
        limit: int = 100,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Signal]:
        """Get recent signals from database."""
        with db.session() as session:
            repo = SignalRepository(session)
            return repo.get_recent(
                hours=hours,
                limit=limit,
                source=source,
                category=category,
                min_score=min_score
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all adapters."""
        health = {
            "status": "healthy",
            "last_collection": self._last_collection.isoformat() if self._last_collection else None,
            "adapters": {}
        }

        for adapter in self.adapters:
            adapter_health = await adapter.health_check()
            health["adapters"][adapter.name] = adapter_health

            if not adapter_health.get("enabled", True):
                continue

            if "error" in str(adapter_health.get("api_status", "")):
                health["status"] = "degraded"

        return health

    def get_adapter(self, name: str) -> Optional[BaseAdapter]:
        """Get adapter by name."""
        for adapter in self.adapters:
            if adapter.name == name:
                return adapter
        return None

    def add_adapter(self, adapter: BaseAdapter) -> None:
        """Add a new adapter."""
        self.adapters.append(adapter)

    def remove_adapter(self, name: str) -> bool:
        """Remove an adapter by name."""
        for i, adapter in enumerate(self.adapters):
            if adapter.name == name:
                self.adapters.pop(i)
                return True
        return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        with db.session() as session:
            repo = SignalRepository(session)
            return {
                "adapters_count": len(self.adapters),
                "enabled_adapters": len([a for a in self.adapters if a.is_enabled()]),
                "signals_by_source": repo.count_by_source(),
                "signals_by_category": repo.count_by_category(),
                "last_collection": self._last_collection.isoformat() if self._last_collection else None,
            }
