# Mossland Agentic Orchestrator - 개발 진행 상황

## 프로젝트 개요

모스랜드 생태계를 위한 마이크로 Web3 서비스를 자율적으로 발굴, 기획, 구현하는 오케스트레이션 시스템.

---

## Phase 1: 초기 구현 (v0.1.0) ✅

### 완료 항목

#### 코어 시스템
- [x] 상태 머신 구현 (IDEATION → PLANNING_DRAFT → PLANNING_REVIEW → DEV → QA → DONE)
- [x] YAML 기반 상태 영속화 (`.agent/state.yaml`)
- [x] 반복 추적 및 제한 설정
- [x] 품질 메트릭 추적

#### LLM 프로바이더
- [x] Claude Provider (CLI 모드 + API 모드)
- [x] OpenAI Provider (gpt-5.2-chat-latest)
- [x] Gemini Provider (gemini-3-flash-preview)
- [x] Rate limit 자동 재시도 (지수 백오프)
- [x] 폴백 모델 지원
- [x] 할당량 소진 감지

#### 스테이지 핸들러
- [x] Ideation 핸들러
- [x] Planning Draft 핸들러
- [x] Planning Review 핸들러
- [x] Development 핸들러
- [x] Quality Assurance 핸들러
- [x] Done 핸들러

#### CLI 명령어
- [x] `ao init` - 프로젝트 초기화
- [x] `ao step` - 단일 스텝 실행
- [x] `ao loop` - 연속 실행
- [x] `ao status` - 상태 확인
- [x] `ao resume` - 재개
- [x] `ao reset` - 초기화
- [x] `ao push` - 푸시

#### 인프라
- [x] 프롬프트 템플릿
- [x] GitHub Actions CI
- [x] 단위 테스트 (64개)

---

## Phase 2: 백로그 기반 워크플로우 (v0.2.0) ✅

### 완료 항목

#### GitHub 통합
- [x] GitHubClient 구현 (`src/agentic_orchestrator/github_client.py`)
  - Issues CRUD
  - Labels 관리
  - Search API
  - Rate limit 처리

#### 백로그 워크플로우
- [x] BacklogOrchestrator 구현 (`src/agentic_orchestrator/backlog.py`)
  - IdeaGenerator: 아이디어 자동 생성
  - PlanGenerator: 프로모션된 아이디어로 계획 생성
  - DevScaffolder: 프로젝트 스캐폴드 생성

#### 프로모션 시스템
- [x] `promote:to-plan` 라벨 처리
- [x] `promote:to-dev` 라벨 처리
- [x] `processed:*` 라벨로 중복 방지
- [x] 자동 라벨 업데이트

#### CLI 명령어
- [x] `ao backlog run` - 전체 사이클 실행
- [x] `ao backlog generate` - 아이디어 생성
- [x] `ao backlog process` - 프로모션 처리
- [x] `ao backlog status` - 상태 확인
- [x] `ao backlog setup` - 라벨 설정

#### GitHub 설정
- [x] 이슈 템플릿 (`idea.yml`, `plan.yml`)
- [x] 스케줄 워크플로우 (`backlog.yml`)
- [x] 라벨 문서 (`docs/labels.md`)

#### 동시성 제어
- [x] 파일 기반 잠금 (fcntl)
- [x] 중복 처리 방지

#### 테스트
- [x] 백로그 모듈 테스트 추가 (19개)
- [x] 전체 테스트 통과 (83개)

---

## Phase 3: 문서화 ✅

### 완료 항목

- [x] README.md 업데이트 (백로그 워크플로우)
- [x] CHANGELOG.md 업데이트 (v0.2.0)
- [x] README.ko.md 한국어 번역
- [x] CHANGELOG.ko.md 한국어 번역
- [x] 언어 전환 링크 추가

---

## Phase 4: 안정성 및 신뢰성 (v0.2.1) ✅

### 완료 항목

#### 멱등성 보호
- [x] PlanGenerator: 이미 처리된 아이디어 스킵
- [x] PlanGenerator: 기존 plan 검색 및 중복 방지
- [x] DevScaffolder: 이미 처리된 plan 스킵
- [x] DevScaffolder: 기존 project 검색 및 중복 방지

#### Lock 타임아웃
- [x] Lock 파일에 PID 및 타임스탬프 기록
- [x] 타임아웃(기본 300초) 초과 시 stale lock 제거
- [x] 프로세스 생존 확인 (signal 0 사용)
- [x] 잘못된 형식의 lock 파일 처리

#### 환경 변수 검증
- [x] validate_backlog_environment() 함수
- [x] EnvironmentValidationError 예외 클래스
- [x] CLI 명령 시작 시 환경 검증
- [x] 친절한 오류 메시지 제공

