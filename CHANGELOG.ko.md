# 변경 이력

**한국어** | [English](CHANGELOG.md)

Mossland Agentic Orchestrator의 모든 주요 변경 사항을 이 파일에 문서화합니다.

이 형식은 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)를 기반으로 하며,
이 프로젝트는 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 준수합니다.

## [0.6.5] - 2026-02-01

### 수정됨

#### 백엔드 안정성 및 성능 (시스템 점검)
- **Ollama 쓰로틀 락 병목 (H3)**: `_wait_for_throttle`에서 `asyncio.sleep()` 중 락 해제, 다수 에이전트 동시 LLM 요청 시 직렬화 방지
- **토론 타임아웃 (H4)**: 프로덕션 모드에서 무한 실행 방지를 위한 45분 전체 타임아웃 (`DEBATE_TIMEOUT_SECONDS`) 추가
- **API 에러 응답 일관성 (H5)**: dict 기반 에러 응답(`{"error": "..."}`)을 `HTTPException(status_code=404)`로 통일 (토론 상세, 아이디어 상세, 아이디어 계보, 플랜 상세)
- **중복 프로젝트 생성 방지 (M1)**: `_create_project_record()`에 중복 체크 추가 - 동일 Plan에 "generating" 또는 "ready" 상태 프로젝트가 있으면 기존 ID 반환
- **Job 상태 영속화 (M2)**: 프로젝트 생성 작업 상태가 `data/project_jobs.json`에 저장되어 서버 재시작 시에도 유지
- **Plan 상세에 `title_ko` 누락 (M3)**: `/plans/{id}` 응답에 `title_ko`, `final_plan_ko` 필드 추가
- **Signal 페이지네이션 (M5)**: Python 슬라이싱을 SQL `LIMIT/OFFSET`으로 교체, `count_recent_filtered()` 추가
- **토론 페이지네이션**: debates 엔드포인트에서 SQL 레벨 페이지네이션 적용 (`get_all_sessions()`)
- **LLM Fallback 무한 루프 (L2)**: fallback도 실패 시 즉시 예외 발생하도록 try/except 추가
- **점수 기본값 5.0 문제 (L3)**: 점수 추출 실패 시 임의 5.0 할당 대신 경고 로깅 후 스킵

### 변경됨
- **config test_mode 통일 (H2)**: `debate.test_mode: false`로 설정하여 `throttling.test_mode: false`와 일치 (프로덕션 모드)
- **print → logger (L1)**: `ollama.py`, `router.py`, `aggregator.py`의 모든 `print()` 호출을 `logger.error()`/`logger.info()`로 교체

---

## [0.6.4] - 2026-01-25

### 추가됨

#### 외부 링크 접근을 위한 동적 상세 페이지
- **직접 URL 접근**: 외부 링크가 전용 상세 페이지로 연결
  - `/signals/{id}` - 시그널 상세 페이지
  - `/ideas/{id}` - 아이디어 상세 페이지
  - `/plans/{id}` - 플랜 상세 페이지
  - `/projects/{id}` - 프로젝트 상세 페이지
- **SEO 최적화 메타데이터**: 링크 공유를 위한 Open Graph 및 Twitter 카드 지원
- **새 백엔드 엔드포인트**: `GET /signals/{signal_id}` 단일 시그널 조회
- **공유 레이아웃 컴포넌트**: 네비게이션, 로딩/에러 상태가 포함된 `DetailPageLayout`
- **다국어 지원**: 상세 페이지에 EN/KO 로컬라이제이션 완전 지원

---

## [0.6.3] - 2026-01-25

### 추가됨

#### 프로덕션 수준 코드 생성
- **향상된 Plan 파서**: 포괄적인 추출을 위한 Deep LLM 파싱
  - 새 데이터클래스: `DataEntity`, `ExternalService`, `UIComponent`, `SmartContractSpec`
  - 상세 엔티티, 서비스, 컴포넌트 추출을 위한 `parse_deep_with_llm()`
  - 외부 서비스 탐지 (Twitter API, Coingecko, Etherscan, WebSocket 등)
- **풀 프로젝트 제너레이터**: 스캐폴드 대신 프로덕션 레디 코드
  - `generate_full_project()` - 고품질 생성을 위한 메인 진입점
  - 비즈니스 로직이 포함된 완전한 FastAPI/Express 백엔드
  - 모든 페이지와 컴포넌트가 포함된 완전한 Next.js/React 프론트엔드
  - Hardhat 테스트 프레임워크가 포함된 Solidity 스마트 컨트랙트
  - 외부 서비스 통합 레이어
  - 데이터베이스 스키마 및 마이그레이션
  - Docker 설정

