# MOSS.AO 아이디어 생성 파이프라인

이 문서는 MOSS.AO의 아이디어 생성 파이프라인을 설명합니다.

## 파이프라인 개요

```
┌──────────────────────────────────────────────────────────────────┐
│                        입력 소스                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   RSS Feeds ──┐                                                  │
│               │    ┌─────────────────┐                           │
│   GitHub    ──┼───▶│ Signal Collector│──▶ signals DB             │
│               │    └─────────────────┘         │                 │
│   OnChain   ──┘                                │                 │
│                                                ▼                 │
│                                    ┌───────────────────┐         │
│                                    │  Trend Analyzer   │         │
│                                    │    (Ollama)       │         │
│                                    └─────────┬─────────┘         │
│                                              │                   │
│                                              ▼                   │
│   ┌───────────────┐              ┌───────────────────┐           │
│   │ IdeaGenerator │              │ TrendBased Ideas  │           │
│   │   (Claude)    │              │    (Claude)       │           │
│   └───────┬───────┘              └─────────┬─────────┘           │
│           │                                │                     │
│           │    ┌───────────────────────────┘                     │
│           │    │                                                 │
│           ▼    ▼                                                 │
│   ┌─────────────────────────────────────────────────────┐        │
│   │               Multi-Stage Debate                     │        │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │        │
│   │  │Divergence│─▶│Convergence│─▶│ Planning │           │        │
│   │  │16 agents │  │ 8 agents │  │10 agents │           │        │
│   │  └──────────┘  └──────────┘  └──────────┘           │        │
│   └─────────────────────────┬───────────────────────────┘        │
│                             │                                    │
│                             ▼                                    │
│                  ┌───────────────────┐                           │
│                  │   Auto-Scorer     │                           │
│                  │    (Ollama)       │                           │
│                  └─────────┬─────────┘                           │
│                            │                                     │
│           ┌────────────────┼────────────────┐                    │
│           ▼                ▼                ▼                    │
│     ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│     │ promoted │    │  scored  │    │ archived │                 │
│     │ (≥7.0)   │    │ (4-7)    │    │ (<4.0)   │                 │
│     └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│          │               │               │                       │
│          ▼               ▼               ▼                       │
│   ┌────────────────────────────────────────────────┐             │
│   │                  SQLite DB                      │             │
│   │              ideas table                        │             │
│   └─────────────────────┬──────────────────────────┘             │
│                         │                                        │
│                         ▼                                        │
│   ┌────────────────────────────────────────────────┐             │
│   │              GitHub Issues                      │             │
│   │    type:idea + status:backlog/promoted          │             │
│   └────────────────────────────────────────────────┘             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 아이디어 생성 방법

### 1. IdeaGenerator (수동 생성)

**파일**: `src/agentic_orchestrator/backlog.py:36-200`

```
CLI 명령 → ClaudeProvider → GitHub Issue 생성
```

- **CLI**: `agentic-orchestrator backlog generate --count 3`
- **LLM**: Claude API 사용
- **출력**: GitHub Issue (`type:idea`, `status:backlog`)
- **특징**: Mossland 생태계 맞춤 프롬프트, 1-2주 MVP 가능한 아이디어

### 2. TrendBasedIdeaGenerator (트렌드 기반)

**파일**: `src/agentic_orchestrator/backlog.py:419-530`

```
RSS 피드 → 트렌드 분석 → Claude로 아이디어 생성 → GitHub Issue
```

- **CLI**: `agentic-orchestrator backlog run-cycle`
- **LLM**: Claude API
- **출력**: GitHub Issue + `source:trend` 라벨
- **특징**: 최신 트렌드에서 영감을 얻은 아이디어

### 3. Multi-Stage Debate (에이전트 토론)

**파일**: `src/agentic_orchestrator/debate/multi_stage.py`

```
토픽 입력 → 3단계 토론 → 아이디어 리스트 생성
          │
          ├─ Divergence: 다양한 아이디어 생성
          ├─ Convergence: 평가/병합/필터링
          └─ Planning: 실행 계획 작성
