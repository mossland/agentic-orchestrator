# Agentic Orchestrator v0.4.0 업그레이드 계획 보완

> UPGRADE_PLAN.md의 보완 문서
> 작성일: 2026-01-22

---

## 목차

1. [웹사이트 디자인 (Vibe Labs 스타일)](#1-웹사이트-디자인-vibe-labs-스타일)
2. [다양한 페르소나 에이전트 시스템](#2-다양한-페르소나-에이전트-시스템)
3. [데이터베이스 기반 장기 운영 아키텍처](#3-데이터베이스-기반-장기-운영-아키텍처)

---

## 1. 웹사이트 디자인 (Vibe Labs 스타일)

### 1.1 디자인 레퍼런스 분석 (vibelabs.hashed.com)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Vibe Labs 핵심 디자인 요소                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  • 터미널/CLI 인터페이스 모방                                            │
│  • 시스템 리소스 표시 (MEM: 48MB CPU: 2%)                               │
│  • "> 명령어를 입력하세요..." 프롬프트 스타일                            │
│  • JetBrains Mono + Pretendard (한글) 폰트                              │
│  • 다크 테마 + 네온 악센트                                              │
│  • 미니멀하지만 기술적인 느낌                                           │
│  • 이중 언어 지원 (한국어/EN)                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 새로운 디자인 시스템

#### 컬러 팔레트

```css
:root {
  /* 배경 */
  --bg-primary: #0a0a0a;           /* 깊은 검정 */
  --bg-secondary: #111111;          /* 약간 밝은 검정 */
  --bg-tertiary: #1a1a1a;           /* 패널 배경 */
  --bg-terminal: #0d0d0d;           /* 터미널 배경 */
  --bg-hover: #1f1f1f;              /* 호버 상태 */

  /* 텍스트 */
  --text-primary: #ffffff;          /* 주요 텍스트 */
  --text-secondary: #a0a0a0;        /* 보조 텍스트 */
  --text-muted: #666666;            /* 음소거 텍스트 */
  --text-accent: #00ff88;           /* 강조 (민트 그린) */

  /* 악센트 컬러 */
  --accent-green: #00ff88;          /* 민트 그린 (주요) */
  --accent-blue: #00d4ff;           /* 사이버 블루 */
  --accent-purple: #a855f7;         /* 퍼플 */
  --accent-orange: #ff6b35;         /* 오렌지 */
  --accent-pink: #ff0080;           /* 핫 핑크 */
  --accent-yellow: #ffd700;         /* 골드 */

  /* 상태 컬러 */
  --status-success: #00ff88;
  --status-warning: #ffb800;
  --status-error: #ff3366;
  --status-info: #00d4ff;

  /* 보더 */
  --border-subtle: #222222;
  --border-default: #333333;
  --border-accent: #00ff8840;

  /* 그림자 */
  --glow-green: 0 0 20px #00ff8820;
  --glow-blue: 0 0 20px #00d4ff20;
}
```

#### 타이포그래피

```css
:root {
  /* 폰트 패밀리 */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  --font-sans: 'Pretendard Variable', 'Inter', -apple-system, sans-serif;

  /* 폰트 사이즈 */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.875rem;     /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 2rem;        /* 32px */
}

/* 코드/터미널 텍스트 */
.mono {
  font-family: var(--font-mono);
  font-feature-settings: 'liga' 1, 'calt' 1;
}

/* 본문 텍스트 */
.sans {
  font-family: var(--font-sans);
  font-weight: 400;
}
```

### 1.3 새로운 레이아웃 디자인

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─ HEADER ─────────────────────────────────────────────────────────────────┐│
│ │  AGENTIC ORCHESTRATOR                    MEM: 2.4GB  CPU: 12%  ◉ ONLINE ││
│ │  v0.4.0 "Signal Storm"                   [한국어 ▼] [⚙ Settings]        ││
│ └──────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─ SIGNALS ──────────────────┐ ┌─ LIVE DEBATE ─────────────────────────────┐│
│ │                            │ │                                           ││
│ │  ▸ RSS Feeds      45/45 ◉  │ │  DIVERGENCE PHASE  Round 2/3             ││
│ │  ▸ GitHub Events  25/25 ◉  │ │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━         ││
│ │  ▸ OnChain        ETH ◉    │ │                                           ││
│ │  ▸ Social         12/12 ◉  │ │  ┌─ @OptimisticDev ─────────────────────┐ ││
│ │  ▸ News API       4/4 ◉    │ │  │ "이 아이디어는 React Server          │ ││
│ │                            │ │  │ Components와 결합하면 더 강력해질    │ ││
│ │  ─────────────────────────│ │  │ 수 있을 것 같아요! 특히..."           │ ││
│ │                            │ │  └─────────────────────────────────────┘ ││
│ │  LATEST SIGNALS            │ │                                           ││
│ │                            │ │  ┌─ @CautiousArchitect ─────────────────┐ ││
│ │  • EIP-7702 discussion     │ │  │ "잠깐, 보안 측면을 먼저 고려해야     │ ││
│ │    ethereum/EIPs #trending │ │  │ 합니다. 이 방식은 공격 벡터가..."     │ ││
│ │                            │ │  └─────────────────────────────────────┘ ││
│ │  • Solana Firedancer       │ │                                           ││
│ │    GitHub 2.3k ★ today     │ │  ┌─ @VisionaryFounder ──────────────────┐ ││
│ │                            │ │  │ "두 의견 모두 좋습니다. 보안을        │ ││
│ │  • MOC whale movement      │ │  │ 유지하면서 혁신적인 방향으로..."      │ ││
│ │    +500k tokens transfer   │ │  └─────────────────────────────────────┘ ││
│ │                            │ │                                           ││
│ └────────────────────────────┘ └───────────────────────────────────────────┘│
│ ┌─ PROCESSES ────────────────┐ ┌─ OUTPUT ──────────────────────────────────┐│
│ │                            │ │                                           ││
│ │  PID   NAME         STATUS │ │  ▸ 15:42:01  Idea #47 generated          ││
│ │  ────────────────────────  │ │  ▸ 15:41:45  Divergence round 2 started  ││
│ │  2401  signal-fetch  ◉ RUN │ │  ▸ 15:40:22  Signal batch processed      ││
│ │  2402  debate-main   ◉ RUN │ │  ▸ 15:38:11  GitHub adapter: 15 events   ││
│ │  2403  llm-router    ◉ RUN │ │  ▸ 15:35:00  OnChain: MOC activity +23%  ││
│ │  2404  ws-server     ◉ RUN │ │                                           ││
│ │  2405  budget-mon    ○ IDLE│ │  [View Full Logs →]                       ││
│ │                            │ │                                           ││
│ └────────────────────────────┘ └───────────────────────────────────────────┘│
│ ┌─ BUDGET ───────────────────┐ ┌─ IDEAS ───────────────────────────────────┐│
│ │                            │ │                                           ││
│ │  TODAY      $12.40 / $50   │ │  PENDING    12  ━━━━━━━━━━━━━━━━━━━━━━━  ││
│ │  ████████░░░░░░░░  24.8%   │ │  IN DEBATE   3  ━━━━━━━                   ││
│ │                            │ │  SELECTED    5  ━━━━━━━━━━               ││
│ │  MONTH     $342 / $1,500   │ │  PLANNED     8  ━━━━━━━━━━━━━            ││
│ │  █████░░░░░░░░░░░  22.8%   │ │                                           ││
│ │                            │ │  [View Backlog →]                         ││
│ └────────────────────────────┘ └───────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─ TERMINAL ───────────────────────────────────────────────────────────────┐│
│ │  > _                                                                     ││
│ │                                                                          ││
│ │  ┌─ COMMANDS ──────────────────────────────────────────────────────────┐ ││
│ │  │  [↑↓ Navigate]  [Enter Select]  [Esc Cancel]  [/ Search]            │ ││
│ │  │                                                                      │ ││
│ │  │  ▸ run cycle           전체 오케스트레이션 사이클 실행              │ ││
│ │  │    view signals        현재 신호 분석 보기                          │ ││
│ │  │    view debate         진행 중인 토론 세션 보기                     │ ││
│ │  │    view budget         API 사용량 및 예산 확인                      │ ││
│ │  │    view ideas          아이디어 백로그 보기                         │ ││
│ │  │    config              설정 수정                                    │ ││
│ │  └──────────────────────────────────────────────────────────────────────┘ ││
│ └──────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 모바일 레이아웃

```
┌─────────────────────────────┐
│ AGENTIC ORCHESTRATOR        │
│ ◉ ONLINE    MEM: 2.4GB      │
├─────────────────────────────┤
│ ┌─ TABS ──────────────────┐ │
│ │[SIGNALS][DEBATE][OUTPUT]│ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│                             │
│  ┌─ LIVE DEBATE ─────────┐  │
│  │                       │  │
│  │ DIVERGENCE  R2/3      │  │
│  │ ━━━━━━━━━━━━━━━━━━━━ │  │
│  │                       │  │
│  │ @OptimisticDev        │  │
│  │ "이 아이디어는 React  │  │
│  │ Server Components와   │  │
│  │ 결합하면..."          │  │
│  │                       │  │
│  │ @CautiousArchitect    │  │
│  │ "잠깐, 보안 측면을    │  │
│  │ 먼저 고려해야..."     │  │
│  │                       │  │
│  └───────────────────────┘  │
│                             │
├─────────────────────────────┤
│ ┌─ COMMAND BAR ───────────┐ │
│ │ > Tap to open commands  │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### 1.5 핵심 UI 컴포넌트

```typescript
// website/src/components/SystemStatus.tsx

export function SystemStatus() {
  const { memory, cpu, status } = useSystemMetrics();

  return (
    <div className="system-status font-mono text-sm">
      <span className="text-muted">MEM:</span>
      <span className="text-primary ml-1">{memory}</span>

      <span className="text-muted ml-4">CPU:</span>
      <span className="text-primary ml-1">{cpu}%</span>

      <span className={`ml-4 status-dot ${status}`}>◉</span>
      <span className="text-primary ml-1 uppercase">{status}</span>
    </div>
  );
}
```

```typescript
// website/src/components/DebateMessage.tsx

interface DebateMessageProps {
  agent: AgentPersona;
  message: string;
  timestamp: Date;
}

export function DebateMessage({ agent, message, timestamp }: DebateMessageProps) {
  return (
    <div className="debate-message bg-tertiary rounded-lg p-4 mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span
          className="agent-badge px-2 py-0.5 rounded text-xs font-mono"
          style={{ backgroundColor: agent.color + '20', color: agent.color }}
        >
          @{agent.handle}
        </span>
        <span className="text-muted text-xs">
          {formatTime(timestamp)}
        </span>
        <span className="personality-tag text-xs text-secondary">
          {agent.personality}
        </span>
      </div>
      <p className="text-primary text-sm leading-relaxed">
        "{message}"
      </p>
    </div>
  );
}
```

---

## 2. 다양한 페르소나 에이전트 시스템

### 2.1 성격 유형 프레임워크

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        성격 차원 (4가지 축)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 사고 스타일                                                         │
│     ├─ 낙관적 (Optimistic)     ←──────────→  신중한 (Cautious)         │
│     └─ 아이디어를 긍정적으로 봄    vs    리스크와 문제점 먼저 봄         │
│                                                                         │
│  2. 의사결정 방식                                                       │
│     ├─ 직관적 (Intuitive)      ←──────────→  분석적 (Analytical)       │
│     └─ 감으로 빠르게 판단         vs    데이터 기반 체계적 분석          │
│                                                                         │
│  3. 커뮤니케이션 스타일                                                 │
│     ├─ 도전적 (Challenger)     ←──────────→  지지적 (Supporter)        │
│     └─ 날카로운 질문과 반박       vs    격려와 발전적 피드백             │
│                                                                         │
│  4. 행동 성향                                                           │
│     ├─ 혁신적 (Innovative)     ←──────────→  실용적 (Pragmatic)        │
│     └─ 새롭고 파격적인 접근       vs    검증된 방법 선호                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 발산 단계 에이전트 (16명)

#### 기술 전문가 그룹 (8명)

| ID | 이름 | 직업 | 성격 | 모델 | 특징 |
|----|------|------|------|------|------|
| `dev_optimistic` | **Alex Kim** | Frontend Dev | 낙관적, 혁신적 | phi4:14b | 새로운 UI 패턴 적극 수용, "이거 가능해요!" |
| `dev_cautious` | **Sarah Park** | Frontend Dev | 신중한, 분석적 | qwen2.5:14b | 성능/접근성 우선, "브라우저 호환성은요?" |
| `eng_systematic` | **James Lee** | Backend Eng | 분석적, 실용적 | qwen2.5:14b | 시스템 설계 체계적, 확장성 중시 |
| `eng_creative` | **Mina Choi** | Backend Eng | 직관적, 혁신적 | phi4:14b | 새로운 아키텍처 제안, 실험적 |
| `chain_maximalist` | **David Hong** | Blockchain Expert | 혁신적, 도전적 | phi4:14b | "온체인으로 다 올리자!", 탈중앙화 극대화 |
| `chain_pragmatic` | **Emily Yoon** | Blockchain Expert | 실용적, 신중한 | qwen2.5:14b | 가스비 고려, 하이브리드 접근 |
| `security_paranoid` | **Chris Oh** | Security Researcher | 신중한, 도전적 | qwen2.5:32b | 모든 공격 벡터 고려, "이건 해킹당해요" |
| `infra_devops` | **Ryan Jung** | DevOps Engineer | 분석적, 실용적 | phi4:14b | 운영 관점, CI/CD, 모니터링 |

#### 디자인/제품 그룹 (4명)

| ID | 이름 | 직업 | 성격 | 모델 | 특징 |
|----|------|------|------|------|------|
| `design_bold` | **Luna Shin** | Product Designer | 혁신적, 낙관적 | qwen2.5:14b | 대담한 디자인, 트렌드 리더 |
| `design_minimal` | **Hana Kang** | UX Designer | 신중한, 분석적 | phi4:14b | 미니멀리즘, 사용자 리서치 기반 |
| `pm_visionary` | **Tony Baek** | Product Manager | 직관적, 혁신적 | qwen2.5:14b | 큰 그림 제시, 비전 중심 |
| `pm_execution` | **Jina Nam** | Product Manager | 분석적, 실용적 | phi4:14b | 실행 가능성, 마일스톤 |

#### 비즈니스/마케팅 그룹 (4명)

| ID | 이름 | 직업 | 성격 | 모델 | 특징 |
|----|------|------|------|------|------|
| `mkt_growth` | **Kevin Lim** | Growth Marketer | 낙관적, 도전적 | llama3.2:3b | 바이럴 성장, 공격적 마케팅 |
| `mkt_brand` | **Yuri Han** | Brand Strategist | 직관적, 지지적 | llama3.2:3b | 브랜드 스토리, 감성 마케팅 |
| `biz_analyst` | **Steve Kwon** | Business Analyst | 분석적, 신중한 | phi4:14b | 시장 데이터, 경쟁 분석 |
| `community_lead` | **Joy Song** | Community Manager | 지지적, 낙관적 | llama3.2:3b | 유저 피드백, 커뮤니티 인사이트 |

### 2.3 수렴 단계 에이전트 (8명)

| ID | 이름 | 직업 | 성격 | 모델 | 평가 관점 |
|----|------|------|------|------|----------|
| `vc_aggressive` | **Michael Chen** | VC Partner (Crypto) | 도전적, 혁신적 | qwen2.5:32b | "100배 성장 가능성은?" |
| `vc_conservative` | **Jennifer Kim** | VC Partner (Traditional) | 신중한, 분석적 | qwen2.5:32b | "유닛 이코노믹스가 맞나요?" |
| `accel_speed` | **Paul Ryu** | Accelerator Mentor | 낙관적, 실용적 | qwen2.5:32b | "빠르게 MVP 검증하세요" |
| `accel_deep` | **Grace Seo** | Accelerator Mentor | 분석적, 지지적 | qwen2.5:14b | "고객 페인포인트 깊게 파세요" |
| `founder_serial` | **Daniel Park** | Serial Entrepreneur | 직관적, 도전적 | llama3.3:70b | 3회 엑싯 경험, 패턴 인식 |
| `founder_first` | **Soyeon Lee** | First-time Founder | 낙관적, 혁신적 | qwen2.5:14b | 신선한 관점, 도메인 전문성 |
| `expert_tech` | **Dr. Hyun Cho** | Tech Domain Expert | 분석적, 신중한 | qwen2.5:32b | 기술 타당성 심층 검토 |
| `expert_market` | **Amy Hwang** | Market Expert | 분석적, 실용적 | qwen2.5:32b | 시장 규모, 타이밍 분석 |

### 2.4 기획 단계 에이전트 (10명)

| ID | 이름 | 직업 | 성격 | 모델 | 담당 영역 |
|----|------|------|------|------|----------|
| `cpo_vision` | **Marcus Ko** | CPO | 직관적, 혁신적 | llama3.3:70b | 제품 비전, 전체 방향 |
| `pm_detail` | **Lisa Jung** | Senior PM | 분석적, 실용적 | qwen2.5:32b | PRD 상세 작성 |
| `tech_lead` | **Andrew Yoo** | Tech Lead | 분석적, 신중한 | qwen2.5:32b | 기술 아키텍처 |
| `fe_lead` | **Nina Song** | Frontend Lead | 낙관적, 혁신적 | qwen2.5:14b | 프론트엔드 설계 |
| `be_lead` | **Jason Chung** | Backend Lead | 신중한, 분석적 | qwen2.5:14b | 백엔드/인프라 설계 |
| `chain_lead` | **Eric Moon** | Blockchain Lead | 혁신적, 도전적 | phi4:14b | 스마트 컨트랙트 설계 |
| `ux_research` | **Mia Jang** | UX Researcher | 분석적, 지지적 | phi4:14b | 사용자 리서치 |
| `qa_lead` | **Tom Ahn** | QA Lead | 신중한, 도전적 | phi4:14b | 테스트 전략 |
| `devrel` | **Anna Cho** | DevRel | 낙관적, 지지적 | llama3.2:3b | 개발자 경험, 문서화 |
| `project_mgr` | **Ben Park** | Project Manager | 실용적, 분석적 | qwen2.5:14b | 일정, 리소스, 리스크 |

### 2.5 에이전트 성격 정의

```python
# src/agentic_orchestrator/personas/personalities.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

class ThinkingStyle(Enum):
    OPTIMISTIC = "optimistic"
    CAUTIOUS = "cautious"

class DecisionStyle(Enum):
    INTUITIVE = "intuitive"
    ANALYTICAL = "analytical"

class CommunicationStyle(Enum):
    CHALLENGER = "challenger"
    SUPPORTER = "supporter"

class ActionStyle(Enum):
    INNOVATIVE = "innovative"
    PRAGMATIC = "pragmatic"

@dataclass
class Personality:
    thinking: ThinkingStyle
    decision: DecisionStyle
    communication: CommunicationStyle
    action: ActionStyle

    def get_behavior_modifiers(self) -> Dict[str, str]:
        """성격에 따른 행동 수정자 반환"""
        modifiers = {}

        if self.thinking == ThinkingStyle.OPTIMISTIC:
            modifiers["initial_reaction"] = "가능성과 기회를 먼저 본다"
            modifiers["problem_approach"] = "해결책 중심으로 생각한다"
        else:
            modifiers["initial_reaction"] = "리스크와 문제점을 먼저 본다"
            modifiers["problem_approach"] = "잠재적 실패 요인을 먼저 분석한다"

        if self.decision == DecisionStyle.INTUITIVE:
            modifiers["decision_speed"] = "빠르게 직감으로 판단한다"
            modifiers["evidence_need"] = "경험과 패턴 기반으로 결정한다"
        else:
            modifiers["decision_speed"] = "충분한 데이터 수집 후 판단한다"
            modifiers["evidence_need"] = "수치와 근거를 요구한다"

        if self.communication == CommunicationStyle.CHALLENGER:
            modifiers["feedback_style"] = "날카로운 질문과 반박을 제기한다"
            modifiers["disagreement"] = "문제점을 직접적으로 지적한다"
        else:
            modifiers["feedback_style"] = "격려와 발전적 피드백을 준다"
            modifiers["disagreement"] = "대안을 제시하며 부드럽게 반대한다"

        if self.action == ActionStyle.INNOVATIVE:
            modifiers["solution_preference"] = "새롭고 파격적인 접근을 선호한다"
            modifiers["risk_tolerance"] = "실험적 시도를 두려워하지 않는다"
        else:
            modifiers["solution_preference"] = "검증된 방법을 선호한다"
            modifiers["risk_tolerance"] = "안정적이고 예측 가능한 방법을 택한다"

        return modifiers


@dataclass
class AgentPersona:
    id: str
    name: str
    handle: str                    # @mention용 핸들
    role: str
    personality: Personality
    model: str
    color: str                     # UI 표시용 컬러
    expertise: List[str]
    catchphrase: str               # 캐릭터 특징적 표현
    system_prompt_template: str

    def build_system_prompt(self) -> str:
        """성격이 반영된 시스템 프롬프트 생성"""
        modifiers = self.personality.get_behavior_modifiers()

        return f"""당신은 {self.name}입니다. {self.role}로 활동하고 있습니다.

## 당신의 성격과 특징
{self._format_personality()}

## 행동 방식
- 초기 반응: {modifiers['initial_reaction']}
- 문제 접근: {modifiers['problem_approach']}
- 의사결정: {modifiers['decision_speed']}
- 근거 요구: {modifiers['evidence_need']}
- 피드백: {modifiers['feedback_style']}
- 반대 시: {modifiers['disagreement']}
- 해결책: {modifiers['solution_preference']}
- 리스크: {modifiers['risk_tolerance']}

## 전문 분야
{', '.join(self.expertise)}

## 특징적 표현
자주 "{self.catchphrase}"라고 말합니다.

{self.system_prompt_template}
"""

    def _format_personality(self) -> str:
        traits = []
        if self.personality.thinking == ThinkingStyle.OPTIMISTIC:
            traits.append("낙관적이고 긍정적")
        else:
            traits.append("신중하고 비판적")

        if self.personality.decision == DecisionStyle.INTUITIVE:
            traits.append("직관적 판단")
        else:
            traits.append("분석적 사고")

        if self.personality.communication == CommunicationStyle.CHALLENGER:
            traits.append("도전적 소통")
        else:
            traits.append("지지적 소통")

        if self.personality.action == ActionStyle.INNOVATIVE:
            traits.append("혁신 추구")
        else:
            traits.append("실용주의")

        return ", ".join(traits)
```

### 2.6 에이전트 정의 예시

```python
# src/agentic_orchestrator/personas/catalog.py

from .personalities import *

# 발산 단계 에이전트들

ALEX_KIM = AgentPersona(
    id="dev_optimistic",
    name="Alex Kim",
    handle="OptimisticDev",
    role="Senior Frontend Developer",
    personality=Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.INNOVATIVE
    ),
    model="phi4:14b",
    color="#00ff88",
    expertise=["React", "Next.js", "Web3 Frontend", "Animation"],
    catchphrase="이거 진짜 되겠는데요!",
    system_prompt_template="""
프론트엔드 관점에서 아이디어를 평가할 때:
- 사용자 경험이 혁신적인지 확인
- 새로운 UI 패턴 적용 가능성 탐색
- 기술적 도전을 기회로 봄
- 빠른 프로토타이핑 가능성 고려

항상 "할 수 있다"는 관점에서 시작하되,
실현 가능한 방법을 구체적으로 제시합니다.
"""
)

SARAH_PARK = AgentPersona(
    id="dev_cautious",
    name="Sarah Park",
    handle="CautiousArchitect",
    role="Staff Frontend Engineer",
    personality=Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.PRAGMATIC
    ),
    model="qwen2.5:14b",
    color="#00d4ff",
    expertise=["Performance", "Accessibility", "Testing", "Browser Compatibility"],
    catchphrase="잠깐, 이 부분 검토해봤어요?",
    system_prompt_template="""
프론트엔드 관점에서 아이디어를 평가할 때:
- 성능 영향을 먼저 고려
- 브라우저 호환성 문제 지적
- 접근성(A11y) 요구사항 확인
- 테스트 가능성 검토

문제점을 지적하되, 항상 대안을 함께 제시합니다.
"이건 문제가 있지만, 이렇게 하면 해결됩니다."
"""
)

CHRIS_OH = AgentPersona(
    id="security_paranoid",
    name="Chris Oh",
    handle="SecurityParanoid",
    role="Senior Security Researcher",
    personality=Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.ANALYTICAL,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.PRAGMATIC
    ),
    model="qwen2.5:32b",
    color="#ff3366",
    expertise=["Smart Contract Audit", "Penetration Testing", "Cryptography", "OWASP"],
    catchphrase="이건 해킹당할 수 있어요",
    system_prompt_template="""
보안 관점에서 아이디어를 평가할 때:
- 모든 공격 벡터를 고려
- 스마트 컨트랙트 취약점 분석
- 프라이버시 리스크 평가
- 규제 컴플라이언스 확인

보안 문제는 타협하지 않지만,
보안을 유지하면서 기능을 구현하는 방법을 제시합니다.
"""
)