#### 우선순위 기반 프로젝트 생성
- **고우선순위 Plan 자동 생성**: 점수 >= 8.0
  - Plan 자동 승인 및 프로젝트 생성 트리거
  - `config.yaml`에서 임계값 설정 가능 (`project.auto_generate.min_score`)
- **저우선순위 Plan 수동 승인**: 점수 < 8.0
  - "draft" 상태로 Plan 생성
  - 프로젝트 생성 전 수동 승인 필요

#### 수동 제어를 위한 새 API 엔드포인트
- `POST /plans/{plan_id}/approve` - Draft plan 수동 승인
  - 즉시 프로젝트 생성 트리거 옵션 (`generate_project=true`)
  - 사용자가 어떤 낮은 점수 Plan을 개발할지 제어 가능
- `GET /plans/pending-approval` - 수동 승인 대기 중인 draft plan 목록
  - 결정 컨텍스트를 위한 아이디어 점수 표시

### 변경됨
- 커밋 메시지가 "scaffold"에서 "production-quality code"로 변경
- 프로젝트 생성 파이프라인이 이제 완전한, 실행 가능한 코드 생성

---

## [0.6.2] - 2026-01-25

### 추가됨

#### 파이프라인 프로젝트 스테이지
- **파이프라인 모달 지원**: 파이프라인 상태 모달에서 Projects 스테이지 완전 지원
  - 상태 배지와 함께 프로젝트 가져오기 및 표시
  - "View All Projects" 버튼으로 `/projects` 페이지 이동
  - 도움말이 있는 빈 상태 표시
- **GitHub에서 코드 보기 버튼**: ProjectDetail 모달에 새 버튼 추가
  - 프로젝트 코드 디렉토리로 직접 링크: `github.com/.../tree/main/projects/{project-name}`
  - Issue 링크와 분리하여 명확하게 구분

#### GitHub 자동 푸시
- **자동 Git 커밋/푸시**: 생성된 프로젝트가 자동으로 커밋 및 푸시됨
  - 스캐폴드 생성 후 자동으로 `git add`, `git commit`, `git push` 실행
  - 커밋 메시지: `feat: auto-generate project scaffold for {project-name}`
  - 푸시 실패 시 프로젝트 생성은 차단되지 않음 (경고 로그만 출력)

### 수정됨
- **PipelineDetail Projects 스테이지**: Projects 클릭 시 "#" 텍스트만 표시되는 문제 수정
  - 데이터 가져오기에 `projects` stageId 처리 추가
  - 적절한 설명, 빈 상태 이모지, 네비게이션 추가

---

## [0.6.1] - 2026-01-25

### 추가됨

#### Projects UI 통합
- **프로젝트 페이지**: 상태 필터링(전체/완료/생성 중/오류)이 있는 새 `/projects` 페이지
  - 기술 스택 배지 (프론트엔드/백엔드/블록체인)
  - 디렉토리 경로 표시
  - 생성된 파일 수
  - 클릭하여 프로젝트 상세 모달 열기
- **대시보드 통합**: 최근 5개 프로젝트를 보여주는 "Recent Projects" 섹션
  - `/projects` 페이지 직접 링크
  - 상태 표시기 및 기술 스택 표시
- **아이디어 페이지 프로젝트 탭**: 빠른 접근을 위해 아이디어 페이지에 프로젝트 섹션 추가

### 수정됨
- **API 클라이언트 타임아웃**: 네트워크 지연 처리를 위해 타임아웃을 3초에서 10초로 증가
  - "Using mock stats/pipeline due to API error" 경고 해결
  - 느린 연결에서 조기 요청 중단 방지
- **Projects 테이블 생성**: `/projects` 엔드포인트 500 오류 수정
  - 데이터베이스에 누락된 `projects` 테이블 생성
  - 다른 모델과 함께 테이블 자동 생성

### 기술 사항
- 재사용 가능한 프로젝트 목록 표시를 위한 `ProjectsSection` 컴포넌트 추가
- `ApiClient`에 10초 타임아웃 업데이트 (AbortController)
- 데이터베이스 마이그레이션으로 `projects` 테이블 존재 보장

---

## [0.6.0] "Project Generator" - 2026-01-25

### 추가됨

