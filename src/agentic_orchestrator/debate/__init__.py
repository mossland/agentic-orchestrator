"""
Multi-agent debate system for PLAN generation.

This module provides two debate approaches:

1. Legacy 4-role debate (DebateSession):
   - Founder, VC, Accelerator, Founder Friend
   - Uses paid API providers (Claude, OpenAI, Gemini)

2. Multi-stage debate with diverse personas (MultiStageDebate):
   - 34 agents with unique personalities
   - Three phases: Divergence → Convergence → Planning
   - Hybrid LLM routing (local Ollama + API fallback)

Usage (Legacy):
    from agentic_orchestrator.debate import (
        DebateSession,
        create_debate_session,
    )
    session = create_debate_session(...)
    result = session.run_debate()

Usage (Multi-stage):
    from agentic_orchestrator.debate import (
        MultiStageDebate,
        run_multi_stage_debate,
    )
    result = await run_multi_stage_debate(router, topic, context)
"""

from .debate_session import (
    DebateResult,
    DebateSession,
    create_debate_session,
)
from .discussion_record import (
    DebateRecord,
    DiscussionRecordFormatter,
    FeedbackEntry,
    FounderDecision,
    RoundData,
    create_feedback_entry,
    create_founder_decision,
    create_record,
    create_round_data,
)
from .moderator import (
    DebateModerator,
    RoundAssignment,
)
from .roles import (
    ROLE_CONFIGS,
    Role,
    RoleConfig,
    get_all_roles,
    get_feedback_roles,
    get_role_config,
)
from .protocol import (
    DebatePhase,
    DebateProtocol,
    DebateProtocolConfig,
    DebateMessage,
    DebateRound,
    PhaseResult,
    MessageType,
)
from .multi_stage import (
    Idea,
    MultiStageDebate,
    MultiStageDebateResult,
    run_multi_stage_debate,
)

__all__ = [
    # Roles (legacy)
    "Role",
    "RoleConfig",
    "get_role_config",
    "get_all_roles",
    "get_feedback_roles",
    "ROLE_CONFIGS",
    # Moderator (legacy)
    "DebateModerator",
    "RoundAssignment",
    # Records (legacy)
    "DebateRecord",
    "RoundData",
    "FeedbackEntry",
    "FounderDecision",
    "DiscussionRecordFormatter",
    "create_record",
    "create_round_data",
    "create_feedback_entry",
    "create_founder_decision",
    # Session (legacy)
    "DebateSession",
    "DebateResult",
    "create_debate_session",
    # Protocol (new)
    "DebatePhase",
    "DebateProtocol",
    "DebateProtocolConfig",
    "DebateMessage",
    "DebateRound",
    "PhaseResult",
    "MessageType",
    # Multi-stage debate (new)
    "Idea",
    "MultiStageDebate",
    "MultiStageDebateResult",
    "run_multi_stage_debate",
]
