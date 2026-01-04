"""
Configuration utilities for the Agentic Orchestrator.

Handles loading configuration from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Optional
import yaml

from dotenv import load_dotenv


# Load .env file if present
load_dotenv()


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.
        required: Raise error if not set.

    Returns:
        Environment variable value.

    Raises:
        ValueError: If required and not set.
    """
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable not set: {key}")
    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get a boolean environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Boolean value.
    """
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def get_env_int(key: str, default: int = 0) -> int:
    """
    Get an integer environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Integer value.
    """
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Config:
    """
    Configuration manager for the orchestrator.

    Loads configuration from config.yaml and environment variables.
    Environment variables take precedence over file configuration.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml. Defaults to ./config.yaml.
        """
        self.config_path = config_path or Path("config.yaml")
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f) or {}

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a nested configuration value.

        Args:
            *keys: Path to the configuration value (e.g., "models", "claude", "default").
            default: Default value if not found.

        Returns:
            Configuration value.
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    # Model Configuration
    @property
    def claude_model(self) -> str:
        """Get the Claude model to use."""
        return get_env("CLAUDE_MODEL") or self.get("models", "claude", "default", default="opus")

    @property
    def claude_model_fallback(self) -> str:
        """Get the Claude fallback model."""
        return self.get("models", "claude", "fallback", default="sonnet")

    @property
    def openai_model(self) -> str:
        """Get the OpenAI model to use."""
        # Check for pinned version first
        pinned = get_env("OPENAI_MODEL_PINNED") or self.get("models", "openai", "pinned")
        if pinned:
            return pinned
        return get_env("OPENAI_MODEL") or self.get(
            "models", "openai", "default", default="gpt-5.2-chat-latest"
        )

    @property
    def openai_model_fallback(self) -> str:
        """Get the OpenAI fallback model."""
        return get_env("OPENAI_MODEL_FALLBACK") or self.get(
            "models", "openai", "fallback", default="gpt-5.2"
        )

    @property
    def gemini_model(self) -> str:
        """Get the Gemini model to use."""
        # Check for pinned version first
        pinned = get_env("GEMINI_MODEL_PINNED") or self.get("models", "gemini", "pinned")
        if pinned:
            return pinned
        return get_env("GEMINI_MODEL") or self.get(
            "models", "gemini", "default", default="gemini-3-flash-preview"
        )

    @property
    def gemini_model_fallback(self) -> str:
        """Get the Gemini fallback model."""
        return get_env("GEMINI_MODEL_FALLBACK") or self.get(
            "models", "gemini", "fallback", default="gemini-3-pro-preview"
        )

    # Limit Configuration
    @property
    def planning_max_iterations(self) -> int:
        """Get maximum planning iterations."""
        return get_env_int("PLANNING_MAX_ITERATIONS") or self.get(
            "limits", "planning_max_iterations", default=3
        )

    @property
    def dev_max_iterations(self) -> int:
        """Get maximum development iterations."""
        return get_env_int("DEV_MAX_ITERATIONS") or self.get(
            "limits", "dev_max_iterations", default=5
        )

    @property
    def rate_limit_max_retries(self) -> int:
        """Get maximum rate limit retries."""
        return get_env_int("RATE_LIMIT_MAX_RETRIES") or self.get(
            "limits", "rate_limit", "max_retries", default=5
        )

    @property
    def rate_limit_max_wait(self) -> int:
        """Get maximum rate limit wait time in seconds."""
        return get_env_int("RATE_LIMIT_MAX_WAIT_SECONDS") or self.get(
            "limits", "rate_limit", "max_wait_seconds", default=3600
        )

    @property
    def loop_max_steps(self) -> int:
        """Get maximum steps in loop mode."""
        return get_env_int("LOOP_MAX_STEPS") or self.get(
            "limits", "loop", "max_steps", default=100
        )

    @property
    def loop_delay(self) -> int:
        """Get delay between loop iterations in seconds."""
        return get_env_int("LOOP_DELAY_SECONDS") or self.get(
            "limits", "loop", "delay_seconds", default=10
        )

    # Debate Configuration
    @property
    def debate_enabled(self) -> bool:
        """Check if multi-agent debate mode is enabled for plan generation."""
        return get_env_bool("DEBATE_ENABLED", default=True) and self.get(
            "debate", "enabled", default=True
        )

    @property
    def debate_max_rounds(self) -> int:
        """Get maximum number of debate rounds."""
        return get_env_int("DEBATE_MAX_ROUNDS") or self.get(
            "debate", "max_rounds", default=5
        )

    @property
    def debate_min_rounds(self) -> int:
        """Get minimum debate rounds before early termination allowed."""
        return get_env_int("DEBATE_MIN_ROUNDS") or self.get(
            "debate", "min_rounds", default=1
        )

    @property
    def debate_require_all_approval(self) -> bool:
        """Check if all reviewers must approve for early termination."""
        return get_env_bool("DEBATE_REQUIRE_ALL_APPROVAL", default=False) and self.get(
            "debate", "require_all_approval", default=False
        )

    # Quality Configuration
    @property
    def required_review_score(self) -> float:
        """Get required review score."""
        return float(self.get("quality", "required_review_score", default=7.0))

    @property
    def min_test_coverage(self) -> int:
        """Get minimum test coverage percentage."""
        return self.get("quality", "min_test_coverage", default=70)

    # Dry Run
    @property
    def dry_run(self) -> bool:
        """Check if running in dry-run mode."""
        return get_env_bool("DRY_RUN", default=False)

    # Git Configuration
    @property
    def git_auto_push(self) -> bool:
        """Check if auto-push is enabled."""
        return self.get("git", "auto_push", default=False)

    @property
    def git_user_name(self) -> str:
        """Get Git user name."""
        return get_env("GIT_USER_NAME") or "Agentic Orchestrator"

    @property
    def git_user_email(self) -> str:
        """Get Git user email."""
        return get_env("GIT_USER_EMAIL") or "orchestrator@mossland.org"


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load and return configuration.

    Args:
        config_path: Path to config.yaml.

    Returns:
        Config instance.
    """
    return Config(config_path)


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing."""

    def __init__(self, missing: list, message: str = None):
        self.missing = missing
        self.message = message or f"Missing required environment variables: {', '.join(missing)}"
        super().__init__(self.message)


def validate_backlog_environment() -> dict:
    """
    Validate environment variables required for backlog workflow.

    Checks for:
    - GitHub credentials (GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO)
    - At least one LLM provider API key

    Returns:
        Dict with validation status and details.

    Raises:
        EnvironmentValidationError: If required variables are missing.
    """
    result = {
        "valid": True,
        "github": {"valid": True, "missing": []},
        "llm": {"valid": True, "missing": [], "available": []},
        "warnings": [],
    }

    # Check GitHub credentials
    github_required = ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO"]
    github_missing = [var for var in github_required if not os.environ.get(var)]

    if github_missing:
        result["valid"] = False
        result["github"]["valid"] = False
        result["github"]["missing"] = github_missing

    # Check LLM providers (at least one must be available)
    llm_providers = {
        "ANTHROPIC_API_KEY": "Claude",
        "OPENAI_API_KEY": "OpenAI",
        "GEMINI_API_KEY": "Gemini",
    }

    available_llm = []
    for env_var, provider_name in llm_providers.items():
        if os.environ.get(env_var):
            available_llm.append(provider_name)

    result["llm"]["available"] = available_llm

    if not available_llm:
        result["valid"] = False
        result["llm"]["valid"] = False
        result["llm"]["missing"] = list(llm_providers.keys())

    # Raise error if validation failed
    if not result["valid"]:
        all_missing = result["github"]["missing"] + (
            result["llm"]["missing"] if not result["llm"]["available"] else []
        )

        error_parts = []
        if result["github"]["missing"]:
            error_parts.append(
                f"GitHub: {', '.join(result['github']['missing'])}"
            )
        if not result["llm"]["available"]:
            error_parts.append(
                "LLM: At least one of ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY"
            )

        raise EnvironmentValidationError(
            missing=all_missing,
            message=(
                f"Missing required environment variables:\n"
                f"  - {chr(10) + '  - '.join(error_parts)}\n\n"
                f"See .env.example for configuration details."
            ),
        )

    return result


def validate_environment_for_command(command: str) -> dict:
    """
    Validate environment for a specific CLI command.

    Args:
        command: The command name (e.g., "backlog", "init", "step").

    Returns:
        Dict with validation status.

    Raises:
        EnvironmentValidationError: If required variables are missing.
    """
    if command in ("backlog", "backlog run", "backlog generate", "backlog process"):
        return validate_backlog_environment()

    # Other commands may have different requirements
    return {"valid": True}