#### Plan → Project 자동 생성
- **프로젝트 스캐폴드 모듈**: 승인된 Plan에서 자동 프로젝트 생성을 위한 새 `project/` 패키지
  - `parser.py` - Plan 마크다운을 구조화된 데이터로 파싱 (TechStack, APIEndpoint, ProjectTask)
  - `templates.py` - 기술 스택 템플릿 (Next.js, React, Vue, FastAPI, Express, Hardhat, Anchor)
  - `generator.py` - 작업별 모델 라우팅이 있는 LLM 기반 코드 생성
  - `scaffold.py` - 전체 프로젝트 생성 파이프라인 오케스트레이션
- **작업별 LLM 모델**: 다른 작업에 다른 모델 사용
  - `glm-4.7-flash` - 빠른 Plan 파싱 및 구조 추출
  - `qwen2.5:32b` - 메인 코드 생성 (컴포넌트, API, 모델)
  - `llama3.3:70b` - 복잡한 아키텍처 설계
  - `phi4:14b` - 간단한 작업 및 폴백
- **하이브리드 트리거 시스템**:
  - **자동 생성**: 점수 ≥ 8.0인 Plan은 자동으로 프로젝트 생성
  - **수동 버튼**: 낮은 점수의 Plan은 UI에서 생성 트리거 가능
- **데이터베이스 스키마**: `projects` 테이블 추가
  - `plan_id`, `name`, `directory_path`, `tech_stack` (JSON), `status`, `files_generated`
- **프로젝트 리포지토리**: 프로젝트를 위한 전체 CRUD 작업

#### 새 API 엔드포인트
- `POST /plans/{plan_id}/generate-project` - 비동기 프로젝트 생성 트리거
- `GET /plans/{plan_id}/project` - 특정 Plan의 프로젝트 조회
- `GET /projects` - 생성된 모든 프로젝트 목록
- `GET /projects/{project_id}` - 프로젝트 상세
- `GET /jobs/{job_id}` - 비동기 작업 상태 확인

#### 프론트엔드 업데이트
- **Generate Project 버튼**: 승인된 Plan을 위해 `PlanDetail.tsx`에 추가
- **프로젝트 상태 표시**: 생성 중 스피너, 준비 완료 상태의 기술 스택 배지, 오류 상태의 재시도 버튼
- **작업 폴링**: 생성 중 자동 상태 폴링
- **API 클라이언트 메서드**: `generateProject()`, `getProjects()`, `getProjectDetail()`, `getJobStatus()`, `getPlanProject()`

### 변경됨
- 스케줄러가 토론 완료 후 프로젝트 자동 생성 통합
- Plan 생성 시 `final_plan` 및 `final_plan_ko` 콘텐츠를 올바르게 저장
- 파이프라인 흐름 확장: Ideas → Plans → Projects (점수 ≥ 8.0인 경우)

### 설정
`config.yaml`에 새 `project` 섹션:
```yaml
project:
  auto_generate:
    enabled: true
    min_score: 8.0
    max_concurrent: 1
  llm:
    parsing: "glm-4.7-flash"
    code_generation: "qwen2.5:32b"
    architecture: "llama3.3:70b"
    fallback: "phi4:14b"
  output_dir: "projects"
```

### 기술 사항
- `ProjectScaffold`, `ProjectCodeGenerator`, `PlanParser`, `TemplateManager` 클래스 추가
- 데이터베이스 레이어에 `Project` 모델 및 `ProjectRepository` 추가
- 스케줄러에 `_auto_generate_project()` 및 `_load_project_config()` 추가
- `_auto_score_and_save_ideas()`가 프로젝트 생성을 위해 `final_plan_content` 전달하도록 수정
- `ApiProject`, `GenerateProjectResponse`, `ProjectJobStatus` TypeScript 타입 추가

---

## [0.5.1] "Bilingual" - 2026-01-24

### 추가됨

#### 이중 언어 콘텐츠 지원 (EN/KO)
- **양방향 번역**: ContentTranslator가 소스 언어를 감지하고 자동 번역
  - 한글 콘텐츠 → 영어 (메인 필드) + 한글 (`*_ko` 필드)
  - 영어 콘텐츠 → 영어 (메인 필드) + 한글 번역 (`*_ko` 필드)
- **데이터베이스 스키마**: Ideas와 Plans에 한글 필드 추가
  - `Idea`: `title_ko`, `summary_ko`, `description_ko`
  - `Plan`: `title_ko`, `final_plan_ko`
