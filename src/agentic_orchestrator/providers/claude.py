"""
Claude provider adapter.

Supports two modes:
1. Claude Code CLI: Invokes the local claude CLI tool
2. Anthropic API: Direct API calls for environments without CLI

The CLI mode is preferred for development tasks as it has access
to full Claude Code capabilities.
"""

import os
import subprocess
import json
from typing import List, Optional, Any
from pathlib import Path

from .base import (
    BaseProvider,
    Message,
    CompletionResponse,
    RetryConfig,
    RateLimitError,
    QuotaExhaustedError,
    AuthenticationError,
    ProviderError,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Try to import anthropic
try:
    import anthropic
    from anthropic import Anthropic, APIError, RateLimitError as AnthropicRateLimitError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    APIError = Exception
    AnthropicRateLimitError = Exception


class ClaudeCodeExecutor:
    """
    Executor for Claude Code CLI commands.

    Handles invoking the claude CLI tool with proper arguments
    and parsing its output.
    """

    def __init__(
        self,
        model: str = "opus",
        working_dir: Optional[Path] = None,
        timeout: int = 600,
    ):
        """
        Initialize Claude Code executor.

        Args:
            model: Model to use (opus, sonnet).
            working_dir: Working directory for commands.
            timeout: Command timeout in seconds.
        """
        self.model = model
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if claude CLI is available."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def execute(
        self,
        prompt: str,
        print_output: bool = False,
    ) -> tuple[str, int]:
        """
        Execute a prompt using Claude Code CLI.

        Args:
            prompt: The prompt to send to Claude.
            print_output: Whether to print output in real-time.

        Returns:
            Tuple of (output, return_code).
        """
        cmd = [
            "claude",
            "--model", self.model,
            "--print",  # Print mode for non-interactive use
            "--output-format", "text",
            "-p", prompt,
        ]

        logger.debug(f"Executing Claude Code: {' '.join(cmd[:4])}...")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            output = result.stdout
            if result.stderr:
                logger.debug(f"Claude Code stderr: {result.stderr}")

            return output, result.returncode

        except subprocess.TimeoutExpired:
            logger.error(f"Claude Code timed out after {self.timeout}s")
            raise ProviderError(
                f"Claude Code timed out after {self.timeout} seconds",
                provider="claude-code",
            )

        except FileNotFoundError:
            raise ProviderError(
                "Claude Code CLI not found. Install it: https://claude.ai/code",
                provider="claude-code",
            )

    def execute_with_context(
        self,
        prompt: str,
        context_files: Optional[List[str]] = None,
    ) -> tuple[str, int]:
        """
        Execute a prompt with file context.

        Args:
            prompt: The prompt to send.
            context_files: List of file paths to include as context.

        Returns:
            Tuple of (output, return_code).
        """
        # Build prompt with file references
        if context_files:
            file_refs = "\n".join(f"- {f}" for f in context_files)
            full_prompt = f"{prompt}\n\nRelevant files:\n{file_refs}"
        else:
            full_prompt = prompt

        return self.execute(full_prompt)