DAVID_HONG = AgentPersona(
    id="chain_maximalist",
    name="David Hong",
    handle="ChainMaximalist",
    role="Blockchain Architect",
    personality=Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.INNOVATIVE
    ),
    model="phi4:14b",
    color="#a855f7",
    expertise=["Ethereum", "DeFi", "DAOs", "Tokenomics", "ZK Proofs"],
    catchphrase="온체인으로 다 올리자!",
    system_prompt_template="""
블록체인 관점에서 아이디어를 평가할 때:
- 탈중앙화 극대화 방안 모색
- 토큰 유틸리티 확장 가능성
- 온체인 거버넌스 적용
- 새로운 DeFi 메커니즘 제안

진정한 Web3의 가치는 탈중앙화입니다.
중앙화된 솔루션에 도전하고 대안을 제시합니다.
"""
)

# 수렴 단계 에이전트

MICHAEL_CHEN = AgentPersona(
    id="vc_aggressive",
    name="Michael Chen",
    handle="CryptoVC",
    role="Partner at Crypto Venture Capital",
    personality=Personality(
        thinking=ThinkingStyle.OPTIMISTIC,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.CHALLENGER,
        action=ActionStyle.INNOVATIVE
    ),
    model="qwen2.5:32b",
    color="#ffd700",
    expertise=["Crypto Investment", "Token Economics", "Growth Strategy", "Network Effects"],
    catchphrase="100배 갈 수 있는 거야?",
    system_prompt_template="""
투자자 관점에서 아이디어를 평가할 때:
- 100배 성장 가능성 평가
- 네트워크 효과 분석
- 토큰 가치 상승 메커니즘
- 시장 타이밍

큰 비전을 가진 프로젝트를 선호합니다.
작은 개선보다 시장을 바꿀 혁신을 찾습니다.
"""
)

