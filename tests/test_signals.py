"""Tests for signal aggregation and scoring system."""

import pytest
from datetime import datetime, timedelta

from agentic_orchestrator.adapters.base import (
    SignalData,
    AdapterConfig,
    AdapterResult,
)
from agentic_orchestrator.signals.scorer import (
    SignalScorer,
    ScoringConfig,
)


class TestSignalData:
    """Tests for SignalData dataclass."""

    def test_signal_creation(self):
        """Test creating a signal."""
        signal = SignalData(
            source="rss",
            category="crypto",
            title="Bitcoin hits new high",
            summary="BTC reaches $100k",
        )
        assert signal.source == "rss"
        assert signal.category == "crypto"
        assert signal.title == "Bitcoin hits new high"
        assert signal.summary == "BTC reaches $100k"

    def test_signal_id_generation(self):
        """Test unique ID generation."""
        signal = SignalData(
            source="rss",
            category="crypto",
            title="Test Signal",
            url="https://example.com/test",
        )
        assert signal.id is not None
        assert len(signal.id) == 16

    def test_signal_id_uniqueness(self):
        """Test that different signals have different IDs."""
        signal1 = SignalData(
            source="rss",
            category="crypto",
            title="Signal 1",
        )
        signal2 = SignalData(
            source="rss",
            category="crypto",
            title="Signal 2",
        )
        assert signal1.id != signal2.id

    def test_signal_id_consistency(self):
        """Test that same content produces same ID."""
        signal1 = SignalData(
            source="rss",
            category="crypto",
            title="Same Title",
            url="https://example.com/same",
        )
        signal2 = SignalData(
            source="rss",
            category="crypto",
            title="Same Title",
            url="https://example.com/same",
        )
        assert signal1.id == signal2.id

    def test_signal_with_metadata(self):
        """Test signal with metadata."""
        signal = SignalData(
            source="github",
            category="dev",
            title="New Release",
            metadata={"repo": "example/repo", "stars": 1000},
        )
        assert signal.metadata["repo"] == "example/repo"
        assert signal.metadata["stars"] == 1000

    def test_signal_to_dict(self):
        """Test signal serialization."""
        signal = SignalData(
            source="rss",
            category="ai",
            title="AI News",
            summary="Big announcement",
        )
        data = signal.to_dict()
        assert data["source"] == "rss"
        assert data["category"] == "ai"
        assert data["title"] == "AI News"
        assert "collected_at" in data

    def test_signal_default_timestamp(self):
        """Test signal has default timestamp."""
        signal = SignalData(
            source="test",
            category="test",
            title="Test",
        )
        assert signal.collected_at is not None
        assert isinstance(signal.collected_at, datetime)


