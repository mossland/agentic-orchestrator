"""
API Budget controller for managing LLM costs.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path
import json

from ..db.connection import db
from ..db.repositories import APIUsageRepository


@dataclass
class UsageBudget:
    """Budget configuration."""
    daily_limit_usd: float = 5.0  # Conservative daily limit
    monthly_limit_usd: float = 150.0  # ~$5/day * 30 days
    warning_threshold: float = 0.7  # Warn at 70%
    critical_threshold: float = 0.9  # Critical at 90%


@dataclass
class ProviderPricing:
    """Pricing per 1M tokens."""
    input: float
    output: float


class BudgetController:
    """
    Controls and tracks API usage and costs.

    Features:
    - Daily and monthly budget tracking
    - Cost estimation before API calls
    - Automatic fallback to local models when budget exceeded
    - Usage reports
    """

    # Pricing per 1M tokens (as of 2026)
    PRICING: Dict[str, ProviderPricing] = {
        # Claude models
        "claude-opus-4-5": ProviderPricing(input=15.0, output=75.0),
        "claude-sonnet-4": ProviderPricing(input=3.0, output=15.0),
        "claude-haiku-3-5": ProviderPricing(input=0.80, output=4.0),

        # OpenAI models
        "gpt-5.2": ProviderPricing(input=2.5, output=10.0),
        "gpt-5.2-chat-latest": ProviderPricing(input=2.5, output=10.0),
        "gpt-4o": ProviderPricing(input=2.5, output=10.0),

        # Gemini models
        "gemini-3-pro": ProviderPricing(input=1.25, output=5.0),
        "gemini-3-flash": ProviderPricing(input=0.075, output=0.30),

        # Local (free)
        "ollama": ProviderPricing(input=0.0, output=0.0),
    }

    def __init__(
        self,
        budget: Optional[UsageBudget] = None,
        storage_path: Optional[Path] = None,
    ):
        self.budget = budget or UsageBudget(
            daily_limit_usd=float(os.getenv("DAILY_BUDGET_USD", "5.0")),
            monthly_limit_usd=float(os.getenv("MONTHLY_BUDGET_USD", "150.0")),
        )
        self.storage_path = storage_path or Path("data/usage")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def can_use_api(
        self,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int = 0,
    ) -> bool:
        """
        Check if API usage is within budget.

        Args:
            model: Model name
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens (defaults to input * 0.5)

        Returns:
            True if usage is within budget
        """
        if estimated_output_tokens == 0:
            estimated_output_tokens = int(estimated_input_tokens * 0.5)

        estimated_cost = self.estimate_cost(
            model,
            estimated_input_tokens,
            estimated_output_tokens
        )

        today_usage = self.get_today_usage()
        return (today_usage["total_cost"] + estimated_cost) <= self.budget.daily_limit_usd

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a request."""
        pricing = self._get_pricing(model)
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing.input
        output_cost = (output_tokens / 1_000_000) * pricing.output

        return round(input_cost + output_cost, 6)

    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, Any]:
        """
        Record API usage.

        Args:
            provider: Provider name (claude, openai, gemini, ollama)
            model: Model name
            input_tokens: Input tokens used
            output_tokens: Output tokens used

        Returns:
            Updated usage statistics
        """
        cost = self.estimate_cost(model, input_tokens, output_tokens)

        with db.session() as session:
            repo = APIUsageRepository(session)
            repo.record(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost
            )

        return self.get_today_usage()

    def get_today_usage(self) -> Dict[str, Any]:
        """Get today's usage statistics."""
        with db.session() as session:
            repo = APIUsageRepository(session)
            usage = repo.get_today_usage()

            return {
                "date": date.today().isoformat(),
                "total_cost": usage["total_cost"],
                "total_input_tokens": usage["total_input_tokens"],
                "total_output_tokens": usage["total_output_tokens"],
                "total_requests": usage["total_requests"],
                "daily_limit": self.budget.daily_limit_usd,
                "daily_remaining": max(0, self.budget.daily_limit_usd - usage["total_cost"]),
                "daily_used_percent": (usage["total_cost"] / self.budget.daily_limit_usd) * 100,
            }

    def get_month_usage(self) -> Dict[str, Any]:
        """Get this month's usage statistics."""
        with db.session() as session:
            repo = APIUsageRepository(session)
            total_cost = repo.get_month_total()

            return {
                "month": date.today().strftime("%Y-%m"),
                "total_cost": total_cost,
                "monthly_limit": self.budget.monthly_limit_usd,
                "monthly_remaining": max(0, self.budget.monthly_limit_usd - total_cost),
                "monthly_used_percent": (total_cost / self.budget.monthly_limit_usd) * 100,
            }

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        today = self.get_today_usage()
        month = self.get_month_usage()

        # Determine status level
        daily_percent = today["daily_used_percent"]
        monthly_percent = month["monthly_used_percent"]

        if daily_percent >= self.budget.critical_threshold * 100 or monthly_percent >= self.budget.critical_threshold * 100:
            status = "critical"
        elif daily_percent >= self.budget.warning_threshold * 100 or monthly_percent >= self.budget.warning_threshold * 100:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "daily": today,
            "monthly": month,
            "can_use_api": daily_percent < 100 and monthly_percent < 100,
        }

    def get_usage_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Get today's usage broken down by provider."""
        with db.session() as session:
            repo = APIUsageRepository(session)
            return repo.get_today_by_provider()

    def get_usage_history(self, days: int = 30) -> list:
        """Get usage history for the past N days."""
        with db.session() as session:
            repo = APIUsageRepository(session)
            return repo.get_usage_history(days)

    def generate_daily_report(self) -> str:
        """Generate a daily usage report."""
        today = self.get_today_usage()
        by_provider = self.get_usage_by_provider()
        month = self.get_month_usage()

        report = f"""
# API Usage Report - {today['date']}

## Daily Summary
- Total Cost: ${today['total_cost']:.4f} / ${today['daily_limit']:.2f}
- Usage: {today['daily_used_percent']:.1f}%
- Remaining: ${today['daily_remaining']:.4f}
- Total Requests: {today['total_requests']}
- Total Tokens: {today['total_input_tokens'] + today['total_output_tokens']:,}

## By Provider
"""
        for provider, usage in by_provider.items():
            report += f"""
### {provider.title()}
- Cost: ${usage['cost']:.4f}
- Requests: {usage['requests']}
- Tokens: {usage['input_tokens'] + usage['output_tokens']:,}
"""

        report += f"""
## Monthly Summary
- Total Cost: ${month['total_cost']:.4f} / ${month['monthly_limit']:.2f}
- Usage: {month['monthly_used_percent']:.1f}%
- Remaining: ${month['monthly_remaining']:.4f}
"""

        return report

    def _get_pricing(self, model: str) -> Optional[ProviderPricing]:
        """Get pricing for a model."""
        # Check exact match
        if model in self.PRICING:
            return self.PRICING[model]

        # Check partial match
        model_lower = model.lower()
        for key, pricing in self.PRICING.items():
            if key in model_lower or model_lower in key:
                return pricing

        # Check provider-based
        if "claude" in model_lower or "opus" in model_lower or "sonnet" in model_lower:
            if "opus" in model_lower:
                return self.PRICING["claude-opus-4-5"]
            elif "sonnet" in model_lower:
                return self.PRICING["claude-sonnet-4"]
            else:
                return self.PRICING["claude-haiku-3-5"]

        if "gpt" in model_lower:
            return self.PRICING["gpt-5.2"]

        if "gemini" in model_lower:
            if "flash" in model_lower:
                return self.PRICING["gemini-3-flash"]
            return self.PRICING["gemini-3-pro"]

        # Default to free (local)
        return self.PRICING["ollama"]

    def should_use_local(self) -> bool:
        """Check if we should prefer local models due to budget."""
        status = self.get_budget_status()
        return status["status"] in ["warning", "critical"]
