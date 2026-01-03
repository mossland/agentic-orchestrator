"""Tests for LLM provider adapters."""

import pytest

from agentic_orchestrator.providers.base import (
    Message,
    CompletionResponse,
    RetryConfig,
    RateLimitError,
    QuotaExhaustedError,
    ProviderError,
)
from agentic_orchestrator.providers.openai import OpenAIProvider
from agentic_orchestrator.providers.gemini import GeminiProvider
from agentic_orchestrator.providers.claude import ClaudeProvider


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_system_message(self):
        """Test system message."""
        msg = Message(role="system", content="You are helpful")
        assert msg.role == "system"


class TestCompletionResponse:
    """Tests for CompletionResponse dataclass."""

    def test_response_creation(self):
        """Test creating a response."""
        response = CompletionResponse(
            content="Hello, world!",
            model="gpt-4",
            provider="openai",
        )
        assert response.content == "Hello, world!"
        assert response.model == "gpt-4"
        assert response.provider == "openai"

    def test_response_with_usage(self):
        """Test response with usage data."""
        response = CompletionResponse(
            content="Test",
            model="gpt-4",
            provider="openai",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )
        assert response.usage["total_tokens"] == 30


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.max_wait_seconds == 3600
        assert config.initial_backoff == 10.0
        assert config.backoff_multiplier == 2.0

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=3,
            max_wait_seconds=1800,
            initial_backoff=5.0,
            backoff_multiplier=1.5,
        )
        assert config.max_retries == 3
        assert config.max_wait_seconds == 1800


class TestExceptions:
    """Tests for custom exceptions."""

    def test_provider_error(self):
        """Test ProviderError."""
        error = ProviderError("Something went wrong", provider="openai", model="gpt-4")
        assert "Something went wrong" in str(error)
        assert error.provider == "openai"
        assert error.model == "gpt-4"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError(
            "Rate limited",
            provider="openai",
            model="gpt-4",
            retry_after=60.0,
        )
        assert error.retry_after == 60.0
        assert error.reset_time is None

    def test_rate_limit_error_with_reset(self):
        """Test RateLimitError with reset time."""
        error = RateLimitError(
            "Rate limited",
            provider="openai",
            model="gpt-4",
            reset_time=1704067200.0,  # Some timestamp
        )
        assert error.reset_time == 1704067200.0

    def test_quota_exhausted_error(self):
        """Test QuotaExhaustedError."""
        error = QuotaExhaustedError(
            "Quota exceeded",
            provider="openai",
            model="gpt-4",
            quota_type="billing",
        )
        assert error.quota_type == "billing"


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_dry_run_mode(self):
        """Test dry run mode."""
        provider = OpenAIProvider(dry_run=True)
        messages = [Message(role="user", content="Hello")]

        response = provider.complete(messages)

        assert "DRY RUN" in response.content
        assert response.provider == "openai"
        assert response.finish_reason == "dry_run"

    def test_is_available_without_key(self):
        """Test availability check without API key."""
        provider = OpenAIProvider(api_key=None)
        # Will only be available if there's a key in env
        # This test just verifies the method runs
        _ = provider.is_available()

    def test_default_models(self):
        """Test default model configuration."""
        provider = OpenAIProvider(dry_run=True)
        assert provider.model == OpenAIProvider.DEFAULT_MODEL
        assert provider.fallback_model == OpenAIProvider.DEFAULT_FALLBACK


class TestGeminiProvider:
    """Tests for Gemini provider."""

    def test_dry_run_mode(self):
        """Test dry run mode."""
        provider = GeminiProvider(dry_run=True)
        messages = [Message(role="user", content="Hello")]

        response = provider.complete(messages)

        assert "DRY RUN" in response.content
        assert response.provider == "gemini"

    def test_default_models(self):
        """Test default model configuration."""
        provider = GeminiProvider(dry_run=True)
        assert provider.model == GeminiProvider.DEFAULT_MODEL
        assert provider.fallback_model == GeminiProvider.DEFAULT_FALLBACK
        assert provider.secondary_fallback == GeminiProvider.SECONDARY_FALLBACK


class TestClaudeProvider:
    """Tests for Claude provider."""

    def test_dry_run_mode(self):
        """Test dry run mode."""
        provider = ClaudeProvider(dry_run=True)
        messages = [Message(role="user", content="Hello")]

        response = provider.complete(messages)

        assert "DRY RUN" in response.content
        assert response.provider == "claude"

    def test_default_models(self):
        """Test default model configuration."""
        provider = ClaudeProvider(dry_run=True)
        assert provider.model == ClaudeProvider.DEFAULT_MODEL
        assert provider.fallback_model == ClaudeProvider.DEFAULT_FALLBACK

    def test_api_model_mapping(self):
        """Test API model name mapping."""
        assert "opus" in ClaudeProvider.API_MODELS
        assert "sonnet" in ClaudeProvider.API_MODELS

    def test_chat_method(self):
        """Test simple chat interface."""
        provider = ClaudeProvider(dry_run=True)
        response = provider.chat("Hello", system_message="Be helpful")

        assert "DRY RUN" in response
