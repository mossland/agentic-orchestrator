# MOSS.AO - Claude Code 참조 문서

이 문서는 Claude Code가 프로젝트 작업 시 참조할 수 있는 정보를 담고 있습니다.

## 프로젝트 개요

**MOSS.AO (Mossland Agentic Orchestrator)**는 AI 에이전트들이 토론을 통해 아이디어를 생성하고 기획안을 작성하는 멀티에이전트 오케스트레이션 시스템입니다.

- **공개 URL:** https://ao.moss.land
- **GitHub:** https://github.com/MosslandOpenDevs/agentic-orchestrator

## 핵심 철학

### 1. 다양한 시그널 소스 (10개 어댑터)

**목적:** 최신 트렌드를 빠르게 파악 → 신선한 아이디어의 기반 마련

```
RSS, GitHub, OnChain, Social, News, Twitter, Discord, Lens, Farcaster, Coingecko
                                    ↓
                        최신 트렌드 실시간 수집
                                    ↓
                        신선한 아이디어 기반 확보
```

### 2. 멀티에이전트 1차 (발산 단계)

**목적:** 뻔하지 않고, 다양한 시선으로 → 신선하고 창의적인 다양한 아이디어 도출

- **SCAMPER 창의성 기법**: 대체, 결합, 적용, 수정, 전용, 제거, 역발상
- **측면사고 프롬프트**: Blue Sky, 역설 접근, 교차 영역 혁신
- **다양성 인식 에이전트 선택**: 4축 성격 균형 (창의성, 분석력, 리스크, 협업)
- **도전자 역할 보장**: 집단사고 방지를 위한 반대 의견 에이전트

### 3. 멀티에이전트 2차 (수렴/기획 단계)

**목적:** 다양한 전문적 시각으로 → 구체적이고 실현 가능한 고품질 아이디어로 발전

- **가중치 평가**: 참신성 30%, 실현가능성 25%, 관련성 20%, 영향력 15%, 시급성 10%
- **상세 기획안 필수 섹션**: 프로젝트 개요, 기술 아키텍처, 실행 계획, 리스크, KPI
- **자동 점수화**: score ≥ 7.0 → 플랜 자동 생성, score < 4.0 → 아카이브

## 프로젝트 구조