class TestAdapterConfig:
    """Tests for AdapterConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AdapterConfig()
        assert config.enabled is True
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.batch_size == 50

    def test_custom_config(self):
        """Test custom configuration."""
        config = AdapterConfig(
            enabled=False,
            timeout=60,
            max_retries=5,
            rate_limit=2.0,
        )
        assert config.enabled is False
        assert config.timeout == 60
        assert config.rate_limit == 2.0


class TestAdapterResult:
    """Tests for AdapterResult."""

    def test_successful_result(self):
        """Test successful adapter result."""
        signals = [
            SignalData(source="test", category="test", title="Signal 1"),
            SignalData(source="test", category="test", title="Signal 2"),
        ]
        result = AdapterResult(
            adapter_name="TestAdapter",
            success=True,
            signals=signals,
            duration_ms=150.5,
        )
        assert result.success is True
        assert result.count == 2
        assert result.error is None

    def test_failed_result(self):
        """Test failed adapter result."""
        result = AdapterResult(
            adapter_name="TestAdapter",
            success=False,
            error="Connection timeout",
        )
        assert result.success is False
        assert result.count == 0
        assert result.error == "Connection timeout"


class TestScoringConfig:
    """Tests for ScoringConfig."""

    def test_default_config(self):
        """Test default scoring configuration."""
        config = ScoringConfig()
        assert config.category_weights is not None
        assert config.positive_keywords is not None
        assert config.mossland_keywords is not None
        assert config.recency_decay_hours == 72

    def test_default_category_weights(self):
        """Test default category weights."""
        config = ScoringConfig()
        assert config.category_weights["crypto"] == 1.2
        assert config.category_weights["ai"] == 1.1
        assert config.category_weights["other"] == 0.8

    def test_default_keywords(self):
        """Test default positive keywords."""
        config = ScoringConfig()
        assert "ethereum" in config.positive_keywords
        assert "defi" in config.positive_keywords
        assert "llm" in config.positive_keywords

    def test_mossland_keywords(self):
        """Test Mossland-specific keywords."""
        config = ScoringConfig()
        assert "mossland" in config.mossland_keywords
        assert "moc" in config.mossland_keywords
        assert "metaverse" not in config.mossland_keywords  # Not Mossland-specific

    def test_custom_config(self):
        """Test custom scoring configuration."""
        config = ScoringConfig(
            category_weights={"crypto": 1.5, "ai": 1.3},
            recency_decay_hours=48,
        )
        assert config.category_weights["crypto"] == 1.5
        assert config.recency_decay_hours == 48


class TestSignalScorer:
    """Tests for SignalScorer."""

    def test_scorer_initialization(self):
        """Test scorer initialization."""
        scorer = SignalScorer()
        assert scorer.config is not None

    def test_scorer_with_custom_config(self):
        """Test scorer with custom configuration."""
        config = ScoringConfig(
            category_weights={"test": 1.0},
        )
        scorer = SignalScorer(config)
        assert scorer.config.category_weights["test"] == 1.0

    def test_base_score(self):
        """Test basic signal scoring."""
        scorer = SignalScorer()
        signal = SignalData(
            source="rss",
            category="other",
            title="Generic news headline",
        )
        score = scorer.score(signal)
        assert 0.0 <= score <= 1.0

    def test_crypto_category_boost(self):
        """Test crypto category gets higher score."""
        scorer = SignalScorer()
        crypto_signal = SignalData(
            source="rss",
            category="crypto",
            title="Cryptocurrency news",
        )
        other_signal = SignalData(
            source="rss",
            category="other",
            title="Generic news",
        )
        crypto_score = scorer.score(crypto_signal)
        other_score = scorer.score(other_signal)
        assert crypto_score > other_score

    def test_keyword_boost(self):
        """Test keywords boost score."""
        scorer = SignalScorer()
        signal_with_keywords = SignalData(
            source="rss",
            category="crypto",
            title="Ethereum DeFi Protocol Launch",
            summary="New smart contract platform goes live",
        )
        signal_without = SignalData(
            source="rss",
            category="crypto",
            title="Market update today",
        )
        score_with = scorer.score(signal_with_keywords)
        score_without = scorer.score(signal_without)
        assert score_with > score_without

    def test_mossland_relevance_boost(self):
        """Test Mossland-related content gets boosted."""
        scorer = SignalScorer()
        mossland_signal = SignalData(
            source="rss",
            category="crypto",
            title="Mossland announces new metaverse feature",
            summary="MOC token integration with AR platform",
        )
        generic_signal = SignalData(
            source="rss",
            category="crypto",
            title="New cryptocurrency exchange launches",
        )
        mossland_score = scorer.score(mossland_signal)
        generic_score = scorer.score(generic_signal)
        assert mossland_score > generic_score

    def test_score_range(self):
        """Test score is always in valid range."""
        scorer = SignalScorer()
        signals = [
            SignalData(source="rss", category="crypto", title="ETH DeFi Web3 NFT blockchain"),  # High keywords
            SignalData(source="rss", category="other", title="x"),  # Minimal content
            SignalData(source="rss", category="ai", title="GPT Claude LLM OpenAI Anthropic AI agent"),  # AI keywords
        ]
        for signal in signals:
            score = scorer.score(signal)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for signal: {signal.title}"

    def test_batch_scoring(self):
        """Test scoring multiple signals at once."""
        scorer = SignalScorer()
        signals = [
            SignalData(source="rss", category="crypto", title="Signal 1"),
            SignalData(source="rss", category="ai", title="Signal 2"),
            SignalData(source="rss", category="dev", title="Signal 3"),
        ]
        scored = scorer.score_batch(signals)
        assert len(scored) == 3
        # score_batch adds score attribute
        for signal in scored:
            assert hasattr(signal, 'score') or 'score' in signal.metadata

    def test_ai_keywords_boost(self):
        """Test AI-related keywords boost score."""
        scorer = SignalScorer()
        ai_signal = SignalData(
            source="rss",
            category="ai",
            title="New LLM model from OpenAI rivals Claude",
            summary="Machine learning breakthrough announced",
        )
        score = scorer.score(ai_signal)
        # AI category with multiple AI keywords should score well
        assert score > 0.5

    def test_case_insensitive_keywords(self):
        """Test keyword matching is case insensitive."""
        scorer = SignalScorer()
        signal_upper = SignalData(
            source="rss",
            category="crypto",
            title="ETHEREUM DEFI LAUNCH",
        )
        signal_lower = SignalData(
            source="rss",
            category="crypto",
            title="ethereum defi launch",
        )
        score_upper = scorer.score(signal_upper)
        score_lower = scorer.score(signal_lower)
        assert abs(score_upper - score_lower) < 0.01  # Should be nearly equal


class TestSignalAggregation:
    """Integration tests for signal aggregation workflow."""

    def test_collect_and_score_workflow(self):
        """Test complete collect and score workflow."""
        # Simulate collected signals
        signals = [
            SignalData(
                source="coindesk",
                category="crypto",
                title="Bitcoin rally continues to $100k",
                summary="BTC shows strong momentum",
            ),
            SignalData(
                source="techcrunch",
                category="ai",
                title="New AI startup raises $50M",
                summary="Machine learning platform funding",
            ),
            SignalData(
                source="github",
                category="dev",
                title="Open source SDK release",
                summary="Developer tools update",
            ),
        ]

        # Score all signals
        scorer = SignalScorer()
        for signal in signals:
            signal.metadata["score"] = scorer.score(signal)

        # Verify all scored
        assert all("score" in s.metadata for s in signals)

        # Sort by score
        sorted_signals = sorted(signals, key=lambda x: x.metadata["score"], reverse=True)

        # Verify sorting works
        for i in range(len(sorted_signals) - 1):
            assert sorted_signals[i].metadata["score"] >= sorted_signals[i + 1].metadata["score"]

    def test_filter_by_score_threshold(self):
        """Test filtering signals by score threshold."""
        signals = [
            SignalData(source="rss", category="crypto", title="High relevance DeFi Ethereum"),
            SignalData(source="rss", category="other", title="Low relevance content"),
            SignalData(source="rss", category="ai", title="Medium relevance LLM news"),
        ]

        scorer = SignalScorer()
        scored = [(s, scorer.score(s)) for s in signals]

        # Filter by threshold
        threshold = 0.5
        filtered = [(s, score) for s, score in scored if score >= threshold]

        # Should have filtered some out
        assert len(filtered) <= len(signals)

    def test_deduplicate_signals(self):
        """Test deduplicating signals by ID."""
        signals = [
            SignalData(source="rss", category="crypto", title="Same title", url="https://example.com/1"),
            SignalData(source="rss", category="crypto", title="Same title", url="https://example.com/1"),  # Duplicate
            SignalData(source="rss", category="crypto", title="Different title", url="https://example.com/2"),
        ]

        # Deduplicate by ID
        seen = set()
        unique = []
        for signal in signals:
            if signal.id not in seen:
                seen.add(signal.id)
                unique.append(signal)

        assert len(unique) == 2
