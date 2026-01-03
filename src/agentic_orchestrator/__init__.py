"""
Mossland Agentic Orchestrator

An autonomous orchestration system that performs the complete software development lifecycle:
Idea Discovery → Detailed Planning → Development → Testing/Evaluation → Feedback Integration
"""

__version__ = "0.1.0"
__author__ = "Mossland"

from .orchestrator import Orchestrator
from .state import State, Stage

__all__ = ["Orchestrator", "State", "Stage", "__version__"]