```
agentic-orchestrator/
├── src/agentic_orchestrator/    # Python 백엔드
│   ├── api/                     # FastAPI 서버 (포트 3001)
│   │   └── main.py              # API 엔드포인트 정의
│   ├── db/                      # SQLAlchemy 모델 & 리포지토리
│   │   ├── models.py            # 데이터베이스 모델
│   │   ├── repositories.py      # 데이터 액세스 레이어
│   │   └── connection.py        # DB 연결 관리
│   ├── debate/                  # 멀티스테이지 토론 시스템
│   │   ├── multi_stage.py       # 3단계 토론 (발산→수렴→기획)
│   │   └── protocol.py          # 토론 프로토콜 정의
│   ├── llm/                     # LLM 라우터
│   │   └── router.py            # Ollama, Claude, OpenAI 라우팅
│   ├── personas/                # AI 에이전트 페르소나 (34명)
│   ├── project/                 # Plan → Project 자동 생성
│   │   ├── parser.py            # Plan 마크다운 파싱
│   │   ├── templates.py         # 기술 스택별 템플릿
│   │   ├── generator.py         # LLM 코드 생성
│   │   └── scaffold.py          # 프로젝트 생성 오케스트레이션
│   ├── scheduler/               # PM2 스케줄 작업
│   │   ├── __main__.py          # CLI 엔트리포인트
│   │   └── tasks.py             # 작업 구현 (signal, debate, backlog, project)
│   ├── translation/             # 양방향 번역 모듈
│   │   └── translator.py        # ContentTranslator (EN↔KO)
│   ├── scripts/                 # 유틸리티 스크립트
│   │   └── migrate_bilingual.py # 기존 데이터 번역 마이그레이션
│   └── signals/                 # 신호 수집기
│       ├── aggregator.py        # 신호 수집 조율
│       └── adapters/            # 시그널 어댑터 (10개)
│           ├── rss.py           # RSS 피드 (28개 소스)
│           ├── github_events.py # GitHub Trending/Releases
│           ├── onchain.py       # DefiLlama, Whale Alert, DEX
│           ├── social.py        # Reddit, Nitter
│           ├── news.py          # NewsAPI, Cryptopanic, HN
│           ├── twitter.py       # Twitter/X (Nitter RSS 풀)
│           ├── discord.py       # Discord 서버 공지
│           ├── lens.py          # Lens Protocol (GraphQL)
│           ├── farcaster.py     # Farcaster (Neynar API)
│           └── coingecko.py     # Coingecko (시장 데이터, 트렌딩)
├── website/                     # Next.js 프론트엔드 (포트 3000)
│   ├── src/app/                 # App Router 페이지
│   │   ├── page.tsx             # 대시보드 (/)
│   │   ├── ideas/page.tsx       # 아이디어 백로그
│   │   ├── debates/page.tsx     # 토론 목록 (실시간 폴링)
│   │   ├── agents/page.tsx      # 에이전트 목록
│   │   └── system/page.tsx      # 시스템 상태
│   ├── src/components/          # React 컴포넌트
│   │   ├── modals/              # 모달 시스템 (ModalProvider, TerminalModal)
│   │   └── details/             # 상세 보기 컴포넌트
│   └── src/lib/                 # 유틸리티
│       ├── api.ts               # API 클라이언트
│       ├── types.ts             # TypeScript 타입
│       └── i18n.tsx             # 다국어 지원 (EN/KO)
├── data/                        # 데이터 디렉토리
│   ├── orchestrator.db          # SQLite 데이터베이스
│   └── trends/                  # 트렌드 분석 결과 (마크다운)
├── projects/                    # 자동 생성된 프로젝트
│   └── {project-name}/          # LLM 생성 프로젝트 스캐폴드
├── docs/                        # 설계 문서
│   ├── pipeline.md              # 아이디어 생성 파이프라인
│   ├── labels.md                # GitHub 라벨 가이드
│   └── projects.md              # 프로젝트 관리 가이드
└── ecosystem.config.js          # PM2 설정
```

