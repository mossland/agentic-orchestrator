"""
Database module for Agentic Orchestrator.

Provides SQLAlchemy models, connection management, and repositories
for long-term data persistence.
"""

from .connection import Database, db
from .models import (
    Base,
    Signal,
    Trend,
    Idea,
    DebateSession,
    DebateMessage,
    Plan,
    APIUsage,
    SystemLog,
    AgentState,
)
from .repositories import (
    SignalRepository,
    TrendRepository,
    IdeaRepository,
    DebateRepository,
    PlanRepository,
    APIUsageRepository,
    SystemLogRepository,
)

__all__ = [
    # Connection
    "Database",
    "db",
    # Models
    "Base",
    "Signal",
    "Trend",
    "Idea",
    "DebateSession",
    "DebateMessage",
    "Plan",
    "APIUsage",
    "SystemLog",
    "AgentState",
    # Repositories
    "SignalRepository",
    "TrendRepository",
    "IdeaRepository",
    "DebateRepository",
    "PlanRepository",
    "APIUsageRepository",
    "SystemLogRepository",
]
