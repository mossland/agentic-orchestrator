# Mossland Agentic Orchestrator - 개발 진행 상황

## 프로젝트 개요

모스랜드 생태계를 위한 마이크로 Web3 서비스를 자율적으로 발굴, 기획, 구현하는 오케스트레이션 시스템.

- **공개 URL**: https://ao.moss.land
- **현재 버전**: v0.5.1 "Bilingual"
- **마지막 업데이트**: 2026-01-24

---

## 완료된 Phase 요약

| Phase | 버전 | 설명 | 상태 |
|-------|------|------|------|
| Phase 1 | v0.1.0 | 초기 구현 (상태 머신, LLM 프로바이더) | ✅ 완료 |
| Phase 2 | v0.2.0 | 백로그 워크플로우 (GitHub Issues) | ✅ 완료 |
| Phase 3 | - | 문서화 | ✅ 완료 |
| Phase 4 | v0.2.1 | 안정성 (멱등성, Lock, 롤백) | ✅ 완료 |
| Phase 5 | v0.3.0 | 트렌드 기반 아이디어 생성 | ✅ 완료 |
| Phase 6 | v0.4.0 | 멀티에이전트 토론 시스템 | ✅ 완료 |
| Phase 7 | v0.5.0 | 대시보드 웹사이트 | ✅ 완료 |
| Phase 8 | v0.4.0+ | Signal Storm (10개 어댑터, 34 에이전트) | ✅ 완료 |
| Phase 9 | v0.5.1 | 양방향 번역 (EN/KO) | ✅ 완료 |

---

## 현재 시스템 아키텍처

### 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                     시그널 수집 (30분마다)                        │
│  RSS, GitHub, OnChain, Social, News, Twitter, Discord,          │
│  Lens, Farcaster, Coingecko (10개 어댑터)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    트렌드 분석 (2시간마다)                        │
│  Ollama (llama3.3:70b) → 트렌드 추출 및 점수화                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               멀티스테이지 토론 (6시간마다)                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Divergence │→ │ Convergence │→ │  Planning   │             │
│  │  12 에이전트 │  │  12 에이전트 │  │  10 에이전트 │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     자동 점수화 (Ollama)                         │
│                                                                 │
│        ┌──────────────┬──────────────┬──────────────┐          │
│        │   promoted   │    scored    │   archived   │          │
│        │   (≥7.0)     │   (4.0-7.0)  │    (<4.0)    │          │
│        └──────────────┴──────────────┴──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SQLite DB (Primary)                        │
│        signals, trends, ideas, plans, debate_sessions           │
│                              +                                  │
│                 GitHub Issues (For Visibility)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| 백엔드 | Python 3.12, FastAPI, SQLAlchemy |
| 프론트엔드 | Next.js 14, TypeScript, Tailwind CSS |
| LLM (로컬) | Ollama (llama3.3:70b, qwen2.5:32b, phi4:14b) |
| LLM (클라우드) | Claude, OpenAI, Gemini (폴백) |
| 데이터베이스 | SQLite |
| 프로세스 관리 | PM2 |
| 프록시 | Nginx (Lightsail) |

---

## 프로젝트 구조 (현재)