## 인프라 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         인터넷                                  │
│                            │                                    │
│                            ▼                                    │
│                    ao.moss.land                                 │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │   AWS Lightsail         │                        │
│              │   (Nginx Reverse Proxy) │                        │
│              └───────────┬─────────────┘                        │
│                          │                                      │
│            ┌─────────────┴─────────────┐                        │
│            │                           │                        │
│            ▼                           ▼                        │
│     /api/* 요청                   /* 요청                       │
│            │                           │                        │
│            ▼                           ▼                        │
│  ┌─────────────────────────────────────────────┐                │
│  │           개발/운영 서버                     │                │
│  │  ┌─────────────────┐  ┌─────────────────┐   │                │
│  │  │ FastAPI Backend │  │ Next.js Frontend│   │                │
│  │  │   Port: 3001    │  │   Port: 3000    │   │                │
│  │  └─────────────────┘  └─────────────────┘   │                │
│  └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

**실제 IP 주소는 `CLAUDE.local.md` 파일 참조 (gitignore 처리됨)**

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/status` | 시스템 상태 및 통계 |
| GET | `/signals` | 수집된 신호 목록 |
| GET | `/signals/{id}` | 시그널 상세 정보 |
| GET | `/trends` | 분석된 트렌드 |
| GET | `/ideas` | 아이디어 백로그 |
| GET | `/ideas/{id}` | 아이디어 상세 |
| GET | `/debates` | 토론 세션 목록 |
| GET | `/debates/{id}` | 토론 상세 (메시지 포함) |
| GET | `/plans` | 기획 문서 목록 |
| GET | `/plans/{id}` | 기획 문서 상세 |
| POST | `/plans/{id}/generate-project` | Plan에서 프로젝트 생성 (비동기) |
| GET | `/plans/{id}/project` | Plan의 프로젝트 조회 |
| GET | `/projects` | 생성된 프로젝트 목록 |
| GET | `/projects/{id}` | 프로젝트 상세 |
| GET | `/jobs/{id}` | 비동기 작업 상태 조회 |
| POST | `/plans/{id}/approve` | Draft 플랜 수동 승인 (generate_project=true로 즉시 프로젝트 생성 가능) |
| GET | `/plans/pending-approval` | 승인 대기 중인 Draft 플랜 목록 |
| GET | `/agents` | 에이전트 목록 |
| GET | `/adapters` | 시그널 어댑터 목록 및 상태 |
| GET | `/usage` | API 사용량 통계 |
| GET | `/activity` | 최근 활동 로그 (실제 DB 데이터 기반) |

## 데이터베이스 스키마

**위치:** `data/orchestrator.db` (SQLite)

### 주요 테이블

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| `signals` | 수집된 신호 | source, category, title, title_ko, score, sentiment |
| `trends` | 분석된 트렌드 | name, name_ko, description, description_ko, score |
| `ideas` | 생성된 아이디어 | title, title_ko, summary, summary_ko, status, score |
| `debate_sessions` | 토론 세션 | topic, phase, status, participants |
| `debate_messages` | 토론 메시지 | agent_id, agent_name, message_type, content, content_ko |
| `plans` | 기획 문서 | title, title_ko, final_plan, final_plan_ko, status |
| `projects` | 생성된 프로젝트 | plan_id, name, directory_path, tech_stack, status |
| `api_usage` | API 사용량 | provider, model, cost_usd, request_count |

### 중요 스키마 노트

- **`debate_sessions.idea_id`**: `nullable=True` (독립 토론 지원)
- **`ideas.score`**: 토론 중 에이전트들이 부여한 평균 점수
- **`*_ko` 필드**: 한글 번역 필드 (양방향 번역 지원)

## 환경 변수

### 웹사이트 (`website/.env.local`)

```bash
# 프로덕션: /api 사용 (Nginx 프록시 경유)
NEXT_PUBLIC_API_URL=/api

# 로컬 개발 시: 직접 백엔드 호출
# NEXT_PUBLIC_API_URL=http://localhost:3001
```

**중요:** `NEXT_PUBLIC_*` 변수는 빌드 시점에 포함되므로, 변경 후 반드시:
1. `npm run build`
2. `pm2 restart moss-ao-web`

## PM2 프로세스 관리

```bash
# 상태 확인
pm2 status

# 주요 프로세스
moss-ao-web      # Next.js 프론트엔드 (포트 3000) - 상시 실행
moss-ao-api      # FastAPI 백엔드 (포트 3001) - 상시 실행
moss-ao-signals  # 신호 수집기 (TEST: 10분, PROD: 30분)
moss-ao-trends   # 트렌드 분석 (TEST: 30분, PROD: 2시간)
moss-ao-debate   # 토론 스케줄러 (TEST: 1시간, PROD: 6시간)
moss-ao-backlog  # 백로그 처리 (TEST: 30분, PROD: 4시간)
moss-ao-health   # 헬스체크 (5분마다)

# 재시작 (환경변수 갱신 포함)
pm2 restart moss-ao-web --update-env
pm2 restart moss-ao-api --update-env

# 프로세스 삭제 후 재시작 (캐시된 환경변수 문제 시)
pm2 delete moss-ao-web && pm2 start ecosystem.config.js --only moss-ao-web

# 로그 확인
pm2 logs moss-ao-api --lines 50
pm2 logs moss-ao-debate --lines 100

# 설정 저장
pm2 save
```

### 현재 운영 모드: PRODUCTION

`ecosystem.config.js`의 `TEST_MODE = false`로 프로덕션 스케줄 적용 중:

| 작업 | 주기 | Cron |
|------|------|------|
| Signals | 30분마다 | `*/30 * * * *` |
| Trends | 2시간마다 | `0 */2 * * *` |
| Debate | 6시간마다 | `0 */6 * * *` |
| Backlog | 4시간마다 | `0 */4 * * *` |

토론 에이전트 설정 (`config.yaml`의 `debate.test_mode: false`):
- Divergence: 8 에이전트/라운드, 3라운드
- Convergence: 4 에이전트/라운드, 2라운드
- Planning: 5 에이전트/라운드, 2라운드
- **예상 시간**: ~30분+

## 개발 워크플로우

### 백엔드 변경 시

```bash
# 1. 코드 수정
# 2. API 서버 재시작
pm2 restart moss-ao-api