#### 부분 실패 롤백
- [x] Plan 생성 후 라벨 업데이트 실패 시 롤백
- [x] 생성된 Plan 이슈 자동 닫기
- [x] `rollback:failed` 라벨 추가
- [x] 오류 코멘트 추가

#### 테스트
- [x] 멱등성 테스트 6개
- [x] Lock 타임아웃 테스트 6개
- [x] 환경 검증 테스트 9개
- [x] 롤백 테스트 1개
- [x] 총 테스트 105개 통과

---

## Phase 5: 트렌드 기반 아이디어 생성 (v0.3.0) ✅

### 완료 항목

#### 트렌드 분석 모듈 (`src/agentic_orchestrator/trends/`)
- [x] `models.py` - FeedItem, Trend, TrendAnalysis, TrendIdeaLink 데이터 클래스
- [x] `feeds.py` - FeedFetcher: RSS/Atom 피드 파싱 (feedparser 사용)
- [x] `analyzer.py` - TrendAnalyzer: Claude 기반 트렌드 추출
- [x] `storage.py` - TrendStorage: Markdown 파일 저장 (YAML frontmatter)

#### 트렌드 기반 아이디어 생성
- [x] TrendBasedIdeaGenerator 클래스 (`backlog.py`)
- [x] 트렌드에서 아이디어 생성 프롬프트
- [x] 아이디어-트렌드 연결 추적
- [x] `source:trend` 라벨 자동 추가

#### RSS 피드 설정 (17개 피드)
- [x] AI 카테고리: OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News
- [x] Crypto 카테고리: CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate
- [x] Finance 카테고리: CNBC Finance
- [x] Security 카테고리: The Hacker News, Krebs on Security
- [x] Dev 카테고리: The Verge, Ars Technica, Stack Overflow Blog

#### CLI 명령어
- [x] `ao backlog run --trend-ideas N --analyze-trends` - 트렌드 포함 실행
- [x] `ao backlog analyze-trends` - 트렌드 분석만 실행
- [x] `ao backlog generate-trends` - 트렌드 기반 아이디어 생성
- [x] `ao backlog trends-status` - 트렌드 분석 이력 확인

#### GitHub Actions
- [x] 스케줄 변경: 매일 8 AM KST (23:00 UTC)
- [x] `run-with-trends` 커맨드 추가 (기본 일일 실행)
- [x] 새 커맨드 옵션: `generate-trends`, `analyze-trends`, `trends-status`

#### 저장 구조
- [x] 트렌드 분석: `data/trends/YYYY/MM/YYYY-MM-DD.md`
- [x] 아이디어 링크: `data/trends/idea_links.json`
- [x] 90일 보존 정책

---

## Phase 6: 멀티 에이전트 토론 시스템 (v0.4.0) ✅

### 완료 항목

#### 토론 시스템 아키텍처
- [x] 4개 역할 정의: Founder, VC, Accelerator, Founder Friend
- [x] 3개 AI 프로바이더 순환: Claude, ChatGPT, Gemini
- [x] 라운드별 역할 배정 매트릭스
- [x] 최대 5라운드, 조기 종료 조건

#### 토론 모듈 (`src/agentic_orchestrator/debate/`)
- [x] `__init__.py` - 모듈 exports
- [x] `roles.py` - 역할 enum + 이중 언어 프롬프트
- [x] `moderator.py` - 순환 매트릭스 + 종료 로직
- [x] `debate_session.py` - 토론 세션 관리
- [x] `discussion_record.py` - GitHub 댓글 포맷팅

#### 역할별 프롬프트
- [x] Founder: 초기 기획서 생성 + 피드백 반영
- [x] VC: 시장/투자 관점 피드백
- [x] Accelerator: 실행/검증 관점 피드백 (YC/Techstars 스타일)
- [x] Founder Friend: 동료 창업자 관점 피드백

#### Plan 거부 워크플로우
- [x] `reject:plan` 라벨 추가
- [x] `GitHubClient.reject_plan()` 메서드
- [x] `GitHubClient.find_rejected_plans()` 메서드
- [x] `GitHubClient.reset_idea_for_replanning()` 메서드
- [x] `BacklogOrchestrator._process_rejected_plan()` 메서드
- [x] `ao backlog reject <plan_number>` CLI 명령어

#### 이중 언어 지원
- [x] 영어 기본 + 한국어 번역 요청 형식
- [x] 토론 기록 "English / 한국어" 표시
- [x] `[PLAN_START]`/`[PLAN_END]` 마커로 기획서 추출

#### 버그 수정
- [x] 거부 처리가 프로모션 처리 전에 실행되도록 순서 변경
- [x] `_find_existing_plan_for_idea()`가 열린 이슈만 검색

