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
당신의 성향과 전문성을 바탕으로 이 주제에 대한 **구체적이고 실행 가능한 아이디어**를 제시해주세요.

### 아이디어 작성 규칙 (반드시 준수)

**제목 규칙:**
- 반드시 `## 아이디어: [제목]` 형식으로 시작하세요
- 제목은 최소 30자 이상, 구체적이고 설명적으로 작성
- 나쁜 예: "AI 활용 서비스", "토큰 이코노미 개선"
- 좋은 예: "GPT-5 기반 DeFi 포지션 자동 리밸런싱 에이전트 개발", "Mossland NFT 홀더를 위한 실시간 메타버스 자산 가치 트래커"

**내용 규칙:**
각 아이디어에 대해 다음 섹션을 **반드시 포함**하세요:

1. **핵심 분석** (100자 이상)
   - 현재 시장/기술 상황 분석
   - 왜 지금 이 아이디어가 필요한지 구체적 근거

2. **기회 또는 리스크** (150자 이상)
   - 정량적 데이터나 구체적 사례 포함
   - 경쟁 서비스와의 차별점

3. **구체적 제안** (200자 이상)
   - 핵심 기능 3-5개 나열
   - 기술 스택 제안 (예: Next.js, Solidity, Python 등)
   - MVP 범위 정의

4. **실행 로드맵** (100자 이상)
   - 1주차, 2주차 등 구체적 일정
   - 필요 리소스 (개발자 수, 예상 비용 등)

5. **성공 지표**
   - 측정 가능한 KPI 2-3개
   - 목표 수치 포함 (예: "출시 1개월 내 DAU 500명")

당신의 전문성이 드러나는 깊이 있는 분석과 제안을 해주세요.
라운드 {round_num}의 발언입니다.

---

### 📝 출력 형식 (아래 JSON 구조를 반드시 사용하세요)

```json
{{
  "idea_title": "30자 이상의 구체적인 제목 (기술명, 프로젝트명, 수치 포함 필수)",
  "core_analysis": "현재 시장/기술 상황 분석 (100자 이상)",
  "opportunity_risk": {{
    "opportunities": "기회 요인 (100자 이상, 정량적 데이터 포함)",
    "risks": "리스크 요인 (50자 이상)",
    "differentiators": "경쟁 서비스 대비 차별점"
  }},
  "proposal": {{
    "description": "구체적 제안 설명 (200자 이상)",
    "core_features": ["핵심 기능 1", "핵심 기능 2", "핵심 기능 3"],
    "tech_stack": ["React/Next.js", "Python/FastAPI", "Solidity"],
    "mvp_scope": "MVP 범위 정의"
  }},
  "roadmap": {{
    "week1": "1주차 계획",
    "week2": "2주차 계획",
    "resources": "필요 리소스 (개발자 수, 예상 비용)"
  }},
  "kpis": [
    {{"metric": "DAU", "target": "500명", "measurement": "Analytics 대시보드"}},
    {{"metric": "거래량", "target": "$10,000/일", "measurement": "On-chain 데이터"}}
  ]
}}
```

⚠️ **중요**: 위 JSON 형식을 정확히 따라야 합니다. 형식이 맞지 않으면 아이디어가 저장되지 않습니다.
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

## 평가 기준 (가중치 적용 - 각 항목에 대해 상세한 평가 근거 작성 필수)

**가중치 배분:**
- 실현 가능성: 25%
- Mossland 관련성: 20%
- **참신성: 30%** ⬆️ (가장 중요 - 기존 솔루션과의 차별화)
- 영향력: 15%
- 시급성: 10%

1. **실현 가능성** (1-10, 가중치 25%)
   - 1-2주 내 MVP 구현 가능성
   - 필요한 기술 스택의 성숙도
   - 팀 역량 대비 복잡도

2. **Mossland 관련성** (1-10, 가중치 20%)
   - Mossland 생태계 내 시너지 효과
   - MOC 토큰 또는 NFT 활용
   - 커뮤니티 가치 창출

3. **참신성** (1-10, 가중치 30%) ⭐ 핵심 기준
   - 기존 시장 솔루션 대비 차별점
   - 기술적 새로움
   - 비즈니스 모델 혁신성
   - ⚠️ 유사한 아이디어가 이미 있다면 낮은 점수
   - 💡 완전히 새로운 접근 방식이면 높은 점수