# 로그 확인
pm2 logs moss-ao-api --lines 30
```

### 프론트엔드 변경 시

```bash
# 1. 코드 수정
cd website

# 2. 빌드 (NEXT_PUBLIC_* 변수 포함)
npm run build

# 3. PM2 재시작
pm2 restart moss-ao-web

# 또는 개발 모드로 실행
npm run dev
```

### 데이터베이스 스키마 변경 시

SQLite는 ALTER COLUMN을 지원하지 않으므로 테이블 재생성 필요:

```sql
-- 1. 새 테이블 생성 (수정된 스키마)
CREATE TABLE table_new (...);

-- 2. 데이터 복사
INSERT INTO table_new SELECT ... FROM table_old;

-- 3. 기존 테이블 삭제
DROP TABLE table_old;

-- 4. 이름 변경
ALTER TABLE table_new RENAME TO table_old;

-- 5. 인덱스 재생성
CREATE INDEX ...;
```

## UI/UX 패턴

### 디자인 시스템

- **테마:** 다크 터미널 스타일
- **주요 색상:**
  - `#39ff14` (녹색) - 활성, 성공
  - `#00ffff` (시안) - 정보, 링크
  - `#ff6b35` (주황) - 경고, 토론
  - `#bd93f9` (보라) - 특수 기능
- **폰트:** JetBrains Mono (모노스페이스)

### 모달 시스템

```typescript
// 모달 열기
const { openModal } = useModal();
openModal('idea', { id: 'idea-123', title: 'My Idea' });

// 모달 타입
type ModalType = 'signal' | 'trend' | 'idea' | 'debate' | 'plan' | 'agent' | 'stats' | 'pipeline';
```

### 다국어 지원 (i18n)

```typescript
// UI 라벨 번역
const { t, locale, setLanguage } = useI18n();
<span>{t('dashboard')}</span>

// 콘텐츠 로컬라이제이션 (아이디어, 트렌드, 플랜 등)
const getLocalizedText = (en: string | null, ko: string | null): string => {
  if (locale === 'ko' && ko) return ko;
  return en || '';
};
<h3>{getLocalizedText(idea.title, idea.title_ko)}</h3>

// 지원 언어: 'en', 'ko'
```

**양방향 번역 (ContentTranslator):**
- 콘텐츠 언어 자동 감지 (한글/영어)
- 한글 원본 → 영어 번역 (main field) + 한글 유지 (`*_ko` field)
- 영어 원본 → 영어 유지 (main field) + 한글 번역 (`*_ko` field)
- LLM: `llama3.3:70b` (로컬, 무료)

## 자주 발생하는 문제와 해결책

### 1. ERR_CONNECTION_REFUSED (API 연결 오류)

**원인:** 브라우저가 `localhost:3001`에 직접 연결 시도

