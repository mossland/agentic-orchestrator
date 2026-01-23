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
          ├─ Divergence (16 에이전트): 다양한 아이디어 생성
          ├─ Convergence (8 에이전트): 평가/병합/필터링
          └─ Planning (10 에이전트): 실행 계획 작성
```

- **스케줄**: PM2 6시간마다
- **LLM**: Ollama (로컬) + Claude (API)
- **출력**: `Idea` 객체 리스트
- **특징**: 34명의 다양한 페르소나가 토론

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

| 작업 | 주기 | Cron | 설명 |
|------|------|------|------|
| Signal Collection | 30분마다 | `*/30 * * * *` | RSS/API에서 신호 수집 |
| Trend Analysis | 2시간마다 | `0 */2 * * *` | 신호 분석 → 트렌드 생성 |
| Debate | 6시간마다 | `0 */6 * * *` | 트렌드 기반 토론 → 아이디어 생성 |
| Backlog | 4시간마다 | `0 */4 * * *` | 상태 집계/리포트 |
| Health Check | 5분마다 | `*/5 * * * *` | 시스템 상태 확인 |

## GitHub 연동

모든 아이디어와 플랜은 GitHub Issues로 생성됩니다.

### 라벨 체계

| 라벨 | 용도 |
|------|------|
| `type:idea` | 아이디어 이슈 |
| `type:plan` | 플랜 이슈 |
| `status:backlog` | 백로그 대기 |
| `promote:to-plan` | 플랜 생성 대상 |
| `generated:by-orchestrator` | 오케스트레이터가 자동 생성 |
| `source:trend` | 트렌드 분석에서 생성 |

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
