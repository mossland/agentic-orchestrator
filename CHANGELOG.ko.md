# 변경 이력

**한국어** | [English](CHANGELOG.md)

Mossland Agentic Orchestrator의 모든 주요 변경 사항을 이 파일에 문서화합니다.

이 형식은 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)를 기반으로 하며,
이 프로젝트는 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 준수합니다.

## [0.4.0] - 2026-01-04

### 추가됨

#### PLAN 생성을 위한 멀티 에이전트 토론 시스템
- **4개 토론 역할**: 창업자, VC (a16z/Sequoia 수준), Accelerator (YC/Techstars 수준), 창업가 친구
- **3개 AI 프로바이더**: Claude, ChatGPT, Gemini가 매 라운드 역할을 순환하며 다양한 관점 제공
- **역할 순환**: 각 라운드마다 다른 AI가 다른 역할 담당
- **조기 종료**: 창업자가 "충분히 개선됨" 판단 시 또는 최대 5라운드에서 토론 종료
- **토론 기록**: 전체 토론 히스토리가 접기/펼치기 가능한 GitHub 댓글로 저장

#### 토론 모듈 (`src/agentic_orchestrator/debate/`)
- `roles.py` - 이중 언어 프롬프트 (영어 + 한국어)가 포함된 역할 정의
- `moderator.py` - 라운드 순환 매트릭스 및 종료 로직
- `debate_session.py` - 전체 토론 세션 오케스트레이션
- `discussion_record.py` - GitHub 댓글 포맷팅

#### Plan 거부 워크플로우
- **`reject:plan` 라벨**: PLAN을 거부하고 원본 아이디어에서 재생성
- **`ao backlog reject <plan_number>`**: 계획 거부를 위한 CLI 명령어
- **자동 리셋**: 거부된 plan이 닫히고, 원본 아이디어에 `promote:to-plan` 복원

#### 이중 언어 지원
- 모든 토론 프롬프트가 영어로 작성되고 한국어 번역 요청 포함
- 토론 기록은 "English / 한국어" 형식으로 표시
- 기획서 추출에 `[PLAN_START]`/`[PLAN_END]` 마커 사용으로 신뢰성 향상

### 변경됨

- PlanGenerator가 3개 프로바이더 모두 사용 가능 시 멀티 에이전트 토론 사용
- 프로바이더 불가 시 단일 에이전트 생성으로 폴백
- `run_cycle()`에서 거부 처리가 프로모션 처리 전에 실행
- `_find_existing_plan_for_idea()`가 열린 이슈만 검색 (닫힌/거부된 이슈 무시)

### 설정

`config.yaml`에 새 `debate` 섹션:
```yaml
debate:
  enabled: true
  max_rounds: 5
  min_rounds: 1
  require_all_approval: false
```

## [0.3.0] - 2026-01-04

### 추가됨

#### 트렌드 기반 아이디어 생성
- **RSS 피드 통합**: AI, Crypto, Finance, Security, Dev 5개 카테고리의 17개 RSS 피드에서 기사 수집
- **트렌드 분석**: Claude를 사용하여 뉴스 기사에서 트렌딩 토픽 식별
- **다중 기간 분석**: 24시간, 1주, 1개월 기간에 걸쳐 트렌드 분석
- **트렌드 기반 아이디어**: 현재 트렌드를 기반으로 Web3 마이크로 서비스 아이디어 생성
- **트렌드 저장소**: YAML frontmatter가 포함된 Markdown 파일로 트렌드 분석 결과 저장

#### 새 트렌드 모듈
- `FeedFetcher` - feedparser를 사용한 RSS/Atom 피드 파싱
- `TrendAnalyzer` - Claude를 사용한 LLM 기반 트렌드 추출
- `TrendStorage` - `data/trends/YYYY/MM/`에 Markdown 파일 저장
- `TrendBasedIdeaGenerator` - 트렌딩 토픽에서 아이디어 생성

