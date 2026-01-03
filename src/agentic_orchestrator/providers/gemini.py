"""
Google Gemini provider adapter.

Handles API calls to Google's Gemini models with proper error handling.
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

# Try to import google-generativeai
try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    google_exceptions = None


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider.

    Used for fast agentic tasks and secondary review.
    Supports latest preview models and fallback configuration.
    """

    provider_name = "gemini"

    # Default models
    DEFAULT_MODEL = "gemini-3-flash-preview"
    DEFAULT_FALLBACK = "gemini-3-pro-preview"
    SECONDARY_FALLBACK = "gemini-2.5-pro"

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        dry_run: bool = False,
    ):
        """
        Initialize Gemini provider.

        Args:
            model: Model to use. Defaults to gemini-3-flash-preview.
            fallback_model: Fallback model. Defaults to gemini-3-pro-preview.
            api_key: Gemini API key. Defaults to GEMINI_API_KEY env var.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            fallback_model=fallback_model or self.DEFAULT_FALLBACK,
            retry_config=retry_config,
            dry_run=dry_run,
        )
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.secondary_fallback = self.SECONDARY_FALLBACK
        self._configured = False

    def _ensure_configured(self) -> None:
        """Ensure the Gemini API is configured."""
        if self._configured:
            return

        if not GEMINI_AVAILABLE:
            raise ProviderError(
                "google-generativeai package not installed. Run: pip install google-generativeai",
                provider=self.provider_name,
            )

        if not self.api_key:
            raise AuthenticationError(
                "Gemini API key not set. Set GEMINI_API_KEY environment variable.",
                provider=self.provider_name,
            )

        genai.configure(api_key=self.api_key)
        self._configured = True

    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return GEMINI_AVAILABLE and bool(self.api_key)

    def _make_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request to Gemini API."""
        self._ensure_configured()

        try:
            # Create model instance
            gemini_model = genai.GenerativeModel(model)

            # Convert messages to Gemini format
            # Gemini uses a different format - combine into chat history
            system_instruction = None
            chat_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_instruction = msg.content
                elif msg.role == "user":
                    chat_messages.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "assistant":
                    chat_messages.append({"role": "model", "parts": [msg.content]})

            # If there's a system message, prepend it to first user message
            if system_instruction and chat_messages:
                first_user_idx = next(
                    (i for i, m in enumerate(chat_messages) if m["role"] == "user"),
                    None
                )
                if first_user_idx is not None:
                    original_content = chat_messages[first_user_idx]["parts"][0]
                    chat_messages[first_user_idx]["parts"][0] = (
                        f"{system_instruction}\n\n{original_content}"
                    )

            # Start chat and send last message
            if len(chat_messages) > 1:
                chat = gemini_model.start_chat(history=chat_messages[:-1])
                last_message = chat_messages[-1]["parts"][0]
                response = chat.send_message(last_message)
            else:
                # Single message case
                content = chat_messages[0]["parts"][0] if chat_messages else ""
                response = gemini_model.generate_content(content)

            # Extract response
            response_text = ""
            if response.text:
                response_text = response.text
            elif response.parts:
                response_text = "".join(part.text for part in response.parts if part.text)

            # Get usage if available
            usage = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(
                        response.usage_metadata, "candidates_token_count", 0
                    ),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            return CompletionResponse(
                content=response_text,
                model=model,
                provider=self.provider_name,
                usage=usage,
                finish_reason="stop",
                raw_response=response,
            )

        except Exception as e:
            self._handle_error(e, model)
            raise  # Should not reach here

    def _handle_error(self, error: Exception, model: str) -> None:
        """Convert Gemini exceptions to our exception types."""
        error_str = str(error).lower()

        # Check for specific Google API errors
        if GEMINI_AVAILABLE and google_exceptions:
            if isinstance(error, google_exceptions.ResourceExhausted):
                raise RateLimitError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

            if isinstance(error, google_exceptions.PermissionDenied):
                if "quota" in error_str:
                    raise QuotaExhaustedError(
                        str(error),
                        provider=self.provider_name,
                        model=model,
                        quota_type="quota",
                    )
                raise AuthenticationError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

            if isinstance(error, google_exceptions.NotFound):
                raise ModelNotAvailableError(
                    str(error),
                    provider=self.provider_name,
                    model=model,
                )

        # String-based error detection
        if "rate limit" in error_str or "resource exhausted" in error_str:
            raise RateLimitError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        if "quota" in error_str or "billing" in error_str:
            raise QuotaExhaustedError(
                str(error),
                provider=self.provider_name,
                model=model,
                quota_type="quota",
            )

        if "api key" in error_str or "authentication" in error_str:
            raise AuthenticationError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        if "model" in error_str and "not found" in error_str:
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

    def complete(
        self,
        messages: List[Message],
        **kwargs,
    ) -> CompletionResponse:
        """
        Get a completion with retry logic and multi-level fallback.

        Gemini supports a secondary fallback (gemini-2.5-pro) in addition
        to the primary fallback.
        """
        if self.dry_run:
            return self._dry_run_response(messages)

        # Try primary model
        try:
            return self._complete_with_retry(messages, self.model, **kwargs)
        except (RateLimitError, ModelNotAvailableError) as e:
            logger.warning(
                f"{self.provider_name}: Primary model {self.model} failed: {e}"
            )

            # Try primary fallback
            if self.fallback_model:
                try:
                    logger.info(f"Trying fallback model: {self.fallback_model}")
                    return self._complete_with_retry(messages, self.fallback_model, **kwargs)
                except (RateLimitError, ModelNotAvailableError) as e2:
                    logger.warning(
                        f"{self.provider_name}: Fallback {self.fallback_model} failed: {e2}"
                    )

                    # Try secondary fallback
                    if self.secondary_fallback:
                        logger.info(f"Trying secondary fallback: {self.secondary_fallback}")
                        return self._complete_with_retry(
                            messages, self.secondary_fallback, **kwargs
                        )
                    raise
            raise


def create_gemini_provider(
    model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    dry_run: bool = False,
) -> GeminiProvider:
    """
    Factory function to create Gemini provider with config defaults.

    Args:
        model: Override model.
        fallback_model: Override fallback model.
        dry_run: Enable dry run mode.

    Returns:
        Configured GeminiProvider instance.
    """
    from ..utils.config import load_config

    config = load_config()

    return GeminiProvider(
        model=model or config.gemini_model,
        fallback_model=fallback_model or config.gemini_model_fallback,
        retry_config=RetryConfig(
            max_retries=config.rate_limit_max_retries,
            max_wait_seconds=config.rate_limit_max_wait,
        ),
        dry_run=dry_run or config.dry_run,
    )
