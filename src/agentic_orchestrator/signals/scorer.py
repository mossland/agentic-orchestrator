"""
Signal scorer for relevance and importance scoring.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
import re

from ..adapters.base import SignalData


@dataclass
class ScoringConfig:
    """Configuration for signal scoring."""

    # Category weights
    category_weights: Dict[str, float] = None

    # Keyword weights (positive impact)
    positive_keywords: Dict[str, float] = None

    # Mossland-specific keywords (extra boost)
    mossland_keywords: Set[str] = None

    # Recency weight (signals lose value over time)
    recency_decay_hours: int = 72

    def __post_init__(self):
        if self.category_weights is None:
            self.category_weights = {
                "crypto": 1.2,
                "ai": 1.1,
                "dev": 1.0,
                "finance": 0.9,
                "security": 1.0,
                "other": 0.8,
            }

        if self.positive_keywords is None:
            self.positive_keywords = {
                # Web3/Crypto
                "ethereum": 0.15,
                "solana": 0.12,
                "polygon": 0.12,
                "defi": 0.15,
                "nft": 0.10,
                "web3": 0.15,
                "token": 0.10,
                "blockchain": 0.12,
                "smart contract": 0.12,
                "dao": 0.10,
                "metaverse": 0.15,
                "gaming": 0.10,

                # AI/ML
                "llm": 0.12,
                "gpt": 0.10,
                "claude": 0.10,
                "openai": 0.10,
                "anthropic": 0.10,
                "ai agent": 0.15,
                "machine learning": 0.10,
                "neural": 0.08,

                # Development
                "launch": 0.10,
                "release": 0.08,
                "open source": 0.10,
                "sdk": 0.08,
                "api": 0.08,
                "developer": 0.08,

                # Business
                "startup": 0.10,
                "funding": 0.12,
                "investment": 0.10,
                "partnership": 0.10,
                "million": 0.08,
                "billion": 0.10,
            }

        if self.mossland_keywords is None:
            self.mossland_keywords = {
                "mossland",
                "moc",
                "moss coin",
                "luniverse",
                "mossverse",
                "ar",
                "augmented reality",
                "virtual land",
                "real estate",
                "location based",
            }


class SignalScorer:
    """
    Scores signals based on relevance and importance.

    Scoring factors:
    - Category weight
    - Keyword presence
    - Mossland relevance
    - Source reliability
    - Engagement metrics (if available)
    - Recency
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()

    def score(self, signal: SignalData) -> float:
        """
        Score a single signal.

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        # Category weight
        category_weight = self.config.category_weights.get(signal.category, 0.8)
        score *= category_weight

        # Keyword scoring
        text = f"{signal.title} {signal.summary or ''}".lower()
        keyword_boost = self._score_keywords(text)
        score += keyword_boost

        # Mossland relevance boost
        mossland_boost = self._score_mossland_relevance(text)
        score += mossland_boost

        # Source reliability
        source_boost = self._score_source(signal)
        score += source_boost

        # Engagement metrics (if available)
        engagement_boost = self._score_engagement(signal)
        score += engagement_boost

        # Normalize to 0-1 range
        score = max(0.0, min(1.0, score))

        return round(score, 4)

    def score_batch(self, signals: List[SignalData]) -> List[SignalData]:
        """Score multiple signals and add score attribute."""
        for signal in signals:
            signal.metadata["score"] = self.score(signal)
            # Add score as attribute for sorting
            object.__setattr__(signal, 'score', signal.metadata["score"])
        return signals

    def _score_keywords(self, text: str) -> float:
        """Score based on keyword presence."""
        boost = 0.0
        text_lower = text.lower()

        for keyword, weight in self.config.positive_keywords.items():
            if keyword in text_lower:
                boost += weight

        # Cap keyword boost
        return min(0.3, boost)

    def _score_mossland_relevance(self, text: str) -> float:
        """Score based on Mossland-specific keywords."""
        boost = 0.0
        text_lower = text.lower()

        for keyword in self.config.mossland_keywords:
            if keyword in text_lower:
                boost += 0.2  # Strong boost for Mossland relevance

        return min(0.4, boost)

    def _score_source(self, signal: SignalData) -> float:
        """Score based on source reliability."""
        source_scores = {
            "rss": 0.05,
            "github": 0.08,
            "onchain": 0.10,
            "social": 0.03,
            "news": 0.05,
        }

        base_boost = source_scores.get(signal.source, 0.0)

        # Specific source boosts
        raw_data = signal.raw_data or {}

        # GitHub trending/releases are more valuable
        if signal.source == "github":
            if raw_data.get("type") == "release":
                base_boost += 0.05
            if raw_data.get("stars", 0) > 1000:
                base_boost += 0.03

        # High-score HN posts
        if raw_data.get("type") == "hackernews":
            score = raw_data.get("score", 0)
            if score > 100:
                base_boost += 0.05
            if score > 500:
                base_boost += 0.05

        # Reddit high-engagement posts
        if raw_data.get("type") == "reddit":
            reddit_score = raw_data.get("score", 0)
            if reddit_score > 100:
                base_boost += 0.03
            if reddit_score > 500:
                base_boost += 0.05

        return min(0.15, base_boost)

    def _score_engagement(self, signal: SignalData) -> float:
        """Score based on engagement metrics."""
        boost = 0.0
        raw_data = signal.raw_data or {}

        # Stars (GitHub)
        stars = raw_data.get("stars", 0)
        if stars > 100:
            boost += 0.02
        if stars > 1000:
            boost += 0.03
        if stars > 10000:
            boost += 0.05

        # Comments
        comments = raw_data.get("num_comments", 0) or raw_data.get("comments", 0) or raw_data.get("descendants", 0)
        if comments > 10:
            boost += 0.02
        if comments > 50:
            boost += 0.03
        if comments > 200:
            boost += 0.05

        # Votes/Score (Reddit, HN)
        score = raw_data.get("score", 0)
        if score > 100:
            boost += 0.02
        if score > 500:
            boost += 0.03

        # Funding amounts (OnChain)
        funding = raw_data.get("amount", 0)
        if funding > 10:  # $10M+
            boost += 0.05
        if funding > 50:  # $50M+
            boost += 0.05

        return min(0.15, boost)

    def get_top_signals(
        self,
        signals: List[SignalData],
        limit: int = 20,
        min_score: float = 0.3,
    ) -> List[SignalData]:
        """Get top signals above minimum score."""
        scored = self.score_batch(signals)
        filtered = [s for s in scored if s.metadata.get("score", 0) >= min_score]
        filtered.sort(key=lambda s: s.metadata.get("score", 0), reverse=True)
        return filtered[:limit]

    def explain_score(self, signal: SignalData) -> Dict[str, Any]:
        """Explain how a signal was scored."""
        text = f"{signal.title} {signal.summary or ''}".lower()

        explanation = {
            "base_score": 0.5,
            "category": {
                "value": signal.category,
                "weight": self.config.category_weights.get(signal.category, 0.8),
            },
            "keywords_found": [],
            "mossland_keywords_found": [],
            "source_boost": self._score_source(signal),
            "engagement_boost": self._score_engagement(signal),
            "final_score": self.score(signal),
        }

        # Find matching keywords
        for keyword in self.config.positive_keywords:
            if keyword in text:
                explanation["keywords_found"].append(keyword)

        for keyword in self.config.mossland_keywords:
            if keyword in text:
                explanation["mossland_keywords_found"].append(keyword)

        return explanation
