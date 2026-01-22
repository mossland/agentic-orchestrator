"""
Hybrid LLM router for intelligent model selection.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..providers.ollama import OllamaProvider, OllamaResponse
from ..providers.claude import ClaudeProvider
from ..providers.openai import OpenAIProvider
from .budget import BudgetController
from .hierarchy import LLMHierarchy, ModelTier


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost: float
    duration_seconds: float
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "duration_seconds": self.duration_seconds,
            "cached": self.cached,
        }


class HybridLLMRouter:
    """
    Routes LLM requests between local (Ollama) and API providers.

    Routing strategy:
    1. Default to local models (free)
    2. Use API for critical/final outputs
    3. Automatic fallback when API budget exceeded
    4. Task-based model selection
    """

    def __init__(
        self,
        ollama: Optional[OllamaProvider] = None,
        claude: Optional[ClaudeProvider] = None,
        openai: Optional[OpenAIProvider] = None,
        budget: Optional[BudgetController] = None,
        hierarchy: Optional[LLMHierarchy] = None,
    ):
        self.ollama = ollama or OllamaProvider()
        self.claude = claude
        self.openai = openai
        self.budget = budget or BudgetController()
        self.hierarchy = hierarchy or LLMHierarchy()

        self._init_api_providers()

    def _init_api_providers(self):
        """Initialize API providers if not provided."""
        import os

        if self.claude is None and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.claude = ClaudeProvider()
            except Exception:
                pass

        if self.openai is None and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai = OpenAIProvider()
            except Exception:
                pass

    async def route(
        self,
        prompt: str,
        task_type: str = "generation",
        system: Optional[str] = None,
        quality: str = "normal",  # low, normal, high, critical
        force_local: bool = False,
        force_api: bool = False,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Route a request to the appropriate LLM.

        Args:
            prompt: The prompt to send
            task_type: Type of task (for model selection)
            system: System prompt
            quality: Required quality level
            force_local: Force use of local models
            force_api: Force use of API models
            model: Specific model to use (overrides routing)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content
        """
        start_time = datetime.utcnow()

        # Determine model to use
        if model:
            selected_model = model
        else:
            selected_model = self._select_model(
                task_type=task_type,
                quality=quality,
                force_local=force_local,
                force_api=force_api,
            )

        # Get model config
        model_config = self.hierarchy.get_model_config(selected_model)
        provider_name = model_config.provider if model_config else "ollama"

        # Route to appropriate provider
        try:
            if provider_name == "ollama":
                response = await self._call_ollama(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif provider_name == "claude" and self.claude:
                response = await self._call_claude(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif provider_name == "openai" and self.openai:
                response = await self._call_openai(
                    model=selected_model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                # Fallback to local
                fallback = self.hierarchy.get_fallback_model(selected_model)
                response = await self._call_ollama(
                    model=fallback,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                selected_model = fallback
                provider_name = "ollama"

        except Exception as e:
            # On error, try fallback
            print(f"Error with {selected_model}: {e}")
            fallback = self.hierarchy.get_fallback_model(selected_model)

            if fallback != selected_model:
                response = await self._call_ollama(
                    model=fallback,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                selected_model = fallback
                provider_name = "ollama"
            else:
                raise

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Record usage for API calls
        if provider_name != "ollama":
            self.budget.record_usage(
                provider=provider_name,
                model=selected_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

        return LLMResponse(
            content=response.content,
            model=selected_model,
            provider=provider_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=self.budget.estimate_cost(selected_model, response.input_tokens, response.output_tokens),
            duration_seconds=duration,
        )

    def _select_model(
        self,
        task_type: str,
        quality: str,
        force_local: bool,
        force_api: bool,
    ) -> str:
        """Select the best model for the request."""
        # Check budget status
        budget_status = self.budget.get_budget_status()
        budget_available = budget_status["can_use_api"]
        prefer_local = self.budget.should_use_local()

        # Force local if requested or no budget
        if force_local or not budget_available:
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=True,
                budget_available=False,
            )

        # Force API if requested and available
        if force_api and budget_available:
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=False,
                budget_available=True,
            )

        # Quality-based selection
        if quality == "critical":
            # Use API for critical tasks (if budget available)
            if budget_available:
                return self.hierarchy.get_model_for_task(
                    task_type,
                    prefer_local=False,
                    budget_available=True,
                )
            else:
                return "llama3.3:70b"  # Best local model

        elif quality == "high":
            # Use good local model or API
            if budget_available and not prefer_local:
                return self.hierarchy.get_model_for_task(
                    task_type,
                    prefer_local=False,
                    budget_available=True,
                )
            else:
                return "qwen2.5:32b"

        else:
            # Normal/low quality - use local
            return self.hierarchy.get_model_for_task(
                task_type,
                prefer_local=True,
                budget_available=budget_available,
            )

    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> OllamaResponse:
        """Call Ollama provider."""
        return await self.ollama.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _call_claude(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Call Claude provider."""
        if not self.claude:
            raise Exception("Claude provider not configured")

        response = await self.claude.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )

        # Convert to OllamaResponse-like object
        class APIResponse:
            def __init__(self, content, input_tokens, output_tokens):
                self.content = content
                self.input_tokens = input_tokens
                self.output_tokens = output_tokens

        return APIResponse(
            content=response.get("content", ""),
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
        )

    async def _call_openai(
        self,
        model: str,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Call OpenAI provider."""
        if not self.openai:
            raise Exception("OpenAI provider not configured")

        response = await self.openai.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )

        class APIResponse:
            def __init__(self, content, input_tokens, output_tokens):
                self.content = content
                self.input_tokens = input_tokens
                self.output_tokens = output_tokens

        return APIResponse(
            content=response.get("content", ""),
            input_tokens=response.get("input_tokens", 0),
            output_tokens=response.get("output_tokens", 0),
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        health = {
            "status": "healthy",
            "providers": {},
            "budget": self.budget.get_budget_status(),
        }

        # Check Ollama
        ollama_health = await self.ollama.health_check()
        health["providers"]["ollama"] = ollama_health

        if ollama_health.get("status") != "healthy":
            health["status"] = "degraded"

        # Check Claude
        if self.claude:
            try:
                health["providers"]["claude"] = {"status": "configured"}
            except Exception as e:
                health["providers"]["claude"] = {"status": "error", "error": str(e)}

        # Check OpenAI
        if self.openai:
            try:
                health["providers"]["openai"] = {"status": "configured"}
            except Exception as e:
                health["providers"]["openai"] = {"status": "error", "error": str(e)}

        return health

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models by provider."""
        return {
            "local": self.hierarchy.get_local_models(),
            "api": self.hierarchy.get_api_models(),
        }
