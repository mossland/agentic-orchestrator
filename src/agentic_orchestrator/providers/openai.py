"""
OpenAI provider adapter.

Handles API calls to OpenAI's GPT models with proper error handling.
"""

import os
from typing import List, Optional, Any

from .base import (
    BaseProvider,
    Message,
    CompletionResponse,
    RetryConfig,
    RateLimitError,
    QuotaExhaustedError,
    AuthenticationError,
    ModelNotAvailableError,
    ProviderError,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Try to import openai
try:
    import openai
    from openai import OpenAI, APIError, RateLimitError as OpenAIRateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    APIError = Exception
    OpenAIRateLimitError = Exception


class OpenAIProvider(BaseProvider):
    """
    OpenAI GPT provider.

    Used primarily for independent code review and evaluation.
    Supports latest models and fallback configuration.
    """

    provider_name = "openai"

    # Default models
    DEFAULT_MODEL = "gpt-5.2-chat-latest"
    DEFAULT_FALLBACK = "gpt-5.2"

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        dry_run: bool = False,
    ):
        """
        Initialize OpenAI provider.

        Args:
            model: Model to use. Defaults to gpt-5.2-chat-latest.
            fallback_model: Fallback model. Defaults to gpt-5.2.
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            fallback_model=fallback_model or self.DEFAULT_FALLBACK,
            retry_config=retry_config,
            dry_run=dry_run,
        )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client: Optional[Any] = None

    @property
    def client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            if not OPENAI_AVAILABLE:
                raise ProviderError(
                    "OpenAI package not installed. Run: pip install openai",
                    provider=self.provider_name,
                )
            if not self.api_key:
                raise AuthenticationError(
                    "OpenAI API key not set. Set OPENAI_API_KEY environment variable.",
                    provider=self.provider_name,
                )
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return OPENAI_AVAILABLE and bool(self.api_key)

    def _make_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request to OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            # Make request
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                **kwargs,
            )

            # Extract response
            choice = response.choices[0]
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return CompletionResponse(
                content=choice.message.content or "",
                model=response.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=choice.finish_reason,
                raw_response=response,
            )

        except Exception as e:
            self._handle_error(e, model)
            raise  # Should not reach here

    def _handle_error(self, error: Exception, model: str) -> None:
        """Convert OpenAI exceptions to our exception types."""
        error_str = str(error).lower()

        # Rate limit errors
        if OPENAI_AVAILABLE and isinstance(error, OpenAIRateLimitError):
            retry_after = None
            # Try to extract retry-after from headers or message
            if hasattr(error, "response") and error.response:
                retry_after_header = error.response.headers.get("retry-after")
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        pass

            raise RateLimitError(
                str(error),
                provider=self.provider_name,
                model=model,
                retry_after=retry_after,
            )

        # Quota exhausted
        if "insufficient_quota" in error_str or "quota" in error_str:
            raise QuotaExhaustedError(
                str(error),
                provider=self.provider_name,
                model=model,
                quota_type="billing",
            )

        # Authentication errors
        if "invalid api key" in error_str or "authentication" in error_str:
            raise AuthenticationError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        # Model not available
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            raise ModelNotAvailableError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        # Generic error
        raise ProviderError(
            str(error),
            provider=self.provider_name,
            model=model,
        )


def create_openai_provider(
    model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    dry_run: bool = False,
) -> OpenAIProvider:
    """
    Factory function to create OpenAI provider with config defaults.

    Args:
        model: Override model.
        fallback_model: Override fallback model.
        dry_run: Enable dry run mode.

    Returns:
        Configured OpenAIProvider instance.
    """
    from ..utils.config import load_config

    config = load_config()

    return OpenAIProvider(
        model=model or config.openai_model,
        fallback_model=fallback_model or config.openai_model_fallback,
        retry_config=RetryConfig(
            max_retries=config.rate_limit_max_retries,
            max_wait_seconds=config.rate_limit_max_wait,
        ),
        dry_run=dry_run or config.dry_run,
    )