```
agentic-orchestrator/
├── src/agentic_orchestrator/    # Python 백엔드
│   ├── api/                     # FastAPI 서버 (포트 3001)
│   ├── db/                      # SQLAlchemy 모델 & 리포지토리
│   ├── debate/                  # 멀티스테이지 토론 시스템
│   │   ├── multi_stage.py       # 3단계 토론 오케스트레이션
│   │   └── protocol.py          # 토론 프로토콜 (프롬프트 포함)
│   ├── llm/                     # 하이브리드 LLM 라우터
│   ├── personas/                # 34개 AI 에이전트 정의
│   ├── scheduler/               # PM2 스케줄 작업
│   ├── signals/                 # 시그널 수집기
│   │   └── adapters/            # 10개 시그널 어댑터
│   └── translation/             # 양방향 번역 모듈
├── website/                     # Next.js 프론트엔드 (포트 3000)
│   ├── src/app/                 # App Router 페이지
│   ├── src/components/          # React 컴포넌트
│   └── src/lib/                 # 유틸리티 (API, i18n)
├── data/                        # 데이터 디렉토리
│   ├── orchestrator.db          # SQLite 데이터베이스
│   └── trends/                  # 트렌드 분석 결과
├── projects/                    # 생성된 프로젝트 (향후 기능)
│   └── README.md                # 프로젝트 목록
├── docs/                        # 설계 문서
│   ├── pipeline.md              # 파이프라인 가이드
│   ├── labels.md                # GitHub 라벨 가이드
│   └── projects.md              # 프로젝트 관리 가이드
├── prompts/                     # 레거시 프롬프트 템플릿
├── ecosystem.config.js          # PM2 설정
└── config.yaml                  # 오케스트레이터 설정
```

---

## PM2 서비스 현황

| 서비스 | 스케줄 | 설명 |
|--------|--------|------|
| `moss-ao-web` | 항시 | Next.js 대시보드 (포트 3000) |
| `moss-ao-api` | 항시 | FastAPI 백엔드 (포트 3001) |
| `moss-ao-signals` | 30분 | 10개 어댑터에서 시그널 수집 |
| `moss-ao-trends` | 2시간 | 시그널 분석 → 트렌드 생성 |
| `moss-ao-debate` | 6시간 | 멀티에이전트 토론 |
| `moss-ao-backlog` | 4시간 | 상태 집계/리포트 |
| `moss-ao-health` | 5분 | 시스템 헬스체크 |

---

## 향후 구현 예정 기능

### 단기 (구현 예정)

- [ ] **Plan → Project 자동 생성**: 승인된 Plan을 `projects/` 폴더에 프로젝트로 변환
- [ ] **웹 UI "Generate Project" 버튼**: Plan에서 바로 프로젝트 생성
- [ ] **GitHub 라벨 승격 워크플로우**: `promote:to-plan`, `promote:to-dev` 자동 처리

### 중기

- [ ] PostgreSQL 마이그레이션 (확장성)
- [ ] 실시간 WebSocket 업데이트
- [ ] Slack/Discord 알림

### 장기

- [ ] 멀티 프로젝트 오케스트레이션
- [ ] 비용 추적 및 예산 제한
- [ ] 성능 모니터링 대시보드

---

## 환경 설정

### 필수 환경 변수

```bash
GITHUB_TOKEN=ghp_xxxxx        # GitHub PAT
GITHUB_OWNER=MosslandOpenDevs # 저장소 소유자
GITHUB_REPO=agentic-orchestrator
ANTHROPIC_API_KEY=sk-ant-xxx  # Claude API (폴백용)
```

### 선택 환경 변수

```bash
OPENAI_API_KEY=sk-xxxxx       # OpenAI (폴백용)
GEMINI_API_KEY=AIzaSyxxxxx    # Gemini (폴백용)
OLLAMA_HOST=http://localhost:11434  # Ollama 서버
```

---

## 실행 방법

### 빠른 시작

```bash
# 설치
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# PM2로 서비스 시작
pm2 start ecosystem.config.js
pm2 save

# 상태 확인
pm2 status
```

### 수동 실행

```bash
# 시그널 수집
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler signal-collect

# 트렌드 분석
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler analyze-trends

# 토론 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate

# 특정 토픽으로 토론
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate --topic "AI Agent Marketplace"
```

---

## 관련 문서

- [CLAUDE.md](CLAUDE.md) - Claude Code 참조 문서
- [docs/pipeline.md](docs/pipeline.md) - 아이디어 생성 파이프라인
- [docs/labels.md](docs/labels.md) - GitHub 라벨 가이드
- [docs/projects.md](docs/projects.md) - 프로젝트 관리 가이드
- [CHANGELOG.md](CHANGELOG.md) - 변경 이력

---

*마지막 업데이트: 2026-01-24 (v0.5.1 "Bilingual")*