```

- **스케줄**: PM2 (TEST: 1시간마다, PROD: 6시간마다)
- **LLM**: Ollama (로컬) - qwen2.5:14b, llama3.2:3b
- **출력**: `Idea` 객체 리스트
- **특징**: 다양한 페르소나가 토론

#### TEST 모드 vs PRODUCTION 모드

| 설정 | TEST 모드 | PRODUCTION 모드 |
|------|-----------|-----------------|
| Divergence 에이전트/라운드 | 2 | 8 |
| Divergence 라운드 | 2 | 3 |
| Convergence 에이전트/라운드 | 2 | 4 |
| Convergence 라운드 | 1 | 2 |
| Planning 에이전트/라운드 | 2 | 5 |
| Planning 라운드 | 1 | 2 |
| **예상 시간** | ~7분 | ~30분+ |

`config.yaml`의 `debate.test_mode`로 전환 (현재: `false` - 프로덕션 모드)

### 4. Auto-Scoring System (자동 점수화)

**파일**: `src/agentic_orchestrator/scheduler/tasks.py:207-426`

```
토론 결과 → 자동 점수화 → DB 저장 + GitHub Issue 생성
                │
                ├─ score >= 7.0 → promoted (플랜 자동 생성)
                ├─ score < 4.0  → archived
                └─ 중간 점수    → scored (백로그)
```

- **트리거**: 토론 완료 후 자동 실행
- **LLM**: Ollama (로컬)
- **출력**: DB 저장 + GitHub Issue
- **특징**: 점수 기반 자동 승격/아카이브

### 5. IdeationStage (레거시)

**파일**: `src/agentic_orchestrator/stages/ideation.py`

```
스테이트 시작 → Claude로 3개 아이디어 생성 → 최적 선택 → 문서 저장
```

- **CLI**: `agentic-orchestrator run --stage ideation`
- **LLM**: Claude API
- **출력**: Markdown 문서 (`ideas.md`, `selected_idea.md`)
- **특징**: 단일 프로젝트 워크플로우용 (구버전)

## 콘텐츠 품질 요구사항

### 제목 규칙

모든 트렌드, 아이디어, 플랜 제목은 다음 요구사항을 충족해야 합니다:

| 항목 | 요구사항 |
|------|----------|
| 최소 길이 | **30자 이상** |
| 내용 | 구체적인 기술명, 프로젝트명, 수치 포함 |
| 형식 | 실행 가능한 액션 또는 명확한 가치 제안 |

**예시:**
- ❌ 나쁜 예: "AI 트렌드", "DeFi 도구", "NFT 서비스"
- ✅ 좋은 예: "OpenAI GPT-5 에이전트 SDK 출시로 자율 AI 워크플로우 자동화 시대 개막"
- ✅ 좋은 예: "Mossland NFT 홀더를 위한 실시간 메타버스 자산 가치 트래커 개발"

### 아이디어 필수 섹션

토론 발산 단계에서 생성되는 아이디어는 다음 형식을 따릅니다:

```markdown
## 아이디어: [구체적인 제목 30자 이상]

### 1. 핵심 분석 (100자 이상)
- 현재 시장/기술 상황 분석
- 왜 지금 이 아이디어가 필요한지 구체적 근거

### 2. 기회 또는 리스크 (150자 이상)
- 정량적 데이터나 구체적 사례 포함
- 경쟁 서비스와의 차별점

### 3. 구체적 제안 (200자 이상)
- 핵심 기능 3-5개 나열
- 기술 스택 제안 (예: Next.js, Solidity, Python)
- MVP 범위 정의

### 4. 실행 로드맵 (100자 이상)
- 1주차, 2주차 등 구체적 일정
- 필요 리소스 (개발자 수, 예상 비용 등)