DANIEL_PARK = AgentPersona(
    id="founder_serial",
    name="Daniel Park",
    handle="SerialFounder",
    role="Serial Entrepreneur (3x Exit)",
    personality=Personality(
        thinking=ThinkingStyle.CAUTIOUS,
        decision=DecisionStyle.INTUITIVE,
        communication=CommunicationStyle.SUPPORTER,
        action=ActionStyle.PRAGMATIC
    ),
    model="llama3.3:70b",
    color="#ff6b35",
    expertise=["Startup Strategy", "Team Building", "Fundraising", "Scaling"],
    catchphrase="예전에 해봤는데...",
    system_prompt_template="""
창업 경험을 바탕으로 아이디어를 평가할 때:
- 과거 성공/실패 패턴 인식
- 실행 가능성 현실적 평가
- 팀 구성 요구사항 분석
- 피벗 가능성 고려

경험에서 배운 교훈을 공유하고,
피할 수 있는 실수를 미리 경고합니다.
"""
)

# 전체 에이전트 목록
DIVERGENCE_AGENTS = [
    ALEX_KIM,
    SARAH_PARK,
    # ... 나머지 에이전트들
]

CONVERGENCE_AGENTS = [
    MICHAEL_CHEN,
    DANIEL_PARK,
    # ... 나머지 에이전트들
]