- **프론트엔드 로컬라이제이션**: UI가 EN/KO 토글에 따라 모든 콘텐츠 표시
  - 아이디어 목록, 상세 모달
  - 플랜 목록, 상세 모달
  - 트렌드 목록, 상세 모달
- **마이그레이션 스크립트**: 기존 데이터를 번역으로 채우는 `migrate_bilingual.py`
- **IdeaContent 컴포넌트**: 구조화된 JSON 아이디어 표시:
  - 색상 테두리가 있는 핵심 분석
  - 시각적 인디케이터가 있는 기회/리스크 그리드
  - 기능 목록과 기술 스택 배지가 있는 제안
  - 로드맵 타임라인
  - 목표 지표가 있는 KPI

### 수정됨
- **TrendHeatmap 크기**: 셀 높이를 `aspect-square`에서 `h-6`으로 축소
- **AdapterDetailModal**: 첫 오픈 시 빈 모달 수정 - 첫 번째 어댑터 자동 선택
- **트렌드 분석**: LLM 프롬프트를 영어 전용으로 변경 (한글은 번역으로 제공)
- **파이프라인 모달**: signals 및 trends 스테이지의 VIEW ALL 버튼 수정
- **날짜 로케일 표시**: EN 로케일에서 한국어 날짜 표시 문제 수정
  - `date.ts`에 `toBrowserLocale()` 헬퍼 추가 (en→en-US, ko→ko-KR)
  - 기본 로케일을 'ko-KR'에서 'en'으로 변경
  - 모든 날짜 포맷 함수가 사용자 로케일 준수
- **토론 JSON 콘텐츠**: 토론 모달에서 원시 JSON 표시 문제 수정
  - JSON 파싱 및 읽기 쉬운 필드 추출을 위한 `extractReadableContent()` 헬퍼 추가
  - LiveDebateViewer, DebateConversation, DebateTimeline 컴포넌트에 적용
- **마크다운 렌더링**: 토론 메시지에 마크다운 지원 추가
  - `marked` 라이브러리를 사용한 `MarkdownContent` 컴포넌트 생성
  - `**bold**`는 시안 색상, `*italic*`은 보라 색상으로 렌더링
  - 리스트, 코드 블록, 헤더, 인용문 스타일 적용

### 기술 사항
- `ContentTranslator` 클래스 추가: `ensure_bilingual()`, `translate_to_english()`, `translate_to_korean()` 메서드
- 한글/영어 감지를 위한 `_detect_language()` 헬퍼 추가
- `_auto_score_and_save_ideas()`를 양방향 번역 사용하도록 업데이트
- 프론트엔드 컴포넌트에 `getLocalizedText()` 헬퍼 추가
- 구조화된 JSON 파싱 및 표시를 위한 `IdeaContent.tsx` 컴포넌트 추가
- 성능을 위해 시그널 번역 비활성화 (시그널은 영어 전용)

---

## [0.5.0] - 2026-01-24

### 추가됨

#### 창의성 프레임워크 강화 (Phase 1)
- **SCAMPER 창의성 프롬프트**: 발산 단계에서 구조화된 SCAMPER 기법 사용
  - 라운드 1: 대체 & 결합 (구성요소 교체, 개념 병합)
  - 라운드 2: 적용 & 수정 (타 산업 영감, 규모 변경)
  - 라운드 3: 전용, 제거 & 역발상 (역설적 사고)
- **측면사고 프롬프트**: 라운드별 교차 적용되는 창의성 기법
  - Blue Sky Thinking (제약 없는 상상)
  - Paradox Approach (역문제 해결)
  - Cross-Domain Innovation (타 산업 패턴 차용)
- **온도 상향**: 발산 단계 온도를 0.95로 상향 (기존 0.9)하여 더 창의적인 출력 유도

#### Coingecko 시장 어댑터
- **트렌딩 코인**: 실시간 검색 트렌드 감지
- **상위 변동종목**: 상위 5개 상승/하락 종목 (24시간, >10% 변동 임계값)
- **거래량 급등**: 비정상 거래 활동 감지 (거래량 > 시가총액의 50%)
- **글로벌 시장 통계**: 전체 시가총액 변동, BTC 도미넌스 알림
- **추적 코인**: MOC (Mossland) 포함 16개 특정 코인

#### 시그널 시간 감쇠
- **신선도 가중치**: 시그널 점수가 경과 시간에 따라 감쇠
  - 0-1시간: 100% 가중치
  - 1-6시간: 90% 가중치
  - 6-12시간: 80% 가중치
  - 12-24시간: 60% 가중치
  - 24-48시간: 40% 가중치
  - 48시간+: 20% 가중치