### 5. 성공 지표
- 측정 가능한 KPI 2-3개
- 목표 수치 포함 (예: "출시 1개월 내 DAU 500명")
```

### 기획안 필수 섹션

Planning 단계에서 생성되는 기획안은 다음 구조를 따릅니다:

```markdown
## 1. 프로젝트 개요
- 프로젝트 명: [구체적이고 설명적인 이름]
- 한 줄 설명: [50자 이내]
- 목표: [3개 이상]
- 대상 사용자: [예상 사용자 수 포함]
- 예상 기간: [MVP vs 풀버전]
- 예상 비용: [인건비, 인프라 비용]

## 2. 기술 아키텍처
- 프론트엔드: [기술 + 선택 이유]
- 백엔드: [기술 + 선택 이유]
- 데이터베이스: [기술 + 선택 이유]
- 블록체인 연동: [체인, 프로토콜]
- 외부 API: [사용할 서비스]

## 3. 상세 실행 계획
### Week 1: [테마]
- [ ] Task 1: [구체적 작업]
- [ ] Task 2: [구체적 작업]
- **마일스톤**: [완료 조건]

## 4. 리스크 관리
| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|

## 5. 성과 지표 (KPI)
| 지표 | 목표 | 측정 방법 | 측정 주기 |
|------|------|----------|----------|

## 6. 향후 확장 계획
- Phase 2 기능: [...]
- 장기 비전: [...]
```

### 평가 상세 기준

Convergence 단계에서 각 아이디어는 5가지 차원으로 평가됩니다:

| 차원 | 평가 기준 |
|------|----------|
| 실현 가능성 | MVP 구현 가능성, 기술 스택 성숙도, 팀 역량 대비 복잡도 |
| 영향력 | 생태계 시너지, 신규 사용자 유입 잠재력, 수익 모델 |
| 혁신성 | 시장 솔루션 대비 차별점, 기술적 새로움, 비즈니스 모델 혁신 |
| 리스크 | 기술적/시장적/규제적 리스크 |
| 시급성 | 시장 타이밍, 경쟁사 동향, 로드맵 적합성 |

각 평가 항목에 대해 **50자 이상의 구체적 근거**를 작성해야 합니다.

---

## 점수화 기준

Auto-Scorer는 4가지 차원으로 아이디어를 평가합니다:

| 차원 | 설명 | 가중치 |
|------|------|--------|
| **Feasibility** | 1-2주 내 MVP로 구현 가능한가? | 25% |
| **Relevance** | Mossland/Web3 생태계와 관련이 있는가? | 25% |
| **Novelty** | 기존 솔루션과 차별화되는가? | 25% |
| **Impact** | 사용자 가치가 있는가? | 25% |

**총점 = (Feasibility + Relevance + Novelty + Impact) / 4**

### 점수에 따른 상태 결정

| 총점 범위 | 상태 | 액션 |
|----------|------|------|
| 7.0 이상 | `promoted` | 플랜 자동 생성, GitHub Issue에 `promote:to-plan` 라벨 |
| 4.0 - 7.0 | `scored` | 백로그 대기, `status:backlog` 라벨 |
| 4.0 미만 | `archived` | 아카이브, `archived` 라벨 |

## 스케줄링

`ecosystem.config.js`의 `TEST_MODE`로 TEST/PRODUCTION 스케줄 전환 (현재: **PRODUCTION 모드**)

### 현재 적용 중: PRODUCTION 모드

| 작업 | 주기 | Cron | 설명 |
|------|------|------|------|
| Signal Collection | 30분마다 | `*/30 * * * *` | RSS/API에서 신호 수집 |
| Trend Analysis | 2시간마다 | `0 */2 * * *` | 신호 분석 → 트렌드 생성 |
| **Debate** | **6시간마다** | `0 */6 * * *` | 트렌드 기반 토론 → 아이디어 생성 |
| Backlog | 4시간마다 | `0 */4 * * *` | 상태 집계/리포트 |
| Health Check | 5분마다 | `*/5 * * * *` | 시스템 상태 확인 |

### TEST 모드 (빠른 테스트용)

`ecosystem.config.js`에서 `TEST_MODE = true`로 설정 시:

| 작업 | 주기 | Cron | 설명 |
|------|------|------|------|
| Signal Collection | 10분마다 | `*/10 * * * *` | RSS/API에서 신호 수집 |
| Trend Analysis | 30분마다 | `*/30 * * * *` | 신호 분석 → 트렌드 생성 |
| Debate | 1시간마다 | `0 * * * *` | 트렌드 기반 토론 → 아이디어 생성 |
| Backlog | 30분마다 | `*/30 * * * *` | 상태 집계/리포트 |
| Health Check | 5분마다 | `*/5 * * * *` | 시스템 상태 확인 |

## GitHub 연동

> **참고**: 현재 시스템은 **DB 중심**입니다. GitHub Issues는 가시성을 위해 선택적으로 생성되며, 기본 데이터 저장소는 SQLite입니다.

아이디어와 플랜은 DB에 저장되고, 선택적으로 GitHub Issues로 생성됩니다.

### 라벨 체계

| 라벨 | 용도 | 상태 |
|------|------|------|
| `type:idea` | 아이디어 이슈 | 활성 |
| `type:plan` | 플랜 이슈 | 활성 |
| `status:backlog` | 백로그 대기 | 활성 |
| `status:promoted` | 고점수 아이디어 | 활성 |
| `generated:by-orchestrator` | 오케스트레이터가 자동 생성 | 활성 |
| `source:debate` | 토론에서 생성 | 활성 |
| `promote:to-plan` | 플랜 생성 대상 | *향후 구현* |
| `promote:to-dev` | 개발 시작 대상 | *향후 구현* |

자세한 내용은 [labels.md](labels.md) 참조.

### Issue 본문 예시

```markdown
## Idea Summary
[아이디어 요약]