---

## 커밋 히스토리

```
041667c [docs] Update changelog and add Korean translations
f335281 [system] Add unit tests for backlog workflow modules
7542b03 [system] Add backlog-based workflow with GitHub Issues integration
81e9340 [system] Add GitHub Actions CI and documentation
134824b [system] Add unit tests
b911992 [system] Add prompt templates for all stages
a9e75e9 [system] Add orchestrator core and CLI
0b50105 [system] Add stage handlers for orchestrator pipeline
... (이전 커밋들)
```

---

## 프로젝트 구조

```
agentic-orchestrator/
├── .agent/                     # 오케스트레이터 상태
├── .github/
│   ├── ISSUE_TEMPLATE/         # 이슈 템플릿
│   │   ├── config.yml
│   │   ├── idea.yml
│   │   └── plan.yml
│   └── workflows/
│       ├── backlog.yml         # 백로그 스케줄러 (8 AM KST) ⭐
│       ├── ci.yml              # CI 파이프라인
│       └── orchestrator.yml    # 레거시 오케스트레이터
├── data/
│   └── trends/                 # 트렌드 분석 저장소 ⭐
│       ├── YYYY/MM/YYYY-MM-DD.md
│       └── idea_links.json
├── docs/
│   └── labels.md               # 라벨 문서
├── prompts/                    # 프롬프트 템플릿
├── src/agentic_orchestrator/
│   ├── __init__.py
│   ├── backlog.py              # 백로그 워크플로우 + TrendBasedIdeaGenerator ⭐
│   ├── cli.py                  # CLI 명령어 (트렌드 명령어 추가) ⭐
│   ├── github_client.py        # GitHub API (source:trend 라벨) ⭐
│   ├── orchestrator.py         # 레거시 오케스트레이터
│   ├── state.py                # 상태 관리
│   ├── handlers/               # 스테이지 핸들러
│   ├── providers/              # LLM 어댑터
│   ├── trends/                 # 트렌드 분석 모듈
│   │   ├── __init__.py
│   │   ├── models.py           # 데이터 모델
│   │   ├── feeds.py            # RSS 피드 파싱
│   │   ├── analyzer.py         # 트렌드 분석
│   │   └── storage.py          # 저장소
│   ├── debate/                 # 멀티 에이전트 토론 모듈 ⭐ NEW
│   │   ├── __init__.py
│   │   ├── roles.py            # 역할 정의 + 이중 언어 프롬프트
│   │   ├── moderator.py        # 라운드 순환 로직
│   │   ├── debate_session.py   # 토론 세션 관리
│   │   └── discussion_record.py # 토론 기록 포맷팅
│   └── utils/                  # 유틸리티 (debate 설정 추가)
├── tests/
│   ├── test_backlog.py         # 백로그 테스트
│   ├── test_orchestrator.py
│   ├── test_providers.py
│   ├── test_state.py
│   └── test_utils.py
├── .env.example
├── CHANGELOG.ko.md             # 한국어 변경 이력
├── CHANGELOG.md
├── LICENSE
├── PROGRESS.md                 # 이 파일
├── README.ko.md                # 한국어 README
├── README.md
├── config.yaml                 # trends 섹션 추가 ⭐
└── pyproject.toml              # feedparser 의존성 ⭐
```

---

## 다음 단계 (예정)

### 단기
- [ ] 원격 저장소 푸시 (인증 설정 필요)
- [ ] 실제 환경에서 `ao backlog run` 테스트
- [ ] Gemini SDK 마이그레이션 (`google.generativeai` → `google.genai`)

### 중기
- [ ] 스마트 컨트랙트 개발 지원 강화
- [ ] 멀티 프로젝트 오케스트레이션
- [ ] 웹 대시보드

### 장기
- [ ] Slack/Discord 알림
- [ ] 비용 추적 및 예산 제한
- [ ] 성능 모니터링

---

## 환경 설정

### 필수 환경 변수
```bash
GITHUB_TOKEN=ghp_xxxxx      # GitHub PAT
GITHUB_OWNER=mossland       # 저장소 소유자
GITHUB_REPO=agentic-orchestrator
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 선택 환경 변수
```bash
OPENAI_API_KEY=sk-xxxxx
GEMINI_API_KEY=AIzaSyxxxxx
DRY_RUN=false
```

---

## 실행 방법

```bash
# 설치
python -m venv venv
source venv/bin/activate
pip install -e .

# 라벨 설정
ao backlog setup

# 아이디어 생성
ao backlog generate --count 2

# 프로모션 처리
ao backlog process

# 전체 사이클
ao backlog run
```

---

*마지막 업데이트: 2026-01-04 (v0.4.0)*