**해결:**
```bash
# .env.local 확인
cat website/.env.local
# NEXT_PUBLIC_API_URL=/api 이어야 함

# 재빌드 및 재시작
cd website && npm run build
pm2 restart moss-ao-web
```

### 2. 토론이 데이터베이스에 저장되지 않음

**원인:** `debate_sessions.idea_id`가 NOT NULL로 설정됨

**해결:** 스키마 마이그레이션으로 nullable 변경 (이미 수정됨)

### 3. PM2 환경변수가 갱신되지 않음

**원인:** PM2가 환경변수를 캐시함

**해결:**
```bash
pm2 delete moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-web
pm2 save
```

### 4. 포트 충돌

**원인:** 이전 프로세스가 포트 점유

**해결:**
```bash
# 포트 사용 프로세스 확인
lsof -i :3000
lsof -i :3001

# 프로세스 종료
kill <PID>
```

### 5. 빌드 실패 (TypeScript 오류)

**해결:**
```bash
cd website
npm run build 2>&1 | head -50  # 오류 확인
# 타입 오류 수정 후 재빌드
```

### 6. Ollama 타임아웃 오류

**증상:** "Ollama timeout after 300s" 에러 발생

**원인:** 여러 에이전트가 동시에 Ollama 요청, 쓰로틀링 큐 대기 중 타임아웃

**해결:**
- `config.yaml`의 `throttling.ollama` 설정 조정:
  - `request_timeout: 600` (600초로 증가)
  - `requests_before_cooling: 10` (쿨링 전 더 많은 요청 허용)
  - `cooling_period_seconds: 60` (쿨링 시간 단축)
- `config.yaml`의 `debate.test_mode: true`로 에이전트 수 감소
- 사용 중인 Ollama 모델 확인: `curl http://localhost:11434/api/ps`

### 7. Ollama 모델 VRAM 메모리 부족

**증상:** 응답이 매우 느리거나 멈춤

**해결:**
```bash
# 사용하지 않는 모델 언로드
curl -s http://localhost:11434/api/generate -d '{"model": "phi4:14b", "keep_alive": 0}'
curl -s http://localhost:11434/api/generate -d '{"model": "qwen2.5:32b", "keep_alive": 0}'
```

## 콘텐츠 품질 요구사항

### 제목 요구사항 (모든 Trend, Idea, Plan)

- **최소 30자 이상** 구체적이고 설명적인 제목
- 일반적인 표현 대신 **구체적인 기술명, 프로젝트명, 수치** 포함

| 나쁜 예 | 좋은 예 |
|---------|---------|
| "AI 트렌드" | "OpenAI GPT-5 에이전트 SDK 출시로 자율 AI 워크플로우 자동화 시대 개막" |
| "DeFi 성장" | "Uniswap v4 훅스 도입으로 맞춤형 DEX 전략 가능" |
| "NFT 플랫폼" | "Mossland NFT 홀더를 위한 실시간 메타버스 자산 가치 트래커" |

### 아이디어 필수 섹션

토론에서 생성되는 아이디어는 다음 섹션을 반드시 포함:

1. **핵심 분석** (100자+) - 시장/기술 상황 분석
2. **기회/리스크** (150자+) - 정량적 데이터, 경쟁 서비스 차별점
3. **구체적 제안** (200자+) - 핵심 기능 3-5개, 기술 스택, MVP 범위
4. **실행 로드맵** (100자+) - 주차별 일정, 필요 리소스
5. **성공 지표** - 측정 가능한 KPI 2-3개 (목표 수치 포함)

### 기획안 필수 섹션

플랜 생성 시 다음 섹션 포함:

1. **프로젝트 개요** - 이름, 한 줄 설명, 목표, 대상 사용자, 예상 기간/비용
2. **기술 아키텍처** - 프론트엔드, 백엔드, DB, 블록체인 연동, 외부 API
3. **상세 실행 계획** - 주차별 Task 및 마일스톤
4. **리스크 관리** - 리스크 테이블 (발생 확률, 영향도, 대응 방안)
5. **성과 지표 (KPI)** - 지표, 목표, 측정 방법, 측정 주기
6. **향후 확장 계획** - Phase 2 기능, 장기 비전

