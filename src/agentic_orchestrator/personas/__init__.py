"""
Personas module for Agentic Orchestrator.

Provides diverse agent personas with different personalities,
roles, and expertise for multi-stage debates.
"""

from .personalities import (
    ThinkingStyle,
    DecisionStyle,
    CommunicationStyle,
    ActionStyle,
    Personality,
)
from .catalog import (
    AgentPersona,
    PersonaCategory,
    get_divergence_agents,
    get_convergence_agents,
    get_planning_agents,
    get_all_agents,
    get_agent_by_id,
)

__all__ = [
    # Personality types
    "ThinkingStyle",
    "DecisionStyle",
    "CommunicationStyle",
    "ActionStyle",
    "Personality",
    # Agent persona
    "AgentPersona",
    "PersonaCategory",
    # Agent getters
    "get_divergence_agents",
    "get_convergence_agents",
    "get_planning_agents",
    "get_all_agents",
    "get_agent_by_id",
]
