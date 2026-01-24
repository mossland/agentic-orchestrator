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

    # Sentiment keywords for analysis
    sentiment_positive: Set[str] = None
    sentiment_negative: Set[str] = None

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

        if self.sentiment_positive is None:
            self.sentiment_positive = {
                # English positive
                "bullish", "growth", "success", "breakthrough", "innovation",
                "partnership", "launch", "upgrade", "milestone", "achievement",
                "profit", "rally", "surge", "soar", "boom", "record high",
                "adoption", "integration", "expansion", "funding", "investment",
                "promising", "exciting", "revolutionary", "game-changing",
                # Korean positive
                "성공", "상승", "호재", "돌파", "혁신", "파트너십", "출시",
                "성장", "수익", "달성", "급등", "신고가", "도입", "확장",
            }

        if self.sentiment_negative is None:
            self.sentiment_negative = {
                # English negative
                "crash", "hack", "scam", "fraud", "rug pull", "exploit",
                "vulnerability", "failure", "loss", "dump", "plunge", "collapse",
                "bankrupt", "lawsuit", "investigation", "warning", "risk",
                "fud", "bear", "correction", "selloff", "panic", "fear",
                "shutdown", "suspend", "delist", "ban", "sanctions",
                # Korean negative
                "폭락", "해킹", "사기", "러그풀", "취약점", "실패", "손실",
                "파산", "소송", "조사", "경고", "위험", "하락", "매도",
                "정지", "상폐", "제재", "금지",
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

        # Sentiment adjustment
        sentiment_adjustment = self._score_sentiment(signal)
        score += sentiment_adjustment

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

    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text using keyword-based detection.

        Args:
            text: Text to analyze

        Returns:
            (sentiment, confidence)
            - sentiment: 'positive', 'negative', or 'neutral'
            - confidence: 0.0-1.0 indicating how confident the classification is
        """
        text_lower = text.lower()

        pos_count = 0
        neg_count = 0

        # Count positive keywords
        for keyword in self.config.sentiment_positive:
            if keyword in text_lower:
                pos_count += 1

        # Count negative keywords
        for keyword in self.config.sentiment_negative:
            if keyword in text_lower:
                neg_count += 1

        total = pos_count + neg_count

        if total == 0:
            return 'neutral', 0.5

        # Calculate sentiment
        if neg_count > pos_count + 1:
            # Strongly negative
            confidence = min(0.9, 0.5 + (neg_count - pos_count) * 0.1)
            return 'negative', confidence
        elif pos_count > neg_count + 1:
            # Strongly positive
            confidence = min(0.9, 0.5 + (pos_count - neg_count) * 0.1)
            return 'positive', confidence
        else:
            # Mixed or neutral
            return 'neutral', 0.5

    def _score_sentiment(self, signal: SignalData) -> float:
        """
        Score adjustment based on sentiment.

        Positive sentiment gets slight boost, negative gets slight penalty.
        """
        text = f"{signal.title} {signal.summary or ''}"
        sentiment, confidence = self._analyze_sentiment(text)

        # Store sentiment in metadata for later use
        signal.metadata["sentiment"] = sentiment
        signal.metadata["sentiment_confidence"] = confidence

        if sentiment == 'positive':
            return 0.05 * confidence  # Slight boost for positive
        elif sentiment == 'negative':
            return -0.03 * confidence  # Slight penalty for negative
        else:
            return 0.0

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

        # Analyze sentiment
        sentiment, sentiment_confidence = self._analyze_sentiment(text)

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
            "sentiment": {
                "value": sentiment,
                "confidence": sentiment_confidence,
                "adjustment": self._score_sentiment(signal),
            },
            "final_score": self.score(signal),
        }

        # Find matching keywords
        for keyword in self.config.positive_keywords:
            if keyword in text:
                explanation["keywords_found"].append(keyword)

        for keyword in self.config.mossland_keywords:
            if keyword in text:
                explanation["mossland_keywords_found"].append(keyword)

        # Find sentiment keywords
        explanation["sentiment_positive_found"] = [
            kw for kw in self.config.sentiment_positive if kw in text
        ]
        explanation["sentiment_negative_found"] = [
            kw for kw in self.config.sentiment_negative if kw in text
        ]

        return explanation
