"""
Debate moderator for managing role rotation and round progression.

This module handles:
- AI provider to role assignment per round
- Round rotation logic
- Termination condition checking
"""

import logging
from dataclasses import dataclass

from .roles import Role, get_feedback_roles

logger = logging.getLogger(__name__)


@dataclass
class RoundAssignment:
    """Role assignments for a single round."""

    round_num: int
    assignments: dict[Role, str]  # Role -> provider name (claude, openai, gemini)

    def get_provider_for_role(self, role: Role) -> str:
        """Get the provider name assigned to a role."""
        return self.assignments[role]

    def get_roles_for_provider(self, provider_name: str) -> list[Role]:
        """Get all roles assigned to a provider."""
        return [role for role, provider in self.assignments.items() if provider == provider_name]


class DebateModerator:
    """
    Manages debate round progression and role rotation.

    The rotation ensures each AI (Claude, ChatGPT, Gemini) takes on different
    roles across rounds, providing diverse perspectives.
    """

    # Provider names
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"

    # Rotation matrix: defines AI-to-role mapping for each round
    # Each round rotates the AI assignments to ensure diverse perspectives
    ROTATION_MATRIX: list[dict[Role, str]] = [
        # Round 1: Claude leads as Founder
        {
            Role.FOUNDER: "claude",
            Role.VC: "openai",
            Role.ACCELERATOR: "gemini",
            Role.FOUNDER_FRIEND: "claude",  # Founder also plays friend (both have reality distortion)
        },
        # Round 2: OpenAI leads as Founder
        {
            Role.FOUNDER: "openai",
            Role.VC: "gemini",
            Role.ACCELERATOR: "claude",
            Role.FOUNDER_FRIEND: "openai",
        },
        # Round 3: Gemini leads as Founder
        {
            Role.FOUNDER: "gemini",
            Role.VC: "claude",
            Role.ACCELERATOR: "openai",
            Role.FOUNDER_FRIEND: "gemini",
        },
        # Round 4: Rotate again
        {
            Role.FOUNDER: "claude",
            Role.VC: "gemini",
            Role.ACCELERATOR: "openai",
            Role.FOUNDER_FRIEND: "claude",
        },
        # Round 5: Final rotation
        {
            Role.FOUNDER: "openai",
            Role.VC: "claude",
            Role.ACCELERATOR: "gemini",
            Role.FOUNDER_FRIEND: "openai",
        },
    ]

    # Explicit termination markers - only these exact strings trigger termination
    # The founder must write [TERMINATE] explicitly to end the debate
    TERMINATION_MARKERS = [
        "[TERMINATE]",
        "[terminate]",
    ]

    # Continue markers for clarity (used for logging, not detection)
    CONTINUE_MARKERS = [
        "[CONTINUE]",
        "[continue]",
    ]

    # Approval indicators from feedback providers
    APPROVAL_INDICATORS = [
        "INVEST",
        "STRONG FIT",
        "APPROVED",
    ]

    def __init__(
        self,
        max_rounds: int = 5,
        min_rounds: int = 1,
        require_all_approval: bool = False,
    ):
        """
        Initialize the debate moderator.

        Args:
            max_rounds: Maximum number of debate rounds
            min_rounds: Minimum rounds before early termination allowed
            require_all_approval: If True, needs all feedback providers to approve
        """
        self.max_rounds = max_rounds
        self.min_rounds = min_rounds
        self.require_all_approval = require_all_approval

    def get_round_assignment(self, round_num: int) -> RoundAssignment:
        """
        Get role assignments for a specific round.

        Args:
            round_num: Round number (1-indexed)

        Returns:
            RoundAssignment with AI-to-role mappings
        """
        # Use modulo to cycle through rotation matrix
        rotation_idx = (round_num - 1) % len(self.ROTATION_MATRIX)
        assignments = self.ROTATION_MATRIX[rotation_idx].copy()

        return RoundAssignment(
            round_num=round_num,
            assignments=assignments,
        )

    def get_provider_for_role(self, round_num: int, role: Role) -> str:
        """
        Get the provider name assigned to a role for a specific round.

        Args:
            round_num: Round number (1-indexed)
            role: The role to get provider for

        Returns:
            Provider name (claude, openai, gemini)
        """
        assignment = self.get_round_assignment(round_num)
        return assignment.get_provider_for_role(role)

    def should_terminate(
        self,
        round_num: int,
        founder_response: str,
        feedback_responses: dict[Role, str] | None = None,
    ) -> tuple[bool, str]:
        """
        Determine if the debate should terminate.

        Args:
            round_num: Current round number (1-indexed)
            founder_response: Founder's reflection response
            feedback_responses: Dict of feedback role to response content

        Returns:
            Tuple of (should_terminate, reason)
        """
        # Check maximum rounds
        if round_num >= self.max_rounds:
            logger.info(f"Terminating: reached maximum rounds ({self.max_rounds})")
            return True, "maximum_rounds_reached"

        # Check minimum rounds before allowing early termination
        if round_num < self.min_rounds:
            return False, "minimum_rounds_not_reached"

        # Check founder satisfaction
        if self._is_founder_satisfied(founder_response):
            logger.info("Terminating: founder indicated sufficient improvement")
            return True, "founder_satisfied"

        # Optionally check all approvals
        if self.require_all_approval and feedback_responses:
            if self._all_approved(feedback_responses):
                logger.info("Terminating: all feedback providers approved")
                return True, "all_approved"

        return False, "continue"

    def _is_founder_satisfied(self, response: str) -> bool:
        """Check if founder explicitly marked termination with [TERMINATE]."""
        return any(marker in response for marker in self.TERMINATION_MARKERS)

    def _all_approved(self, feedback_responses: dict[Role, str]) -> bool:
        """Check if all feedback providers approved."""
        feedback_roles = get_feedback_roles()

        for role in feedback_roles:
            if role not in feedback_responses:
                continue

            response = feedback_responses[role]
            response_upper = response.upper()

            if not any(ind.upper() in response_upper for ind in self.APPROVAL_INDICATORS):
                return False

        return True

    def format_round_header(self, round_num: int) -> str:
        """Format a header string for a round."""
        assignment = self.get_round_assignment(round_num)

        lines = [
            f"## Round {round_num}",
            "",
            "### Role Assignments",
            "| Role | AI |",
            "|------|-----|",
        ]

        role_names = {
            Role.FOUNDER: "Founder",
            Role.VC: "VC",
            Role.ACCELERATOR: "Accelerator",
            Role.FOUNDER_FRIEND: "Founder Friend",
        }

        provider_names = {
            "claude": "Claude",
            "openai": "ChatGPT",
            "gemini": "Gemini",
        }

        for role, provider in assignment.assignments.items():
            role_name = role_names.get(role, role.value)
            provider_name = provider_names.get(provider, provider)
            lines.append(f"| {role_name} | {provider_name} |")

        return "\n".join(lines)

    def get_termination_reason_message(self, reason: str) -> str:
        """Get a human-readable message for termination reason."""
        messages = {
            "maximum_rounds_reached": (
                f"Debate ended: reached maximum rounds ({self.max_rounds})."
            ),
            "founder_satisfied": (
                "Debate ended: founder determined sufficient improvement."
            ),
            "all_approved": (
                "Debate ended: all feedback providers approved."
            ),
            "minimum_rounds_not_reached": (
                f"Continuing: minimum rounds ({self.min_rounds}) not yet reached."
            ),
            "continue": "Continuing debate.",
        }
        return messages.get(reason, f"Debate status: {reason}")