PLANNING_AGENTS = [
    # ... 기획 에이전트들
]
```

### 2.7 토론 다이나믹스

```python
# src/agentic_orchestrator/debate/dynamics.py

class DebateDynamics:
    """
    에이전트 간 상호작용 패턴

    자연스러운 토론을 위해:
    1. 성격에 따른 반응 패턴 적용
    2. 이전 발언 참조
    3. 동의/반대 명시
    4. 아이디어 발전/수정/통합
    """

    INTERACTION_PATTERNS = {
        # 낙관적 + 신중한 = 건설적 토론
        ("optimistic", "cautious"): {
            "dynamic": "constructive_tension",
            "expected_outcome": "균형 잡힌 아이디어"
        },

        # 혁신적 + 실용적 = 실현 가능한 혁신
        ("innovative", "pragmatic"): {
            "dynamic": "grounded_innovation",
            "expected_outcome": "실행 가능한 새로운 접근"
        },

        # 도전적 + 지지적 = 정제된 아이디어
        ("challenger", "supporter"): {
            "dynamic": "refinement",
            "expected_outcome": "강화된 논리와 완성도"
        }
    }

    async def generate_response(
        self,
        agent: AgentPersona,
        context: DebateContext,
        previous_messages: List[DebateMessage]
    ) -> DebateMessage:
        """에이전트 성격에 맞는 응답 생성"""

        # 이전 메시지 중 반응할 대상 선택
        target_message = self._select_response_target(agent, previous_messages)

        # 반응 유형 결정 (동의, 반대, 발전, 통합)
        reaction_type = self._determine_reaction_type(agent, target_message)

        # 프롬프트 구성
        prompt = self._build_response_prompt(
            agent=agent,
            target=target_message,
            reaction=reaction_type,
            context=context
        )

        # LLM 호출
        response = await self.llm_router.route(
            task_type="debate",
            prompt=prompt,
            model=agent.model
        )

        return DebateMessage(
            agent_id=agent.id,
            agent_name=agent.name,
            message_type=reaction_type,
            content=response,
            references=[target_message.id] if target_message else [],
            personality_traits=agent.personality
        )