## Auto-Score Results
- **Total Score**: 7.5/10
- **Feasibility**: 8.0/10
- **Relevance**: 7.0/10
- **Novelty**: 7.5/10
- **Impact**: 7.5/10

## Decision: PROMOTE

## Context
**Debate Topic**: [토론 주제]
**Debate Session**: [세션 ID]

---
*Auto-generated by MOSS.AO Orchestrator*
```

## CLI 명령어

```bash
# 수동 아이디어 생성
agentic-orchestrator backlog generate --count 3

# 트렌드 분석 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler analyze-trends

# 토론 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate

# 특정 토픽으로 토론
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate --topic "AI Agent Marketplace"

# 백로그 처리
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler process-backlog
```

## 디버깅

### DB에서 아이디어 소스별 확인

```sql
SELECT source_type, COUNT(*) as count
FROM ideas
GROUP BY source_type
ORDER BY count DESC;
```

### GitHub Issue 동기화 확인

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN github_issue_url IS NOT NULL THEN 1 ELSE 0 END) as with_github
FROM ideas;
```

### 토론 결과 확인

```sql
SELECT id, topic, status,
       json_array_length(ideas_generated) as idea_count
FROM debate_sessions
ORDER BY started_at DESC
LIMIT 5;
```

---

## 프로젝트 생성 (향후 기능)

> **상태**: 구현 예정. 현재 `projects/` 폴더는 비어 있습니다.

Plan이 승인되면 `projects/` 폴더에 프로젝트 스캐폴드가 자동 생성될 예정입니다.

### 계획된 워크플로우

```
Plan (DB)
    ↓
프로젝트 이름 생성 (kebab-case)
    ↓
projects/{project-name}/
    ├── README.md          # 프로젝트 소개 + 배경
    ├── PLAN.md            # 원본 Plan 문서
    ├── src/               # 생성된 소스 코드
    └── docs/              # 추가 문서
```

자세한 내용은 [projects.md](projects.md) 참조.
