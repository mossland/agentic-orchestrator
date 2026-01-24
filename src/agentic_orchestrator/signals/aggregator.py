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
from ..adapters.twitter import TwitterAdapter
from ..adapters.discord import DiscordAdapter
from ..adapters.lens import LensAdapter
from ..adapters.farcaster import FarcasterAdapter
from ..adapters.coingecko import CoingeckoAdapter
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
            # Core adapters
            RSSAdapter(),
            GitHubEventsAdapter(),
            OnChainAdapter(),  # Now includes DEX volume and whale alerts
            SocialMediaAdapter(),  # Reddit + basic Twitter
            NewsAPIAdapter(),
            # Web3 social adapters (new in v0.5.0)
            TwitterAdapter(),  # Enhanced Twitter/X with Nitter pool
            DiscordAdapter(),  # Discord announcements
            LensAdapter(),  # Lens Protocol
            FarcasterAdapter(),  # Farcaster/Warpcast
            # Market data adapter (new in v0.5.0)
            CoingeckoAdapter(),  # Market trends, gainers/losers, trending coins
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

    def _validate_signal_content(self, signal: SignalData) -> tuple[bool, str]:
        """
        Validate signal content quality.

        Checks:
        - Minimum title length
        - Language (Korean or English only)
        - Spam/ad pattern detection

        Returns:
            (is_valid, reason)
        """
        title = signal.title or ''
        summary = signal.summary or ''

        # Minimum title length check (10 characters)
        if len(title.strip()) < 10:
            return False, "title_too_short"

        # Language validation (Korean or English)
        if not self._is_valid_language(title):
            return False, "invalid_language"

        # Spam/ad pattern detection
        spam_patterns = [
            'click here', 'buy now', 'free money', 'giveaway',
            '무료', '할인', '이벤트', '경품', 'airdrop claim',
            '100x guaranteed', 'limited time', 'act now',
            'send btc', 'send eth', 'dm for',
        ]
        title_lower = title.lower()
        summary_lower = summary.lower()

        for pattern in spam_patterns:
            if pattern in title_lower or pattern in summary_lower:
                return False, f"spam_detected:{pattern}"

        # Check for excessive caps (more than 70% uppercase in title)
        alpha_chars = [c for c in title if c.isalpha()]
        if alpha_chars:
            upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if upper_ratio > 0.7 and len(title) > 20:
                return False, "excessive_caps"

        return True, "valid"

    def _is_valid_language(self, text: str) -> bool:
        """
        Check if text is in Korean or English.

        Uses simple character range detection.
        """
        if not text:
            return False

        # Count character types
        korean_count = 0
        english_count = 0
        other_count = 0

        for char in text:
            if '\uAC00' <= char <= '\uD7A3' or '\u1100' <= char <= '\u11FF':
                # Korean syllables or Jamo
                korean_count += 1
            elif 'a' <= char.lower() <= 'z':
                english_count += 1
            elif char.isalpha():
                other_count += 1

        total_alpha = korean_count + english_count + other_count
        if total_alpha == 0:
            return True  # No alphabetic chars (numbers, symbols) - allow

        # Allow if majority is Korean or English
        korean_english_ratio = (korean_count + english_count) / total_alpha
        return korean_english_ratio >= 0.7

    def _is_semantic_duplicate(
        self,
        new_signal: SignalData,
        existing_signals: List[SignalData],
        threshold: float = 0.7,
    ) -> bool:
        """
        Check if signal is semantically duplicate of existing signals.

        Uses Jaccard similarity on tokenized titles.

        Args:
            new_signal: Signal to check
            existing_signals: Existing signals to compare against
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if duplicate found
        """
        if not existing_signals:
            return False

        new_title = new_signal.title or ''
        new_tokens = set(new_title.lower().split())

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
            'to', 'of', 'and', 'in', 'on', 'for', 'with', 'at',
            '의', '을', '를', '이', '가', '은', '는', '에', '와', '과',
        }
        new_tokens = new_tokens - stop_words

        if len(new_tokens) < 3:
            return False  # Too few tokens to compare meaningfully

        for existing in existing_signals:
            existing_title = existing.title or ''
            existing_tokens = set(existing_title.lower().split()) - stop_words

            if len(existing_tokens) < 3:
                continue

            # Calculate Jaccard similarity
            intersection = len(new_tokens & existing_tokens)
            union = len(new_tokens | existing_tokens)

            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    logger.debug(
                        f"Semantic duplicate found: '{new_title[:50]}' "
                        f"similar to '{existing_title[:50]}' ({similarity:.2f})"
                    )
                    return True

        return False

    def _deduplicate(self, signals: List[SignalData]) -> List[SignalData]:
        """
        Remove duplicate signals using both hash and semantic similarity.

        Two-pass deduplication:
        1. Exact match via content hash
        2. Semantic similarity via Jaccard on titles
        """
        # Phase 1: Hash-based deduplication
        seen_hashes: Dict[str, SignalData] = {}

        for signal in signals:
            content = f"{signal.title}:{signal.url or ''}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            if content_hash not in seen_hashes:
                seen_hashes[content_hash] = signal

        hash_deduped = list(seen_hashes.values())
        logger.info(f"Hash dedup: {len(signals)} -> {len(hash_deduped)}")

        # Phase 2: Content validation
        validated: List[SignalData] = []
        filtered_count = 0

        for signal in hash_deduped:
            is_valid, reason = self._validate_signal_content(signal)
            if is_valid:
                validated.append(signal)
            else:
                filtered_count += 1
                logger.debug(f"Filtered signal: {reason} - '{signal.title[:50]}'")

        logger.info(f"Content validation: {len(hash_deduped)} -> {len(validated)} (filtered {filtered_count})")

        # Phase 3: Semantic deduplication
        final_signals: List[SignalData] = []
        semantic_dupes = 0

        for signal in validated:
            if not self._is_semantic_duplicate(signal, final_signals, threshold=0.7):
                final_signals.append(signal)
            else:
                semantic_dupes += 1

        logger.info(f"Semantic dedup: {len(validated)} -> {len(final_signals)} (dupes: {semantic_dupes})")

        return final_signals

    async def _ensure_bilingual(self, text: str) -> tuple[str, Optional[str]]:
        """
        Ensure text is available in both English and Korean.

        Uses ContentTranslator for bidirectional translation:
        - Korean text -> translates to English, keeps Korean
        - English text -> keeps English, translates to Korean

        Returns:
            Tuple of (english_text, korean_text)
        """
        if not text or len(text.strip()) < 5:
            return (text or "", None)

        try:
            from ..translation.translator import ContentTranslator

            translator = ContentTranslator()
            english_text, korean_text = await translator.ensure_bilingual(text)
            return (english_text or text, korean_text)

        except Exception as e:
            logger.warning(f"Translation failed: {e}")

        return (text, None)

    async def _save_to_db(self, signals: List[SignalData], translate: bool = False) -> int:
        """
        Save signals to database.

        Args:
            signals: List of signals to save
            translate: Whether to translate signals (default: False for performance)
                       Translation is time-consuming (~15s per field), so it's disabled
                       by default. Translations are more useful for trends/ideas/plans.

        Returns:
            Number of signals saved
        """
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
                        title_ko = None
                        summary_ko = None

                        # Optional translation (disabled by default for performance)
                        if translate:
                            try:
                                title_en, title_ko = await self._ensure_bilingual(signal.title)
                                if signal.summary:
                                    _, summary_ko = await self._ensure_bilingual(signal.summary)
                            except Exception as e:
                                logger.warning(f"Translation failed for signal: {e}")

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