4. **영향력** (1-10, 가중치 15%)
   - 신규 사용자 유입 잠재력
   - 수익 모델 가능성
   - 바이럴 성장 가능성

5. **시급성** (1-10, 가중치 10%)
   - 시장 타이밍
   - 경쟁사 동향
   - Mossland 로드맵 적합성

## 지시사항

### 각 아이디어별 상세 평가 (반드시 작성)
```
### 아이디어 N: [제목]
- 실현 가능성: X/10 - [구체적 근거 50자 이상]
- 영향력: X/10 - [구체적 근거 50자 이상]
- 혁신성: X/10 - [구체적 근거 50자 이상]
- 리스크: X/10 - [구체적 근거 50자 이상]
- 시급성: X/10 - [구체적 근거 50자 이상]
- **총점**: XX/50
```

### 최종 분석
1. **상위 3개 아이디어** 선정 및 선정 이유 (각 100자 이상)
   - 참신성(30% 가중치)을 특히 중요하게 평가하세요
2. **유사 아이디어 통합 방안** (있는 경우)
   - 중복되는 아이디어는 과감히 병합하거나 낮은 점수 부여
3. **최종 추천**: 1개 아이디어와 추천 이유 (150자 이상)
   - 가장 참신하면서도 실현 가능한 아이디어 선택

### 가중치 점수 계산
```
최종점수 = (실현가능성 × 0.25) + (관련성 × 0.20) + (참신성 × 0.30) + (영향력 × 0.15) + (시급성 × 0.10)
```

라운드 {round_num}의 평가입니다. 참신성을 가장 중요하게 평가해주세요.
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
위 아이디어들을 바탕으로 **상세하고 실행 가능한 기획안**을 작성하세요.

### 기획안 작성 규칙 (반드시 준수)

**프로젝트 제목 규칙:**
- 제목은 최소 30자 이상, 프로젝트의 핵심 가치를 담아야 함
- 나쁜 예: "DeFi 도구", "NFT 플랫폼"
- 좋은 예: "Mossland 생태계 연동 AI 기반 DeFi 포트폴리오 자동 리밸런싱 시스템"

---

### 1. 프로젝트 개요 (상세히 작성)
- **프로젝트 명**: [구체적이고 설명적인 이름]
- **한 줄 설명**: [50자 이내로 핵심 가치 설명]
- **목표**: [달성하고자 하는 구체적 목표 3개 이상]
- **대상 사용자**: [누가 사용할 것인지, 예상 사용자 수]
- **예상 기간**: [총 개발 기간, MVP vs 풀버전]
- **예상 비용**: [인건비, 인프라 비용 등]

### 2. 기술 아키텍처
- **프론트엔드**: [React/Next.js/Vue 등 + 선택 이유]
- **백엔드**: [Python/Node.js 등 + 선택 이유]
- **데이터베이스**: [PostgreSQL/MongoDB 등 + 선택 이유]
- **블록체인 연동**: [어떤 체인, 어떤 프로토콜]
- **외부 API**: [사용할 외부 서비스]
- **시스템 아키텍처 다이어그램**: [텍스트로 간단히 설명]

### 3. 상세 실행 계획

#### Week 1: 기반 구축
- [ ] Task 1: [구체적인 작업 내용]
- [ ] Task 2: [구체적인 작업 내용]
- **마일스톤**: [이 주차 완료 조건]

#### Week 2: 핵심 기능 개발
- [ ] Task 1: [구체적인 작업 내용]
- [ ] Task 2: [구체적인 작업 내용]
- **마일스톤**: [이 주차 완료 조건]

### 4. 리스크 관리
| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|
| [구체적 리스크] | 높음/중간/낮음 | 상/중/하 | [대응책] |

### 5. 성과 지표 (KPI)
| 지표 | 목표 | 측정 방법 | 측정 주기 |
|------|------|----------|----------|
| DAU | 500명 | Analytics | 일간 |
| 거래량 | $10,000/일 | On-chain 데이터 | 일간 |

### 6. 향후 확장 계획
- Phase 2 기능: [...]
- 장기 비전: [...]

당신의 전문성({agent_expertise})이 드러나는 깊이 있고 실행 가능한 기획안을 작성하세요.
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
