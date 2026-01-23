"""
LLM hierarchy and tier management.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ModelTier(Enum):
    """Model tier levels."""
    FREE = "free"           # Local models (Ollama)
    BUDGET = "budget"       # Cheap API models
    STANDARD = "standard"   # Standard API models
    PREMIUM = "premium"     # Premium API models


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    provider: str
    tier: ModelTier
    context_size: int
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float  # USD
    capabilities: List[str]
    recommended_for: List[str]


class LLMHierarchy:
    """
    Manages LLM model hierarchy and selection.

    Tier 1 (Free - Local):
    - Ollama models
    - No cost, unlimited usage
    - Good for most tasks

    Tier 2 (Paid - API):
    - Claude, OpenAI, Gemini
    - Used for critical/final outputs
    - Budget controlled
    """

    # Local models (Tier 1 - Free)
    LOCAL_MODELS: Dict[str, ModelConfig] = {
        "llama3.3:70b": ModelConfig(
            name="llama3.3:70b",
            provider="ollama",
            tier=ModelTier.FREE,
            context_size=131072,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            capabilities=["reasoning", "analysis", "moderation", "planning"],
            recommended_for=["moderation", "final_evaluation", "complex_reasoning"]
        ),
        "qwen2.5:32b": ModelConfig(
            name="qwen2.5:32b",
            provider="ollama",
            tier=ModelTier.FREE,
            context_size=32768,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            capabilities=["reasoning", "analysis", "coding", "evaluation"],
            recommended_for=["evaluation", "convergence", "technical_review"]
        ),
        "phi4:14b": ModelConfig(
            name="phi4:14b",
            provider="ollama",
            tier=ModelTier.FREE,
            context_size=16384,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            capabilities=["reasoning", "coding", "generation"],
            recommended_for=["generation", "idea_creation", "discussion"]
        ),
        "qwen2.5:14b": ModelConfig(
            name="qwen2.5:14b",
            provider="ollama",
            tier=ModelTier.FREE,
            context_size=32768,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            capabilities=["reasoning", "coding", "generation", "translation"],
            recommended_for=["generation", "translation", "discussion"]
        ),
        "llama3.2:3b": ModelConfig(
            name="llama3.2:3b",
            provider="ollama",
            tier=ModelTier.FREE,
            context_size=131072,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            capabilities=["summarization", "classification", "quick_tasks"],
            recommended_for=["summary", "classification", "filtering"]
        ),
    }

    # API models (Tier 2 - Paid)
    API_MODELS: Dict[str, ModelConfig] = {
        "claude-opus-4-5": ModelConfig(
            name="claude-opus-4-5",
            provider="claude",
            tier=ModelTier.PREMIUM,
            context_size=200000,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            capabilities=["reasoning", "analysis", "planning", "coding", "writing"],
            recommended_for=["final_plan", "quality_check", "complex_documents"]
        ),
        "claude-sonnet-4": ModelConfig(
            name="claude-sonnet-4",
            provider="claude",
            tier=ModelTier.STANDARD,
            context_size=200000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            capabilities=["reasoning", "analysis", "coding"],
            recommended_for=["drafts", "review", "coding"]
        ),
        "gpt-5.2": ModelConfig(
            name="gpt-5.2",
            provider="openai",
            tier=ModelTier.STANDARD,
            context_size=128000,
            cost_per_1k_input=0.0025,
            cost_per_1k_output=0.010,
            capabilities=["reasoning", "analysis", "coding"],
            recommended_for=["technical_review", "architecture", "validation"]
        ),
        "gemini-3-flash": ModelConfig(
            name="gemini-3-flash",
            provider="gemini",
            tier=ModelTier.BUDGET,
            context_size=1000000,
            cost_per_1k_input=0.000075,
            cost_per_1k_output=0.0003,
            capabilities=["fast_tasks", "summarization"],
            recommended_for=["quick_tasks", "bulk_processing"]
        ),
    }

    # Task to model mapping
    TASK_MODEL_MAP: Dict[str, List[str]] = {
        # Divergence phase - use local models
        "idea_generation": ["phi4:14b", "qwen2.5:14b"],
        "brainstorming": ["phi4:14b", "qwen2.5:14b"],
        "discussion": ["phi4:14b", "qwen2.5:14b"],

        # Convergence phase - use better local models
        "evaluation": ["qwen2.5:32b"],
        "scoring": ["qwen2.5:32b"],
        "filtering": ["llama3.2:3b"],

        # Moderation - use best local model
        "moderation": ["llama3.3:70b"],
        "final_decision": ["llama3.3:70b"],

        # Fast tasks - use smallest model
        "summary": ["llama3.2:3b"],
        "classification": ["llama3.2:3b"],
        "translation": ["qwen2.5:14b"],

        # Trend analysis - use good local models
        "trend_analysis": ["qwen2.5:32b", "phi4:14b"],

        # Critical outputs - use API models
        "final_plan": ["claude-opus-4-5", "llama3.3:70b"],  # Fallback to local
        "quality_check": ["claude-opus-4-5", "qwen2.5:32b"],
        "technical_review": ["gpt-5.2", "qwen2.5:32b"],
        "public_output": ["claude-opus-4-5", "llama3.3:70b"],
    }

    def __init__(self):
        self.all_models = {**self.LOCAL_MODELS, **self.API_MODELS}

    def get_model_for_task(
        self,
        task: str,
        prefer_local: bool = False,
        budget_available: bool = True,
    ) -> str:
        """
        Get the best model for a task.

        Args:
            task: Task type
            prefer_local: Whether to prefer local models
            budget_available: Whether API budget is available

        Returns:
            Model name
        """
        candidates = self.TASK_MODEL_MAP.get(task, ["qwen2.5:14b"])

        for model in candidates:
            config = self.all_models.get(model)
            if not config:
                continue

            # If preferring local, skip API models
            if prefer_local and config.provider != "ollama":
                continue

            # If no budget, skip paid models
            if not budget_available and config.tier != ModelTier.FREE:
                continue

            return model

        # Default to local model
        return "qwen2.5:14b"

    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for a model."""
        return self.all_models.get(model)

    def is_local_model(self, model: str) -> bool:
        """Check if a model is local (Ollama)."""
        config = self.all_models.get(model)
        return config and config.provider == "ollama"

    def is_api_model(self, model: str) -> bool:
        """Check if a model requires API."""
        config = self.all_models.get(model)
        return config and config.provider != "ollama"

    def get_local_models(self) -> List[str]:
        """Get list of local model names."""
        return list(self.LOCAL_MODELS.keys())

    def get_api_models(self) -> List[str]:
        """Get list of API model names."""
        return list(self.API_MODELS.keys())

    def get_fallback_model(self, model: str) -> str:
        """Get fallback model if primary is unavailable."""
        config = self.all_models.get(model)
        if not config:
            return "qwen2.5:14b"

        # If it's an API model, fallback to best local model for the task
        if config.provider != "ollama":
            for task in config.recommended_for:
                candidates = self.TASK_MODEL_MAP.get(task, [])
                for candidate in candidates:
                    if candidate in self.LOCAL_MODELS:
                        return candidate

        # Default fallback
        return "qwen2.5:32b" if config.tier in [ModelTier.PREMIUM, ModelTier.STANDARD] else "qwen2.5:14b"

    def estimate_task_tokens(self, task: str) -> Dict[str, int]:
        """Estimate token usage for a task type."""
        estimates = {
            "idea_generation": {"input": 2000, "output": 1000},
            "brainstorming": {"input": 3000, "output": 2000},
            "discussion": {"input": 2000, "output": 1500},
            "evaluation": {"input": 4000, "output": 2000},
            "scoring": {"input": 3000, "output": 500},
            "filtering": {"input": 1000, "output": 200},
            "moderation": {"input": 5000, "output": 2000},
            "final_decision": {"input": 5000, "output": 3000},
            "summary": {"input": 2000, "output": 500},
            "classification": {"input": 500, "output": 100},
            "translation": {"input": 2000, "output": 2000},
            "final_plan": {"input": 10000, "output": 8000},
            "quality_check": {"input": 8000, "output": 3000},
            "technical_review": {"input": 6000, "output": 4000},
            "public_output": {"input": 5000, "output": 5000},
        }
        return estimates.get(task, {"input": 2000, "output": 1000})
