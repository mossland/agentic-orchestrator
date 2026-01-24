"""
Database module for Agentic Orchestrator.

Provides SQLAlchemy models, connection management, and repositories
for long-term data persistence.
"""

from .connection import Database, db, init_database, get_db

# Aliases for backward compatibility
get_database = get_db
from .models import (
    Base,
    Signal,
    Trend,
    Idea,
    DebateSession,
    DebateMessage,
    Plan,
    Project,
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
    ProjectRepository,
    APIUsageRepository,
    SystemLogRepository,
)

__all__ = [
    # Connection
    "Database",
    "db",
    "init_database",
    "get_db",
    "get_database",
    # Models
    "Base",
    "Signal",
    "Trend",
    "Idea",
    "DebateSession",
    "DebateMessage",
    "Plan",
    "Project",
    "APIUsage",
    "SystemLog",
    "AgentState",
    # Repositories
    "SignalRepository",
    "TrendRepository",
    "IdeaRepository",
    "DebateRepository",
    "PlanRepository",
    "ProjectRepository",
    "APIUsageRepository",
    "SystemLogRepository",
]