- **감쇠 로깅**: 분석 주기별 감쇠 분포 디버그 정보 표시

#### 대시보드 UX 개선
- **스켈레톤 로더**: 트렌드 페이지와 아이디어 페이지에 적절한 로딩 스켈레톤 적용
  - 점수, 제목, 키워드 플레이스홀더가 있는 트렌드 카드
  - 스테이지 인디케이터가 있는 파이프라인 뷰
  - 배지와 콘텐츠 플레이스홀더가 있는 리스트 아이템

### 변경됨
- 시그널 애그리게이터에 Coingecko 어댑터 기본 포함
- 트렌드 분석 시 시그널 처리 전 시간 감쇠 적용

### 기술 사항
- `DebateProtocol`에 `SCAMPER_TECHNIQUES`, `LATERAL_THINKING` 딕셔너리 추가
- `DebateProtocol`에 `get_creativity_technique()` 메서드 추가
- `CoingeckoAdapter` 클래스 추가 (trending, movers, global stats, tracked coins 메서드)
- 스케줄러에 `_calculate_time_decay()`, `_apply_time_decay_to_signals()` 함수 추가
- `TrendSkeleton`, `PipelineSkeleton`, `ListItemSkeleton`, `ListSkeleton` React 컴포넌트 추가

---

## [0.4.2] - 2026-01-24

### 추가됨

#### 아이디어 창의성 및 다양성 향상
- **다양성 인식 에이전트 선택**: 성격 축 기반 균형 선택으로 각 토론 라운드에서 다양한 에이전트 타입 보장
- **도전자 역할 보장**: 집단사고 방지를 위해 각 라운드에 최소 1명의 도전자 성격 에이전트 포함
- **아이디어 유사도 피드백**: 아이디어 생성 시 Jaccard 유사도 점수와 차별화 힌트 제공
- **참신성 가중치 강화**: 수렴 단계에서 참신성 가중치를 30%로 상향 (기존 20%, 가장 중요한 기준)

#### 시그널 품질 향상
- **콘텐츠 검증 레이어**: 최소 길이, 언어 (한국어/영어), 스팸 패턴으로 시그널 필터링
- **의미론적 중복 제거**: Jaccard 유사도 기반 중복 제거로 다른 소스의 유사 콘텐츠 필터링
- **참여도 임계값**: 소셜 어댑터에서 저참여 게시물 필터링 (Reddit: 10+ 점수, 3+ 댓글; Farcaster: 3+ 좋아요 또는 1+ 리캐스트)
- **감성 분석**: 키워드 기반 감성 감지 (긍정/부정/중립)를 시그널 점수에 통합

### 변경됨
- 시그널 중복 제거가 3단계 접근 방식 사용: 해시 중복 제거 → 콘텐츠 검증 → 의미론적 중복 제거
- 수렴 평가 기준이 명시적 가중치 점수 공식으로 재구성됨
- Twitter API 검색이 참여도 메트릭으로 트윗 필터링

### 기술 사항
- `MultiStageDebate`에 `_select_agents_with_diversity()`, `_ensure_challenger_presence()` 메서드 추가
- 차별화 힌트를 위한 `_calculate_idea_similarity()`, `_get_similarity_feedback()` 메서드 추가
- `SignalAggregator`에 `_validate_signal_content()`, `_is_semantic_duplicate()` 메서드 추가
- `SignalScorer`에 `_analyze_sentiment()`, `_score_sentiment()` 메서드 추가
- 소셜 어댑터들에 `_meets_engagement_threshold()` 메서드 추가

---

## [0.4.1] - 2026-01-24

### 추가됨

#### 시그널 어댑터 확장 (총 9개 어댑터)
- **Twitter/X 어댑터**: 10개 Nitter 인스턴스 풀, 20개 이상 추적 계정
- **Discord 어댑터**: Bot API 및 웹훅 지원, 7개 추적 서버
- **Lens Protocol 어댑터**: GraphQL API, 10개 추적 프로필
- **Farcaster 어댑터**: Neynar API, 10개 추적 사용자 및 채널
- **온체인 확장**: DEX 거래량, 고래 알림, 스테이블코인 흐름 (DefiLlama)