#### 새 라벨
- `source:trend` - 트렌드 분석에서 생성된 아이디어 표시

#### 새 CLI 명령어
- `ao backlog analyze-trends` - RSS 피드 수집 및 분석
- `ao backlog generate-trends` - 트렌드 기반 아이디어 생성
- `ao backlog trends-status` - 트렌드 분석 이력 표시

#### CLI 업데이트
- `ao backlog run`에 `--trend-ideas` 및 `--analyze-trends` 옵션 추가
- `ao backlog status`에서 트렌드 기반 아이디어 수 표시

#### GitHub Actions
- 스케줄을 매일 오전 8시 KST (23:00 UTC)로 변경
- 새 `run-with-trends` 명령 (기본 일일 실행)
- `generate-trends`, `analyze-trends`, `trends-status` 명령 추가

### 변경됨

- 기본 일일 실행: 전통적 아이디어 1개 + 트렌드 기반 아이디어 2개와 트렌드 분석
- 트렌드 데이터는 `data/trends/` 디렉토리에 저장 (90일 보존)

### 설정

`config.yaml`에 새 `trends` 섹션:
```yaml
trends:
  ideas:
    traditional_count: 1
    trend_based_count: 2
  periods: [24h, 1w, 1m]
  storage:
    directory: data/trends
    retention_days: 90
  feeds:
    ai: [OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News]
    crypto: [CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate]
    finance: [CNBC Finance]
    security: [The Hacker News, Krebs on Security]
    dev: [The Verge, Ars Technica, Stack Overflow Blog]
```

### 의존성

- RSS/Atom 파싱을 위한 `feedparser>=6.0.0` 추가

## [0.2.1] - 2025-01-04

### 추가됨

#### 안정성 개선
- **멱등성 보호**: 라벨 및 기존 아티팩트 확인을 통해 중복 plan/dev 생성 방지
- **Lock 타임아웃 메커니즘**: 크래시된 프로세스의 stale lock 감지 및 제거
- **환경 변수 검증**: 필수 환경 변수의 조기 검증 및 도움말 오류 메시지 제공
- **부분 실패 롤백**: 후속 작업 실패 시 plan 이슈 자동 닫기

#### 새 테스트
- v0.2.1 기능(멱등성, lock 타임아웃, 환경 검증, 롤백)을 위한 22개의 새 테스트
- 총 테스트 수 83개에서 105개로 증가

### 변경됨

- Lock 파일에 stale lock 감지를 위한 PID 및 타임스탬프 포함
- Config.get()이 기본값과 함께 중첩 키 조회를 올바르게 지원
- CLI 명령이 실행 전에 환경 검증 수행

### 기술 세부사항

- Lock 타임아웃 기본값 300초 (config.yaml로 설정 가능)
- signal 0을 사용한 프로세스 생존 확인
- 롤백 시 닫힌 이슈에 `rollback:failed` 라벨 추가

## [0.2.0] - 2025-01-03

### 추가됨

#### 백로그 기반 워크플로우
- **GitHub Issues를 UI/DB로 사용**: 아이디어와 계획을 GitHub Issues로 저장
- **휴먼 인 더 루프**: 스테이지 전환을 위한 라벨 기반 프로모션 시스템
- **GitHubClient**: Issues 및 Labels를 위한 완전한 GitHub API 통합
- **BacklogOrchestrator**: 백로그 기반 워크플로우를 위한 새 오케스트레이터

#### 프로모션 시스템
- 아이디어를 계획 스테이지로 프로모션하는 `promote:to-plan` 라벨
- 계획을 개발 스테이지로 프로모션하는 `promote:to-dev` 라벨
- 추적을 위한 `processed:to-plan` 및 `processed:to-dev` 라벨
- 처리 후 자동 라벨 관리

#### 새 CLI 명령어
- `ao backlog run`: 전체 오케스트레이션 사이클 실행
- `ao backlog generate`: 새 아이디어 이슈 생성
- `ao backlog process`: 대기 중인 프로모션 처리
- `ao backlog status`: 백로그 상태 표시
- `ao backlog setup`: 저장소에 필요한 라벨 설정