## 아이디어 생성 파이프라인

자세한 내용은 `docs/pipeline.md` 참조.

### 파이프라인 개요

```
Signals (30분) → Trends (2시간) → Debate (6시간) → Ideas → Auto-Score → Plans
                      ↓                 ↑                                  ↓
                 (트렌드 기반 토픽)                               Projects (score ≥ 8.0)
```

### 아이디어 소스 유형

| 소스 | 설명 | LLM |
|------|------|-----|
| `trend_based` | 트렌드 분석 기반 생성 | Claude API |
| `debate` | 멀티에이전트 토론에서 생성 | Ollama (로컬) |
| `github_sync` | GitHub Issues에서 동기화 | - |

### 자동 점수화 및 프로젝트 생성 시스템

토론 완료 후 아이디어 자동 점수화:
- **score >= 8.0**: `promoted` → 플랜 자동 생성 + **프로젝트 자동 생성**
- **score 7.0-8.0**: `promoted` → 플랜 자동 생성 (프로젝트는 수동 버튼)
- **score 4.0-7.0**: `scored` → 백로그 대기
- **score < 4.0**: `archived` → 아카이브

## 토론 시스템 (Multi-Stage Debate)

### 3단계 프로세스

1. **Divergence (발산)** - 16명의 에이전트가 아이디어 생성
2. **Convergence (수렴)** - 8명의 분석가가 아이디어 평가/병합
3. **Planning (기획)** - 10명의 기획자가 실행 계획 작성

### 에이전트 페르소나

- **발산 에이전트:** 창업가, 개발자, 마케터, 디자이너 등
- **수렴 에이전트:** VC, 시장 분석가, 기술 전문가 등
- **기획 에이전트:** PM, 테크 리드, QA 리드, DevRel 등

### 스케줄

| 작업 | 주기 | 설명 |
|------|------|------|
| Signal Collection | 30분마다 | RSS/API에서 신호 수집 |
| Trend Analysis | 2시간마다 | 신호 분석 → 트렌드 생성 (Ollama) |
| Debate | 6시간마다 | 트렌드 기반 토론 → 아이디어/플랜 자동 생성 |
| Backlog | 4시간마다 | 처리 상태 집계/리포트 |
| Health Check | 5분마다 | 시스템 상태 확인 |

## 개발 규칙

### 문서 업데이트 규칙

**중요:** 개발이 어느 정도 진척될 때마다 (기능 추가, 버그 수정, 구조 변경 등) 다음 MD 파일들을 업데이트하고 커밋해야 합니다:

1. **CLAUDE.md** - 프로젝트 구조, API 엔드포인트, 새로운 기능 반영
2. **CHANGELOG.md / CHANGELOG.ko.md** - 변경 이력 추가
3. **docs/pipeline.md** - 파이프라인 관련 변경 시
4. **README.md / README.ko.md** - 주요 기능 변경 시

```bash
# 문서 업데이트 후 커밋
git add *.md docs/*.md
git commit -m "docs: update documentation for recent changes"
```

### 커밋 컨벤션

- `feat:` - 새로운 기능
- `fix:` - 버그 수정
- `docs:` - 문서 변경
- `refactor:` - 코드 리팩토링
- `style:` - UI/UX 변경
- `chore:` - 기타 변경

## Plan → Project 자동 생성

**상태:** ✅ 구현 완료 (v0.6.3: Production-Quality Code Generation)

승인된 Plan을 `projects/` 폴더에 실제 프로덕션 품질의 프로젝트로 변환하는 기능:

```
Plan (DB) → Deep LLM 파싱 → 엔티티/서비스 추출 → LLM 코드 생성 → projects/{project-name}/
```

