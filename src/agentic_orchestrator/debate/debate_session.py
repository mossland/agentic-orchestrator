"""
Debate session management for multi-agent PLAN generation.

This module orchestrates the entire debate flow:
1. Founder creates initial plan
2. Feedback from VC, Accelerator, Founder Friend
3. Founder reflects and updates plan
4. Repeat until termination condition met
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..providers.base import BaseProvider, Message
from .roles import (
    Role,
    get_role_config,
    get_feedback_roles,
    ROLE_CONFIGS,
)
from .moderator import DebateModerator
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


logger = logging.getLogger(__name__)


@dataclass
class DebateResult:
    """Result of a completed debate session."""
    final_plan: str
    record: DebateRecord
    termination_reason: str
    total_rounds: int

    def format_discussion_record(self) -> str:
        """Format the debate record for GitHub comment."""
        formatter = DiscussionRecordFormatter()
        return formatter.format_for_comment(self.record)


class DebateSession:
    """
    Manages a complete debate session for PLAN generation.

    The debate follows this flow:
    1. Founder creates initial plan from idea
    2. For each round:
       a. VC provides feedback
       b. Accelerator provides feedback
       c. Founder Friend provides feedback
       d. Founder reflects on feedback and updates plan
    3. Check termination conditions
    4. Repeat until satisfied or max rounds reached
    """

    def __init__(
        self,
        idea_title: str,
        idea_content: str,
        idea_issue_number: int,
        providers: Dict[str, BaseProvider],
        max_rounds: int = 5,
        min_rounds: int = 1,
        dry_run: bool = False,
    ):
        """
        Initialize a debate session.

        Args:
            idea_title: Title of the idea issue
            idea_content: Body content of the idea issue
            idea_issue_number: GitHub issue number for the idea
            providers: Dict of provider name to BaseProvider instance
                       {"claude": ClaudeProvider, "openai": OpenAIProvider, "gemini": GeminiProvider}
            max_rounds: Maximum number of debate rounds
            min_rounds: Minimum rounds before early termination
            dry_run: If True, don't make actual API calls
        """
        self.idea_title = idea_title
        self.idea_content = idea_content
        self.idea_issue_number = idea_issue_number
        self.providers = providers
        self.dry_run = dry_run

        self.moderator = DebateModerator(
            max_rounds=max_rounds,
            min_rounds=min_rounds,
        )

        self.record = create_record(idea_issue_number)
        self.current_plan = ""

    def run_debate(self) -> DebateResult:
        """
        Execute the complete debate session.

        Returns:
            DebateResult with final plan and discussion record
        """
        logger.info(f"Starting debate for idea #{self.idea_issue_number}")

        round_num = 0
        termination_reason = ""
        feedback_responses: Dict[Role, str] = {}

        while True:
            round_num += 1
            logger.info(f"Starting round {round_num}")

            # Get role assignments for this round
            assignment = self.moderator.get_round_assignment(round_num)

            # Create round data
            round_data = create_round_data(
                round_num=round_num,
                role_assignments=assignment.assignments,
                initial_plan=self.current_plan if round_num > 1 else "",
            )

            # Phase 1: Founder creates/updates plan
            if round_num == 1:
                self.current_plan = self._run_founder_initial(assignment)
                round_data.initial_plan = self.current_plan
            else:
                # In subsequent rounds, plan update happens after reflection
                round_data.initial_plan = self.current_plan

            # Phase 2: Get feedback from all reviewers
            feedback_responses = {}
            for role in get_feedback_roles():
                feedback = self._run_feedback(role, assignment)
                feedback_responses[role] = feedback

                # Add to round data
                round_data.feedbacks.append(create_feedback_entry(
                    role=role,
                    provider=assignment.get_provider_for_role(role),
                    content=feedback,
                ))

            # Phase 3: Founder reflects on feedback
            founder_response = self._run_founder_reflection(
                assignment,
                feedback_responses,
            )

            # Parse founder decision
            founder_decision = self._parse_founder_decision(founder_response)
            round_data.founder_decision = founder_decision

            # Extract updated plan from founder's response
            updated_plan = self._extract_updated_plan(founder_response)
            if updated_plan:
                self.current_plan = updated_plan
            round_data.updated_plan = self.current_plan

            # Add round to record
            self.record.add_round(round_data)

            # Check termination
            should_stop, termination_reason = self.moderator.should_terminate(
                round_num=round_num,
                founder_response=founder_response,
                feedback_responses=feedback_responses,
            )

            logger.info(
                f"Round {round_num} completed. "
                f"Termination check: {should_stop}, reason: {termination_reason}"
            )

            if should_stop:
                break

        # Complete the record
        self.record.complete(
            final_plan=self.current_plan,
            termination_reason=termination_reason,
        )

        return DebateResult(
            final_plan=self.current_plan,
            record=self.record,
            termination_reason=termination_reason,
            total_rounds=round_num,
        )

    def _get_provider(self, provider_name: str) -> BaseProvider:
        """Get provider by name."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
        return self.providers[provider_name]

    def _run_founder_initial(self, assignment) -> str:
        """Run founder's initial plan creation."""
        role = Role.FOUNDER
        provider_name = assignment.get_provider_for_role(role)
        provider = self._get_provider(provider_name)
        role_config = get_role_config(role)

        # Build prompt
        prompt = role_config.initial_prompt_template.format(
            idea_title=self.idea_title,
            idea_content=self.idea_content,
        )

        logger.info(f"Founder ({provider_name}) creating initial plan")

        response = provider.chat(
            user_message=prompt,
            system_message=role_config.system_prompt,
        )

        return response

    def _run_feedback(self, role: Role, assignment) -> str:
        """Run feedback from a reviewer role."""
        provider_name = assignment.get_provider_for_role(role)
        provider = self._get_provider(provider_name)
        role_config = get_role_config(role)

        # Build prompt
        prompt = role_config.feedback_prompt_template.format(
            current_plan=self.current_plan,
        )

        logger.info(f"{role.value} ({provider_name}) providing feedback")

        response = provider.chat(
            user_message=prompt,
            system_message=role_config.system_prompt,
        )

        return response

    def _run_founder_reflection(
        self,
        assignment,
        feedback_responses: Dict[Role, str],
    ) -> str:
        """Run founder's reflection on feedback."""
        role = Role.FOUNDER
        provider_name = assignment.get_provider_for_role(role)
        provider = self._get_provider(provider_name)
        role_config = get_role_config(role)

        # Build prompt with all feedback
        prompt = role_config.reflection_prompt_template.format(
            current_plan=self.current_plan,
            vc_feedback=feedback_responses.get(Role.VC, "No feedback provided"),
            accelerator_feedback=feedback_responses.get(Role.ACCELERATOR, "No feedback provided"),
            friend_feedback=feedback_responses.get(Role.FOUNDER_FRIEND, "No feedback provided"),
        )

        logger.info(f"Founder ({provider_name}) reflecting on feedback")

        response = provider.chat(
            user_message=prompt,
            system_message=role_config.system_prompt,
        )

        return response

    def _parse_founder_decision(self, response: str) -> FounderDecision:
        """Parse founder's reflection response to extract decision."""
        reflected = []
        not_reflected = []
        improvement_status = "Needs Further Discussion"

        # Extract improvement status (English patterns first, then Korean)
        if re.search(r"\*\*Sufficiently Improved\*\*", response, re.IGNORECASE):
            improvement_status = "Sufficiently Improved"
        elif re.search(r"Sufficiently Improved", response, re.IGNORECASE):
            improvement_status = "Sufficiently Improved"
        elif re.search(r"\*\*충분히 개선됨\*\*", response):
            improvement_status = "Sufficiently Improved"
        elif re.search(r"충분히 개선됨", response):
            improvement_status = "Sufficiently Improved"
        elif re.search(r"\*\*Needs Further Discussion\*\*", response, re.IGNORECASE):
            improvement_status = "Needs Further Discussion"
        elif re.search(r"\*\*추가 논의 필요\*\*", response):
            improvement_status = "Needs Further Discussion"

        # Try to extract reflected/not reflected items from table format
        # Looking for table rows like: | VC | Market analysis | Important point |
        table_pattern = r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
        lines = response.split("\n")

        in_reflected_section = False
        in_not_reflected_section = False

        for line in lines:
            line_lower = line.lower()

            # Detect section (English first, then Korean)
            if "adopted feedback" in line_lower or "반영할 피드백" in line or "반영한 피드백" in line:
                in_reflected_section = True
                in_not_reflected_section = False
            elif "rejected feedback" in line_lower or "미반영" in line:
                in_reflected_section = False
                in_not_reflected_section = True
            elif line.startswith("##"):
                in_reflected_section = False
                in_not_reflected_section = False

            # Parse table row
            match = re.match(table_pattern, line)
            if match:
                source = match.group(1).strip()
                content = match.group(2).strip()
                reason = match.group(3).strip()

                # Skip header rows (English and Korean)
                if source.lower() in ["source", "피드백 출처", "---", "출처", "역할"]:
                    continue

                entry = {
                    "source": source,
                    "content": content,
                    "reason": reason,
                }

                if in_reflected_section:
                    reflected.append(entry)
                elif in_not_reflected_section:
                    not_reflected.append(entry)

        return create_founder_decision(
            reflected=reflected,
            not_reflected=not_reflected,
            improvement_status=improvement_status,
            raw_response=response,
        )

    def _extract_updated_plan(self, response: str) -> Optional[str]:
        """Extract the updated plan from founder's reflection response."""
        # Priority 1: Look for [PLAN_START] and [PLAN_END] markers (most reliable)
        plan_marker_pattern = r"\[PLAN_START\]\s*(.*?)\s*\[PLAN_END\]"
        marker_match = re.search(plan_marker_pattern, response, re.DOTALL | re.IGNORECASE)
        if marker_match:
            plan_content = marker_match.group(1).strip()
            if plan_content:
                logger.info("Extracted plan using PLAN_START/PLAN_END markers")
                return plan_content

        # Priority 2: Look for "## Updated Plan" or Korean equivalent sections
        section_patterns = [
            r"##\s*Updated Plan\s*\n(.*?)(?=\n---|\n##\s+[^#]|\[Korean Translation|\Z)",
            r"##\s*업데이트된 기획서\s*\n(.*?)(?=\n---|\n##\s+[^#]|\Z)",
            r"##\s*개선된 기획서\s*\n(.*?)(?=\n---|\n##\s+[^#]|\Z)",
        ]

        for pattern in section_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                plan_content = match.group(1).strip()
                if plan_content:
                    logger.info(f"Extracted plan using section pattern")
                    return plan_content

        # If no explicit section found, return None (keep current plan)
        logger.warning("Could not extract updated plan from founder response")
        return None


def create_debate_session(
    idea_title: str,
    idea_content: str,
    idea_issue_number: int,
    providers: Dict[str, BaseProvider],
    max_rounds: int = 5,
    dry_run: bool = False,
) -> DebateSession:
    """
    Factory function to create a debate session.

    Args:
        idea_title: Title of the idea
        idea_content: Body content of the idea
        idea_issue_number: GitHub issue number
        providers: Dict of provider instances
        max_rounds: Maximum debate rounds
        dry_run: If True, don't make actual API calls

    Returns:
        Configured DebateSession instance
    """
    return DebateSession(
        idea_title=idea_title,
        idea_content=idea_content,
        idea_issue_number=idea_issue_number,
        providers=providers,
        max_rounds=max_rounds,
        dry_run=dry_run,
    )
