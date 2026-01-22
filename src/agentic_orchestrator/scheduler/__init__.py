"""
Scheduler module for PM2-managed tasks.

This module provides CLI commands for scheduled tasks:
- signal-collect: Fetch signals from all adapters
- run-debate: Run multi-stage debate
- process-backlog: Process pending backlog items
- health-check: Check system health
"""

from .tasks import (
    signal_collect,
    run_debate,
    process_backlog,
    health_check,
)

__all__ = [
    "signal_collect",
    "run_debate",
    "process_backlog",
    "health_check",
]