#### GitHub 통합
- 아이디어(`idea.yml`) 및 계획(`plan.yml`)용 이슈 템플릿
- 자동 실행을 위한 스케줄 워크플로우(`backlog.yml`)
- 라벨 문서(`docs/labels.md`)

#### 동시성 제어
- 동시 실행 방지를 위한 파일 기반 잠금
- 처리된 라벨을 통한 중복 방지
- cron/스케줄 실행에 안전

### 변경됨

- 자동 진행에서 사람 가이드 방식으로 워크플로우 모델 변경
- 백로그 기반 워크플로우를 위해 README.md 재작성
- GitHub 설정 변수로 `.env.example` 업데이트

### 기술 세부사항

- 비동기 가능 HTTP 클라이언트로 `httpx` 사용
- 83개 단위 테스트 통과
- 테스트를 위한 완전한 드라이런 지원

## [0.1.0] - 2025-01-03

### 추가됨

#### 코어 오케스트레이터
- 스테이지가 있는 상태 머신: IDEATION → PLANNING_DRAFT → PLANNING_REVIEW → DEV → QA → DONE
- YAML 기반 상태 영속화 (`.agent/state.yaml`)
- 계획 및 개발 사이클에 대한 설정 가능한 제한이 있는 반복 추적
- 품질 메트릭 추적 (리뷰 점수, 테스트 결과)

#### LLM 프로바이더 어댑터
- **Claude Provider**: CLI 모드(Claude Code) 및 API 모드 모두 지원
- **OpenAI Provider**: 독립적인 리뷰를 위한 GPT 모델 (기본: gpt-5.2-chat-latest)
- **Gemini Provider**: 빠른 에이전틱 태스크 (기본: gemini-3-flash-preview)
- Rate limit에 대한 지수 백오프로 자동 재시도
- 모든 프로바이더에 대한 폴백 모델 지원
- 적절한 오류 처리와 함께 할당량 소진 감지

#### 스테이지 핸들러
- **Ideation**: 모스랜드 생태계를 위한 Web3 서비스 아이디어 생성
- **Planning Draft**: PRD, 아키텍처, 태스크, 수용 기준 생성
- **Planning Review**: OpenAI/Gemini를 사용한 외부 리뷰
- **Development**: Claude Code를 사용한 기능 구현
- **Quality Assurance**: 테스트, 코드 리뷰, 보안 검사 실행
- **Done**: 완료 보고서 생성

#### CLI 명령어
- `ao init`: 새 프로젝트 초기화
- `ao step`: 단일 파이프라인 스텝 실행
- `ao loop`: 가드레일과 함께 연속 모드로 실행
- `ao status`: 현재 상태 표시 (--json 지원)
- `ao resume`: 일시 중지된 상태에서 재개
- `ao reset`: 오케스트레이터 상태 초기화
- `ao push`: 리모트에 변경사항 푸시

#### 오류 처리
- 자동 대기 및 재시도로 Rate limit 감지
- 할당량 소진 알림 (`alerts/quota.md`)
- 로그 및 커밋에서 민감한 데이터 마스킹
- 무한 루프 방지를 위한 최대 재시도 제한

#### 인프라
- 모든 스테이지에 대한 프롬프트 템플릿
- GitHub Actions CI 워크플로우 (테스트, 린트)
- GitHub Actions 오케스트레이터 워크플로우 (스케줄/수동)
- 포괄적인 단위 테스트

### 설정
- `.env`를 통한 환경 변수
- YAML 설정 (`config.yaml`)
- 테스트를 위한 드라이런 모드
- 재현성을 위한 고정 모델 버전

## [미출시]

### 계획됨
- 향상된 스마트 컨트랙트 개발 지원
- 멀티 프로젝트 오케스트레이션
- 모니터링용 웹 대시보드
- Slack/Discord 알림
- 비용 추적 및 예산 제한