```

---

## 3. 데이터베이스 기반 장기 운영 아키텍처

### 3.1 데이터베이스 선택

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        데이터베이스 아키텍처                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Primary: SQLite (로컬 개발/소규모)  →  PostgreSQL (프로덕션/확장)       │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   SQLite    │    │ PostgreSQL  │    │    Redis    │                 │
│  │             │    │             │    │             │                 │
│  │ • 개발/테스트│    │ • 프로덕션  │    │ • 캐시      │                 │
│  │ • 단일 서버 │    │ • 확장 가능 │    │ • 세션      │                 │
│  │ • 파일 기반 │    │ • 동시성    │    │ • 실시간    │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                                                                         │
│  ORM: SQLAlchemy (Python) / Prisma (TypeScript)                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 데이터베이스 스키마

```sql
-- 신호 (Signals)
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,          -- 'rss', 'github', 'onchain', 'social', 'news'
    category VARCHAR(50) NOT NULL,         -- 'ai', 'crypto', 'finance', etc.
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    raw_data JSONB,                        -- 원본 데이터 (JSON)
    score FLOAT DEFAULT 0.0,               -- 관련성 점수
    sentiment VARCHAR(20),                 -- 'positive', 'negative', 'neutral'
    topics TEXT[],                         -- 관련 토픽 배열
    entities TEXT[],                       -- 추출된 엔티티
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 인덱스
    INDEX idx_signals_source (source),
    INDEX idx_signals_category (category),
    INDEX idx_signals_collected_at (collected_at),
    INDEX idx_signals_score (score DESC)
);