#### 아이디어 품질 향상
- **JSON 출력 포맷**: 더 나은 파싱을 위한 구조화된 LLM 응답
- **콘텐츠 검증**: 최소 글자 수 요구 필수 섹션
- **제목 품질 점수**: 길이, 기술 키워드, Mossland 관련성 기반 0-10 점수

#### 대시보드 UX 개선
- **어댑터 상세 모달**: signals.conf 클릭 시 건강 상태 포함 상세 어댑터 정보 표시
- **스켈레톤 로딩**: 활동 피드 로딩 중 스켈레톤 애니메이션 표시
- **실제 활동 데이터**: `/activity` API가 목업 대신 실제 DB 데이터 반환

#### 새 API 엔드포인트
- `GET /adapters` - 상태, 소스, 건강 정보가 포함된 모든 시그널 어댑터 목록

### 변경됨
- 활동 피드가 더 이상 목업 데이터를 사용하지 않음; 실제 타임스탬프 (HH:MM:SS 형식) 표시
- 대시보드가 스켈레톤 로딩 상태와 함께 활동 데이터 로드

### 기술 사항
- `AdapterInfo` 타입 및 `fetchAdapters()` API 클라이언트 메서드 추가
- `ActivityFeed` 컴포넌트에 `isLoading` prop 추가

---

## [0.4.0] "Signal Storm" - 2026-01-22

### 추가됨

#### 멀티 스테이지 토론 시스템 (34 에이전트)
- **3단계 토론**: 발산 (12 에이전트) → 수렴 (12 에이전트) → 기획 (10 에이전트)
- **4축 성격 시스템**: 창의성, 분석력, 리스크 허용도, 협업 (0-10 척도)
- **토론 프로토콜**: `debate/protocol.py` - 단계, 메시지 타입, 설정
- **멀티 스테이지 오케스트레이션**: `debate/multi_stage.py` - 완전한 토론 흐름 관리

#### 다양한 시그널 소스 (5개 어댑터)
- **RSS 어댑터**: AI, Crypto, Finance, Security, Dev 5개 카테고리의 17개 피드
- **GitHub Events 어댑터**: 저장소 활동, 트렌딩 프로젝트, 이슈/PR 분석
- **온체인 어댑터**: MOC 토큰 트랜잭션, 스마트 컨트랙트 이벤트, DeFi 메트릭
- **소셜 미디어 어댑터**: X (트위터) 멘션, 커뮤니티 감성 분석
- **News API 어댑터**: 실시간 뉴스 집계, 키워드 기반 필터링

#### 하이브리드 LLM 라우터
- **로컬 모델**: Ollama 통합 (Qwen 32B, Llama 3, Mistral)
- **클라우드 API**: Claude, GPT-4, Gemini 폴백
- **지능형 라우팅**: 로컬과 클라우드 간 자동 폴백
- **예산 관리**: 비용 추적 및 제한

#### PM2 프로세스 관리
- **6개 서비스**: signals (30분), debate (6시간), backlog (매일), web, api, health (5분)
- **스케줄러 모듈**: `scheduler/tasks.py` - 비동기 태스크 구현
- **CLI 진입점**: `scheduler/__main__.py` - 커맨드 라인 인터페이스
- **생태계 설정**: `ecosystem.config.js` - PM2 설정

#### FastAPI 백엔드
- **REST API**: `/health`, `/status`, `/signals`, `/debates`, `/agents`, `/docs`
- **API 모듈**: `api/main.py` - FastAPI 애플리케이션
- **포트 3001**: 웹 대시보드와 분리

#### CLI 스타일 웹 인터페이스
- **레트로 터미널 테마**: JetBrains Mono 폰트, 스캔라인, 글로우 효과
- **터미널 컴포넌트**: `TerminalWindow.tsx`, 상태 표시기
- **에이전트 페이지**: `/agents` - 34개 에이전트 페르소나 표시
- **모바일 반응형**: 모든 화면 크기에 적응

### 변경됨

- CLI/터미널 미학으로 대시보드 재설계
- `$` 프롬프트 스타일로 네비게이션 업데이트
- 버전 "Signal Storm"으로 푸터 업데이트
- GitHub Actions 스케줄링을 PM2로 대체

### 제거됨

- `.github/workflows/backlog.yml` - PM2 moss-ao-backlog으로 대체
- `.github/workflows/orchestrator.yml` - PM2 moss-ao-debate으로 대체

### 기술 세부사항

- API 서버에 Python 3.12 필요
- 가상환경 설정: `.venv/`
- 충돌 방지를 위해 서비스 이름에 `moss-ao-` 접두사 사용

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
