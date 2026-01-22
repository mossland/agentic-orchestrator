"""
Personality system for agent personas.

Defines 4 axes of personality traits that influence how agents
think, communicate, and make decisions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ThinkingStyle(Enum):
    """How the agent approaches problems initially."""
    OPTIMISTIC = "optimistic"  # Sees possibilities and opportunities first
    CAUTIOUS = "cautious"      # Sees risks and problems first


class DecisionStyle(Enum):
    """How the agent makes decisions."""
    INTUITIVE = "intuitive"    # Quick, pattern-based decisions
    ANALYTICAL = "analytical"  # Data-driven, systematic analysis


class CommunicationStyle(Enum):
    """How the agent communicates feedback."""
    CHALLENGER = "challenger"  # Direct criticism, tough questions
    SUPPORTER = "supporter"    # Encouraging, constructive feedback


class ActionStyle(Enum):
    """What kind of solutions the agent prefers."""
    INNOVATIVE = "innovative"  # Novel, experimental approaches
    PRAGMATIC = "pragmatic"    # Proven, practical solutions


@dataclass
class Personality:
    """
    Agent personality configuration.

    Combines 4 axes to create unique agent behaviors.
    """
    thinking: ThinkingStyle
    decision: DecisionStyle
    communication: CommunicationStyle
    action: ActionStyle

    def get_trait_description(self) -> str:
        """Get human-readable trait description."""
        traits = []

        if self.thinking == ThinkingStyle.OPTIMISTIC:
            traits.append("낙관적")
        else:
            traits.append("신중한")

        if self.decision == DecisionStyle.INTUITIVE:
            traits.append("직관적")
        else:
            traits.append("분석적")

        if self.communication == CommunicationStyle.CHALLENGER:
            traits.append("도전적")
        else:
            traits.append("지지적")

        if self.action == ActionStyle.INNOVATIVE:
            traits.append("혁신적")
        else:
            traits.append("실용적")

        return ", ".join(traits)

    def get_behavior_modifiers(self) -> Dict[str, str]:
        """
        Get behavior modifiers based on personality.

        These are used to construct system prompts.
        """
        modifiers = {}

        # Thinking style modifiers
        if self.thinking == ThinkingStyle.OPTIMISTIC:
            modifiers["initial_reaction"] = "가능성과 기회를 먼저 본다"
            modifiers["problem_approach"] = "해결책 중심으로 생각한다"
            modifiers["default_stance"] = "긍정적인 관점에서 시작한다"
        else:
            modifiers["initial_reaction"] = "리스크와 문제점을 먼저 본다"
            modifiers["problem_approach"] = "잠재적 실패 요인을 먼저 분석한다"
            modifiers["default_stance"] = "비판적인 관점에서 검토한다"

        # Decision style modifiers
        if self.decision == DecisionStyle.INTUITIVE:
            modifiers["decision_speed"] = "빠르게 직감으로 판단한다"
            modifiers["evidence_need"] = "경험과 패턴 기반으로 결정한다"
            modifiers["analysis_depth"] = "핵심만 빠르게 파악한다"
        else:
            modifiers["decision_speed"] = "충분한 데이터 수집 후 판단한다"
            modifiers["evidence_need"] = "수치와 근거를 요구한다"
            modifiers["analysis_depth"] = "체계적으로 분석한다"

        # Communication style modifiers
        if self.communication == CommunicationStyle.CHALLENGER:
            modifiers["feedback_style"] = "날카로운 질문과 반박을 제기한다"
            modifiers["disagreement"] = "문제점을 직접적으로 지적한다"
            modifiers["tone"] = "직설적이고 도전적이다"
        else:
            modifiers["feedback_style"] = "격려와 발전적 피드백을 준다"
            modifiers["disagreement"] = "대안을 제시하며 부드럽게 반대한다"
            modifiers["tone"] = "따뜻하고 건설적이다"

        # Action style modifiers
        if self.action == ActionStyle.INNOVATIVE:
            modifiers["solution_preference"] = "새롭고 파격적인 접근을 선호한다"
            modifiers["risk_tolerance"] = "실험적 시도를 두려워하지 않는다"
            modifiers["change_attitude"] = "변화와 혁신을 추구한다"
        else:
            modifiers["solution_preference"] = "검증된 방법을 선호한다"
            modifiers["risk_tolerance"] = "안정적이고 예측 가능한 방법을 택한다"
            modifiers["change_attitude"] = "점진적 개선을 선호한다"

        return modifiers

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "thinking": self.thinking.value,
            "decision": self.decision.value,
            "communication": self.communication.value,
            "action": self.action.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Personality":
        """Create from dictionary."""
        return cls(
            thinking=ThinkingStyle(data["thinking"]),
            decision=DecisionStyle(data["decision"]),
            communication=CommunicationStyle(data["communication"]),
            action=ActionStyle(data["action"]),
        )


# Pre-defined personality archetypes
PERSONALITY_ARCHETYPES = {
    "visionary": Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.INNOVATIVE,
    ),
    "critic": Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.PRAGMATIC,
    ),
    "builder": Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.PRAGMATIC,
    ),
    "disruptor": Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.INNOVATIVE,
    ),
    "guardian": Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.PRAGMATIC,
    ),
    "explorer": Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.INNOVATIVE,
    ),
    "analyst": Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.INNOVATIVE,
    ),
    "mentor": Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.PRAGMATIC,
    ),
}