-- 트렌드 (Trends)
CREATE TABLE trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period VARCHAR(20) NOT NULL,           -- '24h', '7d', '30d'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    score FLOAT NOT NULL,
    signal_count INT DEFAULT 0,
    category VARCHAR(50),
    keywords TEXT[],
    related_signals UUID[],                -- signal IDs
    analysis_data JSONB,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_trends_period (period),
    INDEX idx_trends_analyzed_at (analyzed_at),
    INDEX idx_trends_score (score DESC)
);

-- 아이디어 (Ideas)
CREATE TABLE ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    description TEXT,
    source_type VARCHAR(20) NOT NULL,      -- 'traditional', 'trend_based'
    source_trend_id UUID REFERENCES trends(id),
    source_signals UUID[],
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'in_debate', 'selected', 'rejected', 'planned'
    github_issue_id INT,
    github_issue_url TEXT,
    score FLOAT DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_ideas_status (status),
    INDEX idx_ideas_created_at (created_at)
);

-- 토론 세션 (Debate Sessions)
CREATE TABLE debate_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    phase VARCHAR(20) NOT NULL,            -- 'divergence', 'convergence', 'planning'
    round_number INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active',   -- 'active', 'completed', 'cancelled'
    participants TEXT[],                   -- agent IDs
    summary TEXT,
    outcome VARCHAR(20),                   -- 'selected', 'rejected', 'needs_refinement'
    metadata JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_debates_idea (idea_id),
    INDEX idx_debates_status (status),
    INDEX idx_debates_phase (phase)
);

-- 토론 메시지 (Debate Messages)
CREATE TABLE debate_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES debate_sessions(id) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    message_type VARCHAR(20) NOT NULL,     -- 'propose', 'support', 'challenge', 'refine', 'merge'
    content TEXT NOT NULL,
    references UUID[],                     -- 참조하는 이전 메시지 IDs
    personality_traits JSONB,
    token_count INT,
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_messages_session (session_id),
    INDEX idx_messages_agent (agent_id),
    INDEX idx_messages_created_at (created_at)
);

-- 계획서 (Plans)
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    debate_session_id UUID REFERENCES debate_sessions(id),
    title VARCHAR(500) NOT NULL,
    version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',    -- 'draft', 'review', 'approved', 'rejected'
    prd_content TEXT,
    architecture_content TEXT,
    user_research_content TEXT,
    business_model_content TEXT,
    project_plan_content TEXT,
    final_plan TEXT,
    github_issue_id INT,
    github_issue_url TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_plans_idea (idea_id),
    INDEX idx_plans_status (status)
);

-- API 사용량 (API Usage)
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    provider VARCHAR(50) NOT NULL,         -- 'claude', 'openai', 'gemini'
    model VARCHAR(100) NOT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10, 4) DEFAULT 0,
    request_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(date, provider, model),
    INDEX idx_usage_date (date),
    INDEX idx_usage_provider (provider)
);

-- 시스템 로그 (System Logs)
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,            -- 'debug', 'info', 'warn', 'error'
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    trace TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_logs_level (level),
    INDEX idx_logs_source (source),
    INDEX idx_logs_created_at (created_at)
);

