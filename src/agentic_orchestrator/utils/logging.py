"""
Logging utilities for the Agentic Orchestrator.

Provides consistent logging across all modules with file and console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# Global logger cache
_loggers: dict = {}


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up the root logger for the orchestrator.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to log file. If None, only console logging.
        format_string: Custom format string for log messages.

    Returns:
        Root logger instance.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Get root logger for our package
    root_logger = logging.getLogger("agentic_orchestrator")
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Module name (usually __name__).

    Returns:
        Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    # Ensure name is under our package namespace
    if not name.startswith("agentic_orchestrator"):
        name = f"agentic_orchestrator.{name}"

    logger = logging.getLogger(name)
    _loggers[name] = logger

    return logger


class LogContext:
    """
    Context manager for temporary log level changes.

    Usage:
        with LogContext(logging.DEBUG):
            logger.debug("This will be logged")
    """

    def __init__(self, level: int):
        """
        Initialize log context.

        Args:
            level: Temporary logging level.
        """
        self.level = level
        self.previous_level = None
        self.logger = logging.getLogger("agentic_orchestrator")

    def __enter__(self):
        """Enter context - set temporary level."""
        self.previous_level = self.logger.level
        self.logger.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore previous level."""
        if self.previous_level is not None:
            self.logger.setLevel(self.previous_level)
        return False
