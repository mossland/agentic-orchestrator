"""
Debate protocol for agent interactions.

Defines the rules and flow for multi-stage debates with diverse agent personas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class DebatePhase(Enum):
    """Debate phase types."""
    DIVERGENCE = "divergence"     # Generate diverse ideas
    CONVERGENCE = "convergence"   # Filter and merge ideas
    PLANNING = "planning"         # Create actionable plans


class MessageType(Enum):
    """Types of debate messages."""
    INITIAL_IDEA = "initial_idea"
    ANALYSIS = "analysis"
    FEEDBACK = "feedback"
    CHALLENGE = "challenge"
    SUPPORT = "support"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    VOTE = "vote"
    PLAN_DRAFT = "plan_draft"
    PLAN_REVIEW = "plan_review"
    FINAL_PLAN = "final_plan"


@dataclass
class DebateMessage:
    """A single message in the debate."""
    id: str
    phase: DebatePhase
    round: int
    agent_id: str
    agent_name: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    references: List[str] = field(default_factory=list)  # IDs of referenced messages
    score: Optional[float] = None  # Relevance/quality score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "phase": self.phase.value,
            "round": self.round,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "references": self.references,
            "score": self.score,
        }


@dataclass
class DebateRound:
    """A single round within a phase."""
    round_num: int
    phase: DebatePhase
    topic: str
    messages: List[DebateMessage] = field(default_factory=list)
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, message: DebateMessage):
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "phase": self.phase.value,
            "topic": self.topic,
            "messages": [m.to_dict() for m in self.messages],
            "summary": self.summary,
            "key_points": self.key_points,
            "decisions": self.decisions,
        }


@dataclass
class PhaseResult:
    """Result of a debate phase."""
    phase: DebatePhase
    rounds: List[DebateRound]
    output: Dict[str, Any]
    duration_seconds: float
    total_tokens: int
    total_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "rounds": [r.to_dict() for r in self.rounds],
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }


@dataclass
class DebateProtocolConfig:
    """Configuration for debate protocol."""
    # Divergence phase
    divergence_rounds: int = 3
    divergence_agents_per_round: int = 8
    min_ideas_to_generate: int = 20

    # Convergence phase
    convergence_rounds: int = 2
    convergence_agents_per_round: int = 4
    top_ideas_to_keep: int = 5
    merge_threshold: float = 0.7  # Similarity threshold for merging

    # Planning phase
    planning_rounds: int = 2
    planning_agents_per_round: int = 5
    require_unanimous_approval: bool = False
    min_approval_ratio: float = 0.7

    # General settings
    max_tokens_per_response: int = 2000
    temperature_divergence: float = 0.9  # Higher for creativity
    temperature_convergence: float = 0.5  # Lower for analysis
    temperature_planning: float = 0.7

    # Timeouts
    agent_timeout_seconds: int = 120
    round_timeout_seconds: int = 600

    def to_dict(self) -> Dict[str, Any]:
        return {
            "divergence_rounds": self.divergence_rounds,
            "divergence_agents_per_round": self.divergence_agents_per_round,
            "min_ideas_to_generate": self.min_ideas_to_generate,
            "convergence_rounds": self.convergence_rounds,
            "convergence_agents_per_round": self.convergence_agents_per_round,
            "top_ideas_to_keep": self.top_ideas_to_keep,
            "merge_threshold": self.merge_threshold,
            "planning_rounds": self.planning_rounds,
            "planning_agents_per_round": self.planning_agents_per_round,
            "require_unanimous_approval": self.require_unanimous_approval,
            "min_approval_ratio": self.min_approval_ratio,
            "max_tokens_per_response": self.max_tokens_per_response,
            "temperature_divergence": self.temperature_divergence,
            "temperature_convergence": self.temperature_convergence,
            "temperature_planning": self.temperature_planning,
        }


class DebateProtocol:
    """
    Protocol for managing multi-stage debates.

    Defines rules for:
    - Agent participation order
    - Message types allowed per phase
    - Scoring and evaluation criteria
    - Termination conditions
    """

    # Allowed message types per phase
    PHASE_MESSAGE_TYPES = {
        DebatePhase.DIVERGENCE: [
            MessageType.INITIAL_IDEA,
            MessageType.ANALYSIS,
            MessageType.FEEDBACK,
            MessageType.CHALLENGE,
            MessageType.SUPPORT,
        ],
        DebatePhase.CONVERGENCE: [
            MessageType.EVALUATION,
            MessageType.SYNTHESIS,
            MessageType.VOTE,
            MessageType.FEEDBACK,
        ],
        DebatePhase.PLANNING: [
            MessageType.PLAN_DRAFT,
            MessageType.PLAN_REVIEW,
            MessageType.FEEDBACK,
            MessageType.FINAL_PLAN,
        ],
    }

    def __init__(self, config: Optional[DebateProtocolConfig] = None):
        self.config = config or DebateProtocolConfig()

    def get_allowed_message_types(self, phase: DebatePhase) -> List[MessageType]:
        """Get allowed message types for a phase."""
        return self.PHASE_MESSAGE_TYPES.get(phase, [])

    def validate_message(self, message: DebateMessage) -> tuple[bool, str]:
        """
        Validate a debate message.

        Returns:
            (is_valid, error_message)
        """
        allowed_types = self.get_allowed_message_types(message.phase)
        if message.message_type not in allowed_types:
            return False, f"Message type {message.message_type} not allowed in {message.phase}"

        if not message.content or len(message.content.strip()) < 10:
            return False, "Message content too short"

        return True, ""

    def should_end_phase(
        self,
        phase: DebatePhase,
        current_round: int,
        messages: List[DebateMessage],
        ideas_count: int = 0,
    ) -> tuple[bool, str]:
        """
        Check if a phase should end.

        Returns:
            (should_end, reason)
        """
        if phase == DebatePhase.DIVERGENCE:
            if current_round >= self.config.divergence_rounds:
                return True, "max_rounds_reached"
            if ideas_count >= self.config.min_ideas_to_generate:
                return True, "sufficient_ideas"

        elif phase == DebatePhase.CONVERGENCE:
            if current_round >= self.config.convergence_rounds:
                return True, "max_rounds_reached"

        elif phase == DebatePhase.PLANNING:
            if current_round >= self.config.planning_rounds:
                return True, "max_rounds_reached"
            # Check for consensus
            if self._check_consensus(messages):
                return True, "consensus_reached"

        return False, "continue"

    def _check_consensus(self, messages: List[DebateMessage]) -> bool:
        """Check if planning phase reached consensus."""
        votes = [m for m in messages if m.message_type == MessageType.VOTE]
        if not votes:
            return False

        approvals = sum(1 for v in votes if "approve" in v.content.lower() or "찬성" in v.content)
        total = len(votes)

        if self.config.require_unanimous_approval:
            return approvals == total

        return (approvals / total) >= self.config.min_approval_ratio if total > 0 else False

    def get_temperature(self, phase: DebatePhase) -> float:
        """Get recommended temperature for a phase."""
        temps = {
            DebatePhase.DIVERGENCE: self.config.temperature_divergence,
            DebatePhase.CONVERGENCE: self.config.temperature_convergence,
            DebatePhase.PLANNING: self.config.temperature_planning,
        }
        return temps.get(phase, 0.7)

    def create_divergence_prompt(
        self,
        topic: str,
        context: str,
        agent_personality: Dict[str, str],
        round_num: int,
        previous_ideas: List[str],
    ) -> str:
        """Create prompt for divergence phase."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        previous_section = ""
        if previous_ideas:
            previous_section = f"""
이전 라운드에서 제안된 아이디어들:
{chr(10).join(f"- {idea}" for idea in previous_ideas[:10])}

위 아이디어들과 다른 새로운 관점을 제시해주세요.
"""

        return f"""당신은 다음과 같은 성향을 가진 전문가입니다:
{personality_desc}

## 토론 주제
{topic}

## 배경 정보
{context}

{previous_section}

## 지시사항
당신의 성향과 전문성을 바탕으로 이 주제에 대한 의견을 제시해주세요.

1. **핵심 분석**: 이 주제의 가장 중요한 측면은 무엇인가?
2. **기회 또는 리스크**: 당신의 관점에서 어떤 기회/리스크가 보이는가?
3. **제안**: 구체적인 아이디어나 접근법을 제시하라
4. **우선순위**: 무엇부터 해야 하는가?

당신의 고유한 관점을 명확하게 드러내주세요.
라운드 {round_num}의 발언입니다.
"""

    def create_convergence_prompt(
        self,
        topic: str,
        ideas: List[Dict[str, Any]],
        agent_personality: Dict[str, str],
        round_num: int,
    ) -> str:
        """Create prompt for convergence phase."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        ideas_section = ""
        for i, idea in enumerate(ideas, 1):
            ideas_section += f"""
