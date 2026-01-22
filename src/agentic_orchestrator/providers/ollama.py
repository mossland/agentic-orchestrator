"""
Ollama Local LLM provider.

Provides interface to Ollama for running local LLMs.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncIterator

import httpx

from .base import BaseProvider, ProviderError


@dataclass
class OllamaConfig:
    """Ollama configuration."""
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5:14b"
    timeout: int = 300  # 5 minutes for large models
    max_retries: int = 3


@dataclass
class OllamaResponse:
    """Response from Ollama."""
    content: str
    model: str
    total_duration: Optional[int] = None  # nanoseconds
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    done: bool = True

    @property
    def input_tokens(self) -> int:
        return self.prompt_eval_count or 0

    @property
    def output_tokens(self) -> int:
        return self.eval_count or 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def duration_seconds(self) -> float:
        if self.total_duration:
            return self.total_duration / 1e9
        return 0.0


class OllamaProvider(BaseProvider):
    """
    Ollama Local LLM Provider.

    Features:
    - Completely free (runs locally)
    - Streaming support
    - Multiple model support
    - GPU memory management
    """

    # Available models on the user's system
    AVAILABLE_MODELS = {
        "llama3.3:70b": {"size": "42GB", "context": 131072, "tier": "premium"},
        "qwen2.5:32b": {"size": "19GB", "context": 32768, "tier": "high"},
        "phi4:14b": {"size": "9.1GB", "context": 16384, "tier": "standard"},
        "qwen2.5:14b": {"size": "9.0GB", "context": 32768, "tier": "standard"},
        "llama3.2:3b": {"size": "2.0GB", "context": 131072, "tier": "fast"},
    }

    # Recommended models for different tasks
    TASK_MODELS = {
        "moderation": "llama3.3:70b",      # Complex reasoning, final decisions
        "evaluation": "qwen2.5:32b",        # Evaluation, scoring
        "generation": "phi4:14b",           # Idea generation
        "generation_alt": "qwen2.5:14b",    # Alternative generation
        "summary": "llama3.2:3b",           # Fast summaries
        "classification": "llama3.2:3b",    # Quick classification
        "translation": "qwen2.5:14b",       # Translation tasks
    }

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig(
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self._available_models: List[str] = []
        self._last_health_check: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> OllamaResponse:
        """
        Generate text using Ollama.

        Args:
            prompt: The prompt to send
            model: Model to use (default: config.default_model)
            system: System prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            OllamaResponse with generated text
        """
        model = model or self.config.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    content=data.get("response", ""),
                    model=model,
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    done=data.get("done", True)
                )

        except httpx.TimeoutException:
            raise ProviderError(f"Ollama timeout after {self.config.timeout}s")
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama HTTP error: {e.response.status_code}")
        except Exception as e:
            raise ProviderError(f"Ollama error: {e}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream text generation.

        Yields:
            Text chunks as they are generated
        """
        model = model or self.config.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.base_url}/api/generate",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise ProviderError(f"Ollama stream error: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> OllamaResponse:
        """
        Chat completion using Ollama.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            model: Model to use
            system: System prompt
            temperature: Sampling temperature

        Returns:
            OllamaResponse with generated text
        """
        model = model or self.config.default_model

        # Add system message if provided
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(messages)

        payload = {
            "model": model,
            "messages": chat_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=model,
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    done=data.get("done", True)
                )

        except Exception as e:
            raise ProviderError(f"Ollama chat error: {e}")

    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                self._available_models = [
                    model["name"] for model in data.get("models", [])
                ]
                return self._available_models

        except Exception as e:
            print(f"Error getting Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            async with httpx.AsyncClient(timeout=3600) as client:  # 1 hour timeout
                response = await client.post(
                    f"{self.config.base_url}/api/pull",
                    json={"name": model}
                )
                return response.status_code == 200

        except Exception as e:
            print(f"Error pulling model {model}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health and available models."""
        try:
            models = await self.get_available_models()
            self._last_health_check = datetime.utcnow()

            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "available_models": models,
                "default_model": self.config.default_model,
                "last_check": self._last_health_check.isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "base_url": self.config.base_url,
            }

    def get_model_for_task(self, task: str) -> str:
        """Get recommended model for a task type."""
        return self.TASK_MODELS.get(task, self.config.default_model)

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count."""
        # Rough estimate: ~4 characters per token for English
        return len(text) // 4

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