### 향상된 Plan 파서 (v0.6.3)

- **Deep LLM Parsing**: 마크다운에서 상세 정보 추출
- **DataEntity**: 데이터 모델 및 관계 정의
- **ExternalService**: Twitter API, Coingecko, Etherscan 등 외부 서비스 감지
- **UIComponent**: 프론트엔드 컴포넌트 및 페이지 추출
- **SmartContractSpec**: 블록체인 스마트 컨트랙트 사양

### 프로덕션 품질 코드 생성 (v0.6.3)

생성되는 코드:
- **완전한 FastAPI/Express 백엔드**: 비즈니스 로직, 라우터, 모델 포함
- **완전한 Next.js/React 프론트엔드**: 모든 페이지와 컴포넌트 포함
- **Solidity 스마트 컨트랙트**: Hardhat 테스트 프레임워크 포함
- **외부 서비스 연동 레이어**: API 클라이언트, 웹소켓 핸들러
- **데이터베이스 스키마 및 마이그레이션**
- **Docker 설정**

### 트리거 전략

- **자동 생성 (score ≥ 8.0)**: 토론 완료 후 Plan이 자동 승인되고 프로젝트 생성
- **수동 승인 (score < 8.0)**: Plan이 "draft" 상태로 생성됨
  - `POST /plans/{id}/approve` API로 수동 승인
  - 승인 시 `generate_project=true` 옵션으로 즉시 프로젝트 생성 가능
  - `GET /plans/pending-approval` API로 승인 대기 목록 조회

### 지원 기술 스택

| 프론트엔드 | 백엔드 | 블록체인 |
|------------|--------|----------|
| Next.js + TypeScript | FastAPI + SQLAlchemy | Hardhat (Ethereum) |
| React (Vite) | Express.js + TypeScript | Anchor (Solana) |
| Vue 3 | | |

### 작업별 LLM 모델

| 작업 | 모델 | 용도 |
|------|------|------|
| Plan 파싱 | `glm-4.7-flash` | 마크다운 → 구조화된 데이터 |
| 코드 생성 | `qwen2.5:32b` | 컴포넌트, API, 모델 생성 |
| 아키텍처 설계 | `llama3.3:70b` | 복잡한 시스템 설계 |
| 경량/폴백 | `phi4:14b` | 간단한 파일, 설정 |

### 생성되는 프로젝트 구조

```
projects/{project-name}/
├── README.md              # LLM 생성 (Plan 기반)
├── PLAN.md                # 원본 Plan 문서
├── .moss-project.json     # 메타데이터
├── src/
│   ├── frontend/          # Next.js (해당 시)
│   └── backend/           # FastAPI (해당 시)
├── contracts/             # Solidity (해당 시)
├── docs/
│   └── api.md
└── tests/
```

### 설정 (`config.yaml`)

```yaml
project:
  auto_generate:
    enabled: true
    min_score: 8.0        # 자동 생성 최소 점수
    max_concurrent: 1     # 동시 생성 제한
  llm:
    parsing: "glm-4.7-flash"
    code_generation: "qwen2.5:32b"
    architecture: "llama3.3:70b"
    fallback: "phi4:14b"
  output_dir: "projects"
```

## 향후 구현 예정 기능

### GitHub 라벨 기반 승격 워크플로우

**상태:** 구현 예정

GitHub Issues에서 라벨을 추가하면 자동으로 처리:

- `promote:to-plan`: Idea → Plan 자동 생성
- `promote:to-dev`: Plan → Project 스캐폴드 생성

자세한 내용: `docs/labels.md`

## 참고 링크

- **프로젝트 문서:** `docs/` 디렉토리
- **API 문서:** http://localhost:3001/docs (Swagger UI)
- **실제 IP 주소:** `CLAUDE.local.md` (gitignore 처리됨)
- **민감한 정보:** `.env.local` 파일에 저장
