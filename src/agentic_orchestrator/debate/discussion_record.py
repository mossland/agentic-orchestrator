"""
Discussion record management for multi-agent debates.

This module handles:
- Recording debate rounds and feedback
- Formatting records for GitHub comments
- Storing and retrieving debate history
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .roles import Role, get_role_config


@dataclass
class FeedbackEntry:
    """Individual feedback from a role."""
    role: Role
    provider: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def role_name(self) -> str:
        """Get the English role name."""
        return get_role_config(self.role).name

    @property
    def role_emoji(self) -> str:
        """Get the role emoji."""
        return get_role_config(self.role).emoji

    @property
    def provider_display_name(self) -> str:
        """Get display name for provider."""
        names = {
            "claude": "Claude",
            "openai": "ChatGPT",
            "gemini": "Gemini",
        }
        return names.get(self.provider, self.provider)


@dataclass
class FounderDecision:
    """Founder's decision on feedback."""
    reflected: List[Dict[str, str]]  # List of {source, content, reason}
    not_reflected: List[Dict[str, str]]  # List of {source, content, reason}
    improvement_status: str  # "Sufficiently Improved" or "Needs Further Discussion"
    raw_response: str


@dataclass
class RoundData:
    """Data for a single debate round."""
    round_num: int
    role_assignments: Dict[Role, str]
    initial_plan: str
    feedbacks: List[FeedbackEntry]
    founder_decision: Optional[FounderDecision]
    updated_plan: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebateRecord:
    """Complete record of a debate session."""
    idea_issue_number: int
    plan_issue_number: Optional[int] = None
    rounds: List[RoundData] = field(default_factory=list)
    final_plan: str = ""
    termination_reason: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def total_rounds(self) -> int:
        """Get total number of rounds completed."""
        return len(self.rounds)

    @property
    def duration_minutes(self) -> Optional[float]:
        """Get total duration in minutes."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 60
        return None

    def add_round(self, round_data: RoundData) -> None:
        """Add a completed round to the record."""
        self.rounds.append(round_data)

    def complete(self, final_plan: str, termination_reason: str) -> None:
        """Mark the debate as complete."""
        self.final_plan = final_plan
        self.termination_reason = termination_reason
        self.completed_at = datetime.now()


class DiscussionRecordFormatter:
    """Formats debate records for GitHub comments."""

    TERMINATION_REASONS = {
        "maximum_rounds_reached": "Maximum Rounds Reached / 최대 라운드 도달",
        "founder_satisfied": "Founder Satisfied / 창업자 만족",
        "all_approved": "All Approved / 전원 승인",
    }

    PROVIDER_NAMES = {
        "claude": "Claude",
        "openai": "ChatGPT",
        "gemini": "Gemini",
    }

    ROLE_NAMES = {
        Role.FOUNDER: "Founder / 창업자",
        Role.VC: "VC",
        Role.ACCELERATOR: "Accelerator",
        Role.FOUNDER_FRIEND: "Founder Friend / 창업가 친구",
    }

    ROLE_NAMES_SHORT = {
        Role.FOUNDER: "Founder",
        Role.VC: "VC",
        Role.ACCELERATOR: "Accelerator",
        Role.FOUNDER_FRIEND: "Founder Friend",
    }

    def format_for_comment(self, record: DebateRecord) -> str:
        """
        Format the complete debate record as a GitHub comment.

        Args:
            record: The complete debate record

        Returns:
            Formatted markdown string for GitHub comment
        """
        lines = [
            "# 🎭 PLAN Debate Record / 토론 기록",
            "",
            f"**Idea Issue / 아이디어:** #{record.idea_issue_number}",
            f"**Debate Rounds / 토론 라운드:** {record.total_rounds}",
            f"**Termination Reason / 종료 사유:** {self.TERMINATION_REASONS.get(record.termination_reason, record.termination_reason)}",
        ]

        if record.duration_minutes:
            lines.append(f"**Total Duration / 총 소요시간:** {record.duration_minutes:.1f} min")

        lines.extend(["", "---", ""])

        # Add each round
        for round_data in record.rounds:
            lines.extend(self._format_round(round_data))
            lines.extend(["", "---", ""])

        # Add summary
        lines.extend(self._format_summary(record))

        return "\n".join(lines)

    def format_round_comment(self, round_data: RoundData) -> str:
        """
        Format a single round as a GitHub comment.

        Args:
            round_data: Data for the round

        Returns:
            Formatted markdown string
        """
        lines = self._format_round(round_data)
        return "\n".join(lines)

    def _format_round(self, round_data: RoundData) -> List[str]:
        """Format a single round."""
        lines = [
            f"## Round {round_data.round_num} ({round_data.timestamp.strftime('%Y-%m-%d %H:%M')})",
            "",
        ]

        # Role assignment table
        lines.extend([
            "### Role Assignments / 역할 배정",
            "| Role | AI |",
            "|------|-----|",
        ])

        for role, provider in round_data.role_assignments.items():
            role_name = self.ROLE_NAMES_SHORT.get(role, role.value)
            provider_name = self.PROVIDER_NAMES.get(provider, provider)
            lines.append(f"| {role_name} | {provider_name} |")

        lines.append("")

        # Initial/Updated plan (collapsed)
        if round_data.round_num == 1:
            lines.extend([
                "### 🚀 Initial Plan (Founder) / 초기 기획서 (창업자)",
                "<details>",
                "<summary>Click to expand / 펼쳐보기</summary>",
                "",
                round_data.initial_plan,
                "",
                "</details>",
                "",
            ])

        # Feedbacks
        for feedback in round_data.feedbacks:
            lines.extend(self._format_feedback(feedback))

        # Founder decision
        if round_data.founder_decision:
            lines.extend(self._format_founder_decision(round_data.founder_decision))

        # Updated plan (if not the same as initial)
        if round_data.updated_plan and round_data.updated_plan != round_data.initial_plan:
            lines.extend([
                "### 📝 Updated Plan / 업데이트된 기획서",
                "<details>",
                "<summary>Click to expand / 펼쳐보기</summary>",
                "",
                round_data.updated_plan,
                "",
                "</details>",
                "",
            ])

        return lines

    def _format_feedback(self, feedback: FeedbackEntry) -> List[str]:
        """Format a single feedback entry."""
        emoji = feedback.role_emoji
        role_name = self.ROLE_NAMES_SHORT.get(feedback.role, feedback.role_name)
        provider_name = feedback.provider_display_name

        return [
            f"### {emoji} {role_name} Feedback / 피드백 ({provider_name})",
            "<details>",
            "<summary>Click to expand / 펼쳐보기</summary>",
            "",
            feedback.content,
            "",
            "</details>",
            "",
        ]

    def _format_founder_decision(self, decision: FounderDecision) -> List[str]:
        """Format founder's decision on feedback."""
        lines = [
            "### 📋 Founder Decision / 창업자 결정",
            "",
        ]

        # Reflected feedback
        if decision.reflected:
            lines.append("**Adopted Feedback / 반영한 피드백:**")
            for item in decision.reflected:
                lines.append(f"- [{item.get('source', '')}] {item.get('content', '')}")
                if item.get('reason'):
                    lines.append(f"  - Reason / 이유: {item['reason']}")
            lines.append("")

        # Not reflected feedback
        if decision.not_reflected:
            lines.append("**Rejected Feedback / 미반영한 피드백:**")
            for item in decision.not_reflected:
                lines.append(f"- [{item.get('source', '')}] {item.get('content', '')}")
                if item.get('reason'):
                    lines.append(f"  - Reason / 이유: {item['reason']}")
            lines.append("")

        # Improvement status
        lines.extend([
            f"**Improvement Status / 개선 상태:** {decision.improvement_status}",
            "",
        ])

        return lines

    def _format_summary(self, record: DebateRecord) -> List[str]:
        """Format the summary section."""
        lines = [
            "## Final Result / 최종 결과",
            "",
        ]

        if record.completed_at:
            lines.append(f"**Debate Completed / 토론 완료:** {record.completed_at.strftime('%Y-%m-%d %H:%M')}")

        if record.duration_minutes:
            lines.append(f"**Total Duration / 총 소요시간:** {record.duration_minutes:.1f} min")

        reason_text = self.TERMINATION_REASONS.get(
            record.termination_reason,
            record.termination_reason
        )
        lines.extend([
            f"**Final Verdict / 최종 판정:** {reason_text}",
            "",
            "---",
            "*Generated by Agentic Orchestrator Multi-Agent Debate System*",
        ])

        return lines


def create_record(idea_issue_number: int) -> DebateRecord:
    """Create a new debate record."""
    return DebateRecord(idea_issue_number=idea_issue_number)


def create_round_data(
    round_num: int,
    role_assignments: Dict[Role, str],
    initial_plan: str,
) -> RoundData:
    """Create a new round data object."""
    return RoundData(
        round_num=round_num,
        role_assignments=role_assignments,
        initial_plan=initial_plan,
        feedbacks=[],
        founder_decision=None,
        updated_plan="",
    )


def create_feedback_entry(
    role: Role,
    provider: str,
    content: str,
) -> FeedbackEntry:
    """Create a feedback entry."""
    return FeedbackEntry(
        role=role,
        provider=provider,
        content=content,
    )


def create_founder_decision(
    reflected: List[Dict[str, str]],
    not_reflected: List[Dict[str, str]],
    improvement_status: str,
    raw_response: str,
) -> FounderDecision:
    """Create a founder decision record."""
    return FounderDecision(
        reflected=reflected,
        not_reflected=not_reflected,
        improvement_status=improvement_status,
        raw_response=raw_response,
    )