-- 에이전트 상태 (Agent States)
CREATE TABLE agent_states (
    id VARCHAR(100) PRIMARY KEY,           -- agent ID
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'idle',     -- 'idle', 'active', 'error'
    current_task TEXT,
    last_active_at TIMESTAMPTZ,
    total_messages INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 SQLAlchemy 모델

```python
# src/agentic_orchestrator/db/models.py

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class Signal(Base):
    __tablename__ = 'signals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(Text)
    raw_data = Column(JSONB)
    score = Column(Float, default=0.0, index=True)
    sentiment = Column(String(20))
    topics = Column(ARRAY(Text))
    entities = Column(ARRAY(Text))
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Trend(Base):
    __tablename__ = 'trends'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    score = Column(Float, nullable=False, index=True)
    signal_count = Column(Integer, default=0)
    category = Column(String(50))
    keywords = Column(ARRAY(Text))
    related_signals = Column(ARRAY(UUID(as_uuid=True)))
    analysis_data = Column(JSONB)
    analyzed_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ideas = relationship("Idea", back_populates="source_trend")


class Idea(Base):
    __tablename__ = 'ideas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    description = Column(Text)
    source_type = Column(String(20), nullable=False)
    source_trend_id = Column(UUID(as_uuid=True), ForeignKey('trends.id'))
    source_signals = Column(ARRAY(UUID(as_uuid=True)))
    status = Column(String(20), default='pending', index=True)
    github_issue_id = Column(Integer)
    github_issue_url = Column(Text)
    score = Column(Float, default=0.0)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_trend = relationship("Trend", back_populates="ideas")
    debate_sessions = relationship("DebateSession", back_populates="idea")
    plans = relationship("Plan", back_populates="idea")


class DebateSession(Base):
    __tablename__ = 'debate_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey('ideas.id'), nullable=False, index=True)
    phase = Column(String(20), nullable=False, index=True)
    round_number = Column(Integer, default=1)
    status = Column(String(20), default='active', index=True)
    participants = Column(ARRAY(Text))
    summary = Column(Text)
    outcome = Column(String(20))
    metadata = Column(JSONB)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    idea = relationship("Idea", back_populates="debate_sessions")
    messages = relationship("DebateMessage", back_populates="session")


class DebateMessage(Base):
    __tablename__ = 'debate_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('debate_sessions.id'), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    message_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    references = Column(ARRAY(UUID(as_uuid=True)))
    personality_traits = Column(JSONB)
    token_count = Column(Integer)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("DebateSession", back_populates="messages")


class Plan(Base):
    __tablename__ = 'plans'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey('ideas.id'), nullable=False, index=True)
    debate_session_id = Column(UUID(as_uuid=True), ForeignKey('debate_sessions.id'))
    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(20), default='draft', index=True)
    prd_content = Column(Text)
    architecture_content = Column(Text)
    user_research_content = Column(Text)
    business_model_content = Column(Text)
    project_plan_content = Column(Text)
    final_plan = Column(Text)
    github_issue_id = Column(Integer)
    github_issue_url = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    idea = relationship("Idea", back_populates="plans")


class APIUsage(Base):
    __tablename__ = 'api_usage'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    request_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_usage_date_provider_model', 'date', 'provider', 'model', unique=True),
    )


class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSONB)
    trace = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
```

### 3.4 데이터베이스 연결 및 세션 관리

```python
# src/agentic_orchestrator/db/connection.py

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os

from .models import Base


class Database:
    """데이터베이스 연결 관리"""

    def __init__(self, url: str = None):
        self.url = url or os.getenv(
            "DATABASE_URL",
            "sqlite:///data/orchestrator.db"  # 기본값: SQLite
        )

        # PostgreSQL인 경우 커넥션 풀 설정
        if self.url.startswith("postgresql"):
            self.engine = create_engine(
                self.url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
        else:
            # SQLite
            self.engine = create_engine(
                self.url,
                connect_args={"check_same_thread": False}
            )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """테이블 생성"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """세션 반환 (수동 관리용)"""
        return self.SessionLocal()


# 글로벌 인스턴스
db = Database()
```

### 3.5 리포지토리 패턴

```python
# src/agentic_orchestrator/db/repositories.py

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import uuid

from .models import Signal, Trend, Idea, DebateSession, DebateMessage, Plan, APIUsage


class SignalRepository:
    """신호 데이터 접근"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, signal_data: dict) -> Signal:
        signal = Signal(**signal_data)
        self.session.add(signal)
        self.session.flush()
        return signal

    def create_many(self, signals_data: List[dict]) -> List[Signal]:
        signals = [Signal(**data) for data in signals_data]
        self.session.add_all(signals)
        self.session.flush()
        return signals

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[Signal]:
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.session.query(Signal)
            .filter(Signal.collected_at >= since)
            .order_by(desc(Signal.score))
            .limit(limit)
            .all()
        )

    def get_by_source(self, source: str, limit: int = 50) -> List[Signal]:
        return (
            self.session.query(Signal)
            .filter(Signal.source == source)
            .order_by(desc(Signal.collected_at))
            .limit(limit)
            .all()
        )

    def get_by_category(self, category: str, limit: int = 50) -> List[Signal]:
        return (
            self.session.query(Signal)
            .filter(Signal.category == category)
            .order_by(desc(Signal.collected_at))
            .limit(limit)
            .all()
        )

    def count_by_source(self) -> dict:
        results = (
            self.session.query(Signal.source, func.count(Signal.id))
            .group_by(Signal.source)
            .all()
        )
        return {source: count for source, count in results}


class IdeaRepository:
    """아이디어 데이터 접근"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, idea_data: dict) -> Idea:
        idea = Idea(**idea_data)
        self.session.add(idea)
        self.session.flush()
        return idea

    def get_by_id(self, idea_id: uuid.UUID) -> Optional[Idea]:
        return self.session.query(Idea).filter(Idea.id == idea_id).first()

    def get_by_status(self, status: str) -> List[Idea]:
        return (
            self.session.query(Idea)
            .filter(Idea.status == status)
            .order_by(desc(Idea.created_at))
            .all()
        )

    def get_pending(self) -> List[Idea]:
        return self.get_by_status('pending')

    def get_in_debate(self) -> List[Idea]:
        return self.get_by_status('in_debate')

    def update_status(self, idea_id: uuid.UUID, status: str) -> Optional[Idea]:
        idea = self.get_by_id(idea_id)
        if idea:
            idea.status = status
            idea.updated_at = datetime.utcnow()
            self.session.flush()
        return idea

    def count_by_status(self) -> dict:
        results = (
            self.session.query(Idea.status, func.count(Idea.id))
            .group_by(Idea.status)
            .all()
        )
        return {status: count for status, count in results}


class DebateRepository:
    """토론 데이터 접근"""

    def __init__(self, session: Session):
        self.session = session

    def create_session(self, session_data: dict) -> DebateSession:
        debate = DebateSession(**session_data)
        self.session.add(debate)
        self.session.flush()
        return debate

    def add_message(self, message_data: dict) -> DebateMessage:
        message = DebateMessage(**message_data)
        self.session.add(message)
        self.session.flush()
        return message

    def get_session_by_id(self, session_id: uuid.UUID) -> Optional[DebateSession]:
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.id == session_id)
            .first()
        )

    def get_session_messages(self, session_id: uuid.UUID) -> List[DebateMessage]:
        return (
            self.session.query(DebateMessage)
            .filter(DebateMessage.session_id == session_id)
            .order_by(DebateMessage.created_at)
            .all()
        )

    def get_active_sessions(self) -> List[DebateSession]:
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.status == 'active')
            .all()
        )


class APIUsageRepository:
    """API 사용량 데이터 접근"""

    def __init__(self, session: Session):
        self.session = session

    def record(self, provider: str, model: str, input_tokens: int, output_tokens: int, cost: float):
        today = datetime.utcnow().date()

        usage = (
            self.session.query(APIUsage)
            .filter(
                APIUsage.date == today,
                APIUsage.provider == provider,
                APIUsage.model == model
            )
            .first()
        )

        if usage:
            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.cost_usd += cost
            usage.request_count += 1
            usage.updated_at = datetime.utcnow()
        else:
            usage = APIUsage(
                date=today,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                request_count=1
            )
            self.session.add(usage)

        self.session.flush()
        return usage

    def get_today_total(self) -> dict:
        today = datetime.utcnow().date()
        results = (
            self.session.query(
                func.sum(APIUsage.cost_usd).label('total_cost'),
                func.sum(APIUsage.input_tokens).label('total_input'),
                func.sum(APIUsage.output_tokens).label('total_output'),
                func.sum(APIUsage.request_count).label('total_requests')
            )
            .filter(APIUsage.date == today)
            .first()
        )
        return {
            'total_cost': float(results.total_cost or 0),
            'total_input_tokens': int(results.total_input or 0),
            'total_output_tokens': int(results.total_output or 0),
            'total_requests': int(results.total_requests or 0)
        }

    def get_month_total(self) -> float:
        first_of_month = datetime.utcnow().replace(day=1).date()
        result = (
            self.session.query(func.sum(APIUsage.cost_usd))
            .filter(APIUsage.date >= first_of_month)
            .scalar()
        )
        return float(result or 0)
```

### 3.6 마이그레이션 설정 (Alembic)

```python
# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentic_orchestrator.db.models import Base

config = context.config

# .env에서 DATABASE_URL 가져오기
database_url = os.getenv("DATABASE_URL", "sqlite:///data/orchestrator.db")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 마이그레이션"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 마이그레이션"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3.7 Redis 캐시 레이어

```python
# src/agentic_orchestrator/cache/redis_cache.py

import redis
import json
from typing import Optional, Any
from datetime import timedelta
import os


class RedisCache:
    """Redis 기반 캐시"""

    def __init__(self, url: str = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_url(self.url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """캐시 저장 (기본 5분)"""
        return self.client.setex(
            key,
            timedelta(seconds=ttl),
            json.dumps(value, default=str)
        )

    def delete(self, key: str) -> bool:
        """캐시 삭제"""
        return bool(self.client.delete(key))

    def exists(self, key: str) -> bool:
        """캐시 존재 여부"""
        return bool(self.client.exists(key))

    # 실시간 데이터용 메서드

    def publish(self, channel: str, message: Any):
        """Pub/Sub 메시지 발행"""
        self.client.publish(channel, json.dumps(message, default=str))

    def subscribe(self, channel: str):
        """Pub/Sub 구독"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    # 카운터

    def incr(self, key: str, amount: int = 1) -> int:
        """카운터 증가"""
        return self.client.incrby(key, amount)

    def get_counter(self, key: str) -> int:
        """카운터 조회"""
        value = self.client.get(key)
        return int(value) if value else 0


# 캐시 키 패턴
class CacheKeys:
    SIGNALS_RECENT = "signals:recent:{hours}"
    TRENDS_LATEST = "trends:latest:{period}"
    IDEAS_BY_STATUS = "ideas:status:{status}"
    DEBATE_SESSION = "debate:session:{session_id}"
    BUDGET_TODAY = "budget:today"
    BUDGET_MONTH = "budget:month"
    AGENT_STATE = "agent:state:{agent_id}"
```

### 3.8 데이터 보관 및 정리 정책

```python
# src/agentic_orchestrator/db/retention.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import delete, and_

from .models import Signal, SystemLog, DebateMessage


class DataRetentionManager:
    """
    데이터 보관 정책 관리

    보관 기간:
    - 신호: 90일
    - 시스템 로그: 30일
    - 토론 메시지: 영구 (요약 후 상세 내용은 180일)
    - 아이디어/계획: 영구
    - API 사용량: 365일
    """

    RETENTION_DAYS = {
        'signals': 90,
        'system_logs': 30,
        'debate_messages_detail': 180,
        'api_usage': 365
    }

    def __init__(self, session: Session):
        self.session = session

    def cleanup_old_signals(self) -> int:
        """오래된 신호 삭제"""
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['signals'])

        result = self.session.execute(
            delete(Signal).where(Signal.collected_at < cutoff)
        )
        self.session.commit()

        return result.rowcount

    def cleanup_old_logs(self) -> int:
        """오래된 로그 삭제"""
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['system_logs'])

        result = self.session.execute(
            delete(SystemLog).where(SystemLog.created_at < cutoff)
        )
        self.session.commit()

        return result.rowcount

    def archive_old_debate_messages(self) -> int:
        """오래된 토론 메시지 압축 (상세 내용 제거, 요약만 유지)"""
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['debate_messages_detail'])

        # 상세 내용을 요약으로 대체
        messages = (
            self.session.query(DebateMessage)
            .filter(
                DebateMessage.created_at < cutoff,
                DebateMessage.content.isnot(None)
            )
            .all()
        )

        count = 0
        for msg in messages:
            if len(msg.content) > 500:
                # 긴 메시지는 처음 500자만 유지
                msg.content = msg.content[:500] + "... [archived]"
                count += 1

        self.session.commit()
        return count

    def run_all_cleanup(self) -> dict:
        """모든 정리 작업 실행"""
        return {
            'signals_deleted': self.cleanup_old_signals(),
            'logs_deleted': self.cleanup_old_logs(),
            'messages_archived': self.archive_old_debate_messages()
        }
```

### 3.9 파일 구조

```
src/agentic_orchestrator/
├── db/
│   ├── __init__.py
│   ├── connection.py          # 데이터베이스 연결
│   ├── models.py              # SQLAlchemy 모델
│   ├── repositories.py        # 리포지토리 패턴
│   ├── retention.py           # 데이터 보관 정책
│   └── migrations/            # Alembic 마이그레이션
│       ├── versions/
│       └── env.py
├── cache/
│   ├── __init__.py
│   └── redis_cache.py         # Redis 캐시
```

---

## 부록: 환경 설정 업데이트

```bash
# .env.example (추가 항목)

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/orchestrator
# 또는 SQLite: sqlite:///data/orchestrator.db

# Redis
REDIS_URL=redis://localhost:6379/0

# 데이터 보관
RETENTION_SIGNALS_DAYS=90
RETENTION_LOGS_DAYS=30
RETENTION_MESSAGES_DAYS=180
```

```toml
# pyproject.toml (추가 의존성)

[project.dependencies]
# 데이터베이스
sqlalchemy = ">=2.0.0"
alembic = ">=1.12.0"
psycopg2-binary = ">=2.9.0"  # PostgreSQL
asyncpg = ">=0.28.0"          # PostgreSQL async

# 캐시
redis = ">=5.0.0"

# 검증
pydantic = ">=2.0.0"
```

---

*이 문서는 UPGRADE_PLAN.md의 보완 문서입니다.*