### 아이디어 {i}: {idea.get('title', 'Untitled')}
제안자: {idea.get('agent', 'Unknown')}
내용: {idea.get('content', '')}
점수: {idea.get('score', 'N/A')}
"""

        return f"""당신은 다음과 같은 성향을 가진 평가 전문가입니다:
{personality_desc}

## 토론 주제
{topic}

## 평가할 아이디어들
{ideas_section}

## 평가 기준
1. **실현 가능성** (1-10): 실제로 구현할 수 있는가?
2. **영향력** (1-10): Mossland 생태계에 미치는 영향
3. **혁신성** (1-10): 기존 접근과 얼마나 다른가?
4. **리스크** (1-10): 실패 위험이 얼마나 큰가?
5. **시급성** (1-10): 지금 해야 하는가?

## 지시사항
1. 각 아이디어에 대해 위 기준으로 점수를 매기세요
2. 상위 3개 아이디어를 선정하고 이유를 설명하세요
3. 유사한 아이디어가 있다면 통합 방안을 제시하세요
4. 최종 추천 아이디어를 선정하세요

라운드 {round_num}의 평가입니다.
"""

    def create_planning_prompt(
        self,
        topic: str,
        selected_ideas: List[Dict[str, Any]],
        agent_personality: Dict[str, str],
        agent_expertise: str,
        round_num: int,
        draft_plan: Optional[str] = None,
    ) -> str:
        """Create prompt for planning phase."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        ideas_section = "\n".join(
            f"- {idea.get('title', 'Untitled')}: {idea.get('summary', idea.get('content', '')[:200])}"
            for idea in selected_ideas
        )

        if draft_plan:
            return f"""당신은 {agent_expertise} 전문가로서 다음과 같은 성향을 가지고 있습니다:
{personality_desc}

## 토론 주제
{topic}

## 현재 기획안 초안
{draft_plan}

## 지시사항
{agent_expertise}의 관점에서 이 기획안을 검토하고 피드백을 제공하세요:

1. **강점**: 이 기획안의 좋은 점
2. **약점**: 개선이 필요한 부분
3. **리스크**: 예상되는 위험 요소
4. **구체적 제안**: 어떻게 개선할 수 있는가?

최종적으로 이 기획안을 [승인/수정요청/반대] 중 하나로 판단해주세요.
라운드 {round_num}의 검토입니다.
"""
        else:
            return f"""당신은 {agent_expertise} 전문가로서 다음과 같은 성향을 가지고 있습니다:
{personality_desc}

## 토론 주제
{topic}

## 선정된 아이디어들
{ideas_section}

## 지시사항
위 아이디어들을 바탕으로 실행 기획안을 작성하세요:

### 1. 개요
- 프로젝트 명
- 목표
- 예상 기간

### 2. 실행 계획
- 단계별 task
- 각 단계의 담당자/리소스
- 마일스톤

### 3. 리스크 관리
- 예상 리스크
- 대응 방안

### 4. 성과 지표
- KPI
- 측정 방법

당신의 전문성({agent_expertise})이 드러나는 기획안을 작성하세요.
라운드 {round_num}의 기획입니다.
"""

    def format_debate_summary(
        self,
        phase_results: List[PhaseResult],
        final_plan: str,
    ) -> str:
        """Format complete debate summary."""
        summary_parts = [
            "# 멀티 에이전트 토론 결과",
            "",
            f"생성 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]

        # Phase summaries
        for result in phase_results:
            phase_name = {
                DebatePhase.DIVERGENCE: "발산 단계 (Divergence)",
                DebatePhase.CONVERGENCE: "수렴 단계 (Convergence)",
                DebatePhase.PLANNING: "기획 단계 (Planning)",
            }.get(result.phase, result.phase.value)

            summary_parts.append(f"## {phase_name}")
            summary_parts.append(f"- 라운드 수: {len(result.rounds)}")
            summary_parts.append(f"- 소요 시간: {result.duration_seconds:.1f}초")
            summary_parts.append(f"- 토큰 사용량: {result.total_tokens:,}")
            summary_parts.append(f"- 비용: ${result.total_cost:.4f}")
            summary_parts.append("")

            if result.output:
                if result.phase == DebatePhase.DIVERGENCE:
                    ideas = result.output.get("ideas", [])
                    summary_parts.append(f"### 생성된 아이디어: {len(ideas)}개")
                    for idea in ideas[:5]:
                        summary_parts.append(f"- {idea.get('title', 'Untitled')}")

                elif result.phase == DebatePhase.CONVERGENCE:
                    selected = result.output.get("selected_ideas", [])
                    summary_parts.append(f"### 선정된 아이디어: {len(selected)}개")
                    for idea in selected:
                        summary_parts.append(f"- {idea.get('title', 'Untitled')} (점수: {idea.get('score', 'N/A')})")

                elif result.phase == DebatePhase.PLANNING:
                    summary_parts.append("### 기획 검토 결과")
                    approvals = result.output.get("approvals", 0)
                    total = result.output.get("total_votes", 0)
                    summary_parts.append(f"- 승인: {approvals}/{total}")

            summary_parts.append("")

        # Final plan
        summary_parts.append("---")
        summary_parts.append("")
        summary_parts.append("# 최종 기획안")
        summary_parts.append("")
        summary_parts.append(final_plan)

        return "\n".join(summary_parts)