class ClaudeProvider(BaseProvider):
    """
    Claude provider supporting both CLI and API modes.

    Automatically selects the best available mode:
    - CLI mode if claude command is available (preferred for development)
    - API mode if ANTHROPIC_API_KEY is set
    """

    provider_name = "claude"

    # Default models
    DEFAULT_MODEL = "opus"
    DEFAULT_FALLBACK = "sonnet"

    # API model mappings
    API_MODELS = {
        "opus": "claude-opus-4-5-20251101",
        "sonnet": "claude-sonnet-4-20250514",
    }

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        api_key: Optional[str] = None,
        prefer_cli: bool = True,
        working_dir: Optional[Path] = None,
        retry_config: Optional[RetryConfig] = None,
        dry_run: bool = False,
    ):
        """
        Initialize Claude provider.

        Args:
            model: Model to use (opus, sonnet).
            fallback_model: Fallback model.
            api_key: Anthropic API key for API mode.
            prefer_cli: Prefer CLI mode if available.
            working_dir: Working directory for CLI commands.
            retry_config: Retry configuration.
            dry_run: If True, don't make actual API calls.
        """
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            fallback_model=fallback_model or self.DEFAULT_FALLBACK,
            retry_config=retry_config,
            dry_run=dry_run,
        )
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.prefer_cli = prefer_cli
        self.working_dir = working_dir or Path.cwd()

        self._cli_executor: Optional[ClaudeCodeExecutor] = None
        self._api_client: Optional[Any] = None
        self._mode: Optional[str] = None

    @property
    def mode(self) -> str:
        """Get the active mode (cli or api)."""
        if self._mode is None:
            self._mode = self._determine_mode()
        return self._mode

    def _determine_mode(self) -> str:
        """Determine which mode to use."""
        if self.prefer_cli:
            executor = ClaudeCodeExecutor(
                model=self.model,
                working_dir=self.working_dir,
            )
            if executor.is_available():
                self._cli_executor = executor
                logger.info("Using Claude Code CLI mode")
                return "cli"

        if ANTHROPIC_AVAILABLE and self.api_key:
            logger.info("Using Claude API mode")
            return "api"

        # Neither available
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError(
                "Neither Claude CLI nor anthropic package available. "
                "Install Claude Code or run: pip install anthropic",
                provider=self.provider_name,
            )

        raise AuthenticationError(
            "Claude CLI not available and ANTHROPIC_API_KEY not set.",
            provider=self.provider_name,
        )

    @property
    def cli_executor(self) -> ClaudeCodeExecutor:
        """Get CLI executor."""
        if self._cli_executor is None:
            self._cli_executor = ClaudeCodeExecutor(
                model=self.model,
                working_dir=self.working_dir,
            )
        return self._cli_executor

    @property
    def api_client(self):
        """Get API client."""
        if self._api_client is None:
            if not ANTHROPIC_AVAILABLE:
                raise ProviderError(
                    "anthropic package not installed. Run: pip install anthropic",
                    provider=self.provider_name,
                )
            if not self.api_key:
                raise AuthenticationError(
                    "ANTHROPIC_API_KEY not set.",
                    provider=self.provider_name,
                )
            self._api_client = Anthropic(api_key=self.api_key)
        return self._api_client

    def is_available(self) -> bool:
        """Check if Claude provider is available."""
        try:
            _ = self.mode
            return True
        except (ProviderError, AuthenticationError):
            return False

    def _make_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request using the appropriate mode."""
        if self.mode == "cli":
            return self._make_cli_request(messages, model, **kwargs)
        else:
            return self._make_api_request(messages, model, **kwargs)

    def _make_cli_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request using Claude Code CLI."""
        # Update executor model
        self.cli_executor.model = model

        # Build prompt from messages
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(msg.content)
            elif msg.role == "assistant":
                prompt_parts.append(f"Previous response: {msg.content}")

        prompt = "\n\n".join(prompt_parts)

        # Execute
        output, return_code = self.cli_executor.execute(prompt)

        if return_code != 0:
            self._handle_cli_error(output, return_code, model)

        return CompletionResponse(
            content=output.strip(),
            model=model,
            provider=f"{self.provider_name}-cli",
            finish_reason="stop" if return_code == 0 else "error",
        )

    def _handle_cli_error(self, output: str, return_code: int, model: str) -> None:
        """Handle CLI errors."""
        output_lower = output.lower()

        if "rate limit" in output_lower:
            raise RateLimitError(
                f"Claude Code rate limited: {output}",
                provider=self.provider_name,
                model=model,
            )

        if "quota" in output_lower or "billing" in output_lower:
            raise QuotaExhaustedError(
                f"Claude quota issue: {output}",
                provider=self.provider_name,
                model=model,
            )

        raise ProviderError(
            f"Claude Code error (exit {return_code}): {output}",
            provider=self.provider_name,
            model=model,
        )

    def _make_api_request(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> CompletionResponse:
        """Make request using Anthropic API."""
        try:
            # Convert model name to API model
            api_model = self.API_MODELS.get(model, model)

            # Separate system message
            system = None
            api_messages = []

            for msg in messages:
                if msg.role == "system":
                    system = msg.content
                else:
                    api_messages.append({
                        "role": msg.role,
                        "content": msg.content,
                    })

            # Make request
            create_kwargs = {
                "model": api_model,
                "messages": api_messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            if system:
                create_kwargs["system"] = system

            response = self.api_client.messages.create(**create_kwargs)

            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": (
                        response.usage.input_tokens + response.usage.output_tokens
                    ),
                }

            return CompletionResponse(
                content=content,
                model=response.model,
                provider=f"{self.provider_name}-api",
                usage=usage,
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            self._handle_api_error(e, model)
            raise

    def _handle_api_error(self, error: Exception, model: str) -> None:
        """Handle API errors."""
        error_str = str(error).lower()

        if ANTHROPIC_AVAILABLE and isinstance(error, AnthropicRateLimitError):
            retry_after = None
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

        if "rate" in error_str and "limit" in error_str:
            raise RateLimitError(
                str(error),
                provider=self.provider_name,
                model=model,
            )

        if "quota" in error_str or "insufficient" in error_str:
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

        raise ProviderError(
            str(error),
            provider=self.provider_name,
            model=model,
        )

    def execute_task(
        self,
        task: str,
        context_files: Optional[List[str]] = None,
    ) -> str:
        """
        Execute a development task using Claude Code CLI.

        This is the preferred method for development-related tasks
        as it leverages Claude Code's full capabilities.

        Args:
            task: Task description/prompt.
            context_files: Files to include as context.

        Returns:
            Task output.

        Raises:
            ProviderError: If CLI mode is not available.
        """
        if self.mode != "cli":
            raise ProviderError(
                "execute_task requires Claude Code CLI mode",
                provider=self.provider_name,
            )

        output, return_code = self.cli_executor.execute_with_context(
            task, context_files
        )

        if return_code != 0:
            self._handle_cli_error(output, return_code, self.model)

        return output.strip()


def create_claude_provider(
    model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    prefer_cli: bool = True,
    dry_run: bool = False,
) -> ClaudeProvider:
    """
    Factory function to create Claude provider with config defaults.

    Args:
        model: Override model.
        fallback_model: Override fallback model.
        prefer_cli: Prefer CLI mode if available.
        dry_run: Enable dry run mode.

    Returns:
        Configured ClaudeProvider instance.
    """
    from ..utils.config import load_config

    config = load_config()

    return ClaudeProvider(
        model=model or config.claude_model,
        fallback_model=fallback_model or config.claude_model_fallback,
        prefer_cli=prefer_cli,
        retry_config=RetryConfig(
            max_retries=config.rate_limit_max_retries,
            max_wait_seconds=config.rate_limit_max_wait,
        ),
        dry_run=dry_run or config.dry_run,
    )
