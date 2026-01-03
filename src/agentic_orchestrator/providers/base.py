"""
Base provider interface for LLM adapters.

Defines common interfaces, exceptions, and retry logic for all providers.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str = "", model: str = ""):
        super().__init__(message)
        self.provider = provider
        self.model = model


class RateLimitError(ProviderError):
    """
    Exception raised when rate limit is hit.

    Includes retry timing information when available.
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        model: str = "",
        retry_after: Optional[float] = None,
        reset_time: Optional[float] = None,
    ):
        super().__init__(message, provider, model)
        self.retry_after = retry_after  # Seconds to wait
        self.reset_time = reset_time  # Unix timestamp when limit resets


class QuotaExhaustedError(ProviderError):
    """
    Exception raised when API quota is exhausted.

    This typically requires user intervention (payment, key update).
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        model: str = "",
        quota_type: str = "unknown",
    ):
        super().__init__(message, provider, model)
        self.quota_type = quota_type  # e.g., "tokens", "requests", "billing"


class ModelNotAvailableError(ProviderError):
    """Exception raised when a model is not available."""

    pass


class AuthenticationError(ProviderError):
    """Exception raised for authentication failures."""

    pass


@dataclass
class Message:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class CompletionResponse:
    """Response from a completion request."""

    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 5,
        max_wait_seconds: int = 3600,
        initial_backoff: float = 10.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_retries = max_retries
        self.max_wait_seconds = max_wait_seconds
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implements common retry logic and error handling.
    Subclasses must implement the actual API calls.
    """

    provider_name: str = "base"

    def __init__(
        self,
        model: str,
        fallback_model: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        dry_run: bool = False,
    ):
        """
        Initialize provider.

        Args:
            model: Primary model to use.
            fallback_model: Fallback model if primary fails.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        self.model = model
        self.fallback_model = fallback_model
        self.retry_config = retry_config or RetryConfig()
        self.dry_run = dry_run
        self._current_model = model

    @abstractmethod
    def _make_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """
        Make the actual API request.

        Subclasses must implement this method.

        Args:
            messages: List of messages.
            model: Model to use.
            **kwargs: Additional provider-specific arguments.

        Returns:
            CompletionResponse with the result.

        Raises:
            RateLimitError: When rate limited.
            QuotaExhaustedError: When quota is exhausted.
            ProviderError: For other errors.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available (API key set, etc.).

        Returns:
            True if provider can be used.
        """
        pass

    def complete(
        self,
        messages: List[Message],
        **kwargs,
    ) -> CompletionResponse:
        """
        Get a completion with retry logic and fallback.

        Args:
            messages: List of messages.
            **kwargs: Additional arguments.

        Returns:
            CompletionResponse with the result.

        Raises:
            RateLimitError: When rate limit exceeded and max retries hit.
            QuotaExhaustedError: When quota is exhausted.
            ProviderError: For other errors after retries.
        """
        if self.dry_run:
            return self._dry_run_response(messages)

        # Try primary model
        try:
            return self._complete_with_retry(messages, self.model, **kwargs)
        except (RateLimitError, ModelNotAvailableError) as e:
            if self.fallback_model:
                logger.warning(
                    f"{self.provider_name}: Primary model {self.model} failed, "
                    f"trying fallback {self.fallback_model}: {e}"
                )
                return self._complete_with_retry(messages, self.fallback_model, **kwargs)
            raise

    def _complete_with_retry(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """
        Complete with retry logic for rate limits.

        Args:
            messages: List of messages.
            model: Model to use.
            **kwargs: Additional arguments.

        Returns:
            CompletionResponse with the result.
        """
        self._current_model = model
        last_error = None
        backoff = self.retry_config.initial_backoff

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return self._make_request(messages, model, **kwargs)

            except RateLimitError as e:
                last_error = e

                # Determine wait time
                wait_time = self._calculate_wait_time(e, backoff)

                if wait_time > self.retry_config.max_wait_seconds:
                    logger.error(
                        f"{self.provider_name}: Wait time {wait_time}s exceeds "
                        f"max {self.retry_config.max_wait_seconds}s, giving up"
                    )
                    raise

                if attempt < self.retry_config.max_retries:
                    logger.warning(
                        f"{self.provider_name}: Rate limited, waiting {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1})"
                    )
                    time.sleep(wait_time)
                    backoff *= self.retry_config.backoff_multiplier
                else:
                    logger.error(
                        f"{self.provider_name}: Max retries exceeded for rate limit"
                    )
                    raise

            except QuotaExhaustedError:
                # Don't retry quota errors - they need user intervention
                raise

            except ProviderError as e:
                # For other errors, retry with backoff
                last_error = e
                if attempt < self.retry_config.max_retries:
                    logger.warning(
                        f"{self.provider_name}: Request failed, retrying in {backoff}s: {e}"
                    )
                    time.sleep(backoff)
                    backoff *= self.retry_config.backoff_multiplier
                else:
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise ProviderError(f"Unknown error in {self.provider_name}")

    def _calculate_wait_time(self, error: RateLimitError, default_backoff: float) -> float:
        """Calculate wait time from rate limit error or use default backoff."""
        if error.retry_after is not None:
            return error.retry_after
        if error.reset_time is not None:
            wait = error.reset_time - time.time()
            return max(0, wait)
        return default_backoff

    def _dry_run_response(self, messages: List[Message]) -> CompletionResponse:
        """Generate a dry-run response for testing."""
        return CompletionResponse(
            content=f"[DRY RUN] {self.provider_name} response for {len(messages)} messages",
            model=self.model,
            provider=self.provider_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="dry_run",
        )

    def chat(self, user_message: str, system_message: Optional[str] = None) -> str:
        """
        Simple chat interface.

        Args:
            user_message: User's message.
            system_message: Optional system message.

        Returns:
            Assistant's response content.
        """
        messages = []
        if system_message:
            messages.append(Message(role="system", content=system_message))
        messages.append(Message(role="user", content=user_message))

        response = self.complete(messages)
        return response.content
