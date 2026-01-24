"""
Project generation package for Agentic Orchestrator.

Generates project scaffolds from approved Plans using LLM-based code generation.
"""

from .parser import PlanParser, ParsedPlan, TechStack, APIEndpoint, ProjectTask
from .templates import TemplateManager, SUPPORTED_STACKS
from .generator import ProjectCodeGenerator
from .scaffold import ProjectScaffold

__all__ = [
    "PlanParser",
    "ParsedPlan",
    "TechStack",
    "APIEndpoint",
    "ProjectTask",
    "TemplateManager",
    "SUPPORTED_STACKS",
    "ProjectCodeGenerator",
    "ProjectScaffold",
]
