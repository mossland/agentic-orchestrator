"""
Multi-agent debate system for PLAN generation.

This module provides a debate-based approach to generating planning documents
where multiple AI personas (Founder, VC, Accelerator, Founder Friend) discuss
and refine the plan through iterative rounds.

Usage:
    from agentic_orchestrator.debate import (
        DebateSession,
        create_debate_session,
        Role,
        DebateResult,
    )

    # Create a debate session
    session = create_debate_session(
        idea_title="[IDEA] New Feature",
        idea_content="Feature description...",
        idea_issue_number=123,
        providers={
            "claude": claude_provider,
            "openai": openai_provider,
            "gemini": gemini_provider,
        },
    )

    # Run the debate
    result = session.run_debate()

    # Get the final plan
    final_plan = result.final_plan

    # Get formatted discussion record for GitHub
    discussion_comment = result.format_discussion_record()
"""

from .roles import (
    Role,
    RoleConfig,
    get_role_config,
    get_all_roles,
    get_feedback_roles,
    ROLE_CONFIGS,
)

from .moderator import (
    DebateModerator,
    RoundAssignment,
)

from .discussion_record import (
    DebateRecord,
    RoundData,
    FeedbackEntry,
    FounderDecision,
    DiscussionRecordFormatter,
    create_record,
    create_round_data,
    create_feedback_entry,
    create_founder_decision,
)

from .debate_session import (
    DebateSession,
    DebateResult,
    create_debate_session,
)


__all__ = [
    # Roles
    "Role",
    "RoleConfig",
    "get_role_config",
    "get_all_roles",
    "get_feedback_roles",
    "ROLE_CONFIGS",
    # Moderator
    "DebateModerator",
    "RoundAssignment",
    # Records
    "DebateRecord",
    "RoundData",
    "FeedbackEntry",
    "FounderDecision",
    "DiscussionRecordFormatter",
    "create_record",
    "create_round_data",
    "create_feedback_entry",
    "create_founder_decision",
    # Session
    "DebateSession",
    "DebateResult",
    "create_debate_session",
]
