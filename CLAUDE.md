# MOSS.AO - Claude Code 참조 문서

이 문서는 Claude Code가 프로젝트 작업 시 참조할 수 있는 정보를 담고 있습니다.

## 프로젝트 개요

**MOSS.AO (Mossland Agentic Orchestrator)**는 AI 에이전트들이 토론을 통해 아이디어를 생성하고 기획안을 작성하는 멀티에이전트 오케스트레이션 시스템입니다.

- **공개 URL:** https://ao.moss.land
- **GitHub:** https://github.com/MosslandOpenDevs/agentic-orchestrator

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
│   ├── scheduler/               # PM2 스케줄 작업
│   │   ├── __main__.py          # CLI 엔트리포인트
│   │   └── tasks.py             # 작업 구현 (signal, debate, backlog)
│   └── signals/                 # 신호 수집기
│       ├── aggregator.py        # 신호 수집 조율
│       └── adapters/            # RSS, GitHub, OnChain 어댑터
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
| GET | `/trends` | 분석된 트렌드 |
| GET | `/ideas` | 아이디어 백로그 |
| GET | `/ideas/{id}` | 아이디어 상세 |
| GET | `/debates` | 토론 세션 목록 |
| GET | `/debates/{id}` | 토론 상세 (메시지 포함) |
| GET | `/plans` | 기획 문서 목록 |
| GET | `/plans/{id}` | 기획 문서 상세 |
| GET | `/agents` | 에이전트 목록 |
| GET | `/usage` | API 사용량 통계 |
| GET | `/activity` | 최근 활동 로그 |

## 데이터베이스 스키마

**위치:** `data/orchestrator.db` (SQLite)

### 주요 테이블

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| `signals` | 수집된 신호 | source, category, title, score, sentiment |
| `trends` | 분석된 트렌드 | name, score, period, keywords |
| `ideas` | 생성된 아이디어 | title, summary, status, score |
| `debate_sessions` | 토론 세션 | topic, phase, status, participants |
| `debate_messages` | 토론 메시지 | agent_id, agent_name, message_type, content |
| `plans` | 기획 문서 | title, status, prd_content, final_plan |
| `api_usage` | API 사용량 | provider, model, cost_usd, request_count |

### 중요 스키마 노트

- **`debate_sessions.idea_id`**: `nullable=True` (독립 토론 지원)
- **`ideas.score`**: 토론 중 에이전트들이 부여한 평균 점수

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
moss-ao-debate   # 토론 스케줄러 (6시간마다, cron)
moss-ao-signals  # 신호 수집기 (30분마다, cron)
moss-ao-health   # 헬스체크 (5분마다, cron)
moss-ao-backlog  # 백로그 처리 (매일 자정, cron)

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
// 사용법
const { t, language, setLanguage } = useI18n();
<span>{t('dashboard')}</span>

// 지원 언어: 'en', 'ko'
```

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

## 아이디어 생성 파이프라인

자세한 내용은 `docs/pipeline.md` 참조.

### 파이프라인 개요

```
Signals (30분) → Trends (2시간) → Debate (6시간) → Ideas → Auto-Score → Plans
                      ↓                 ↑
                 (트렌드 기반 토픽)
```

### 아이디어 소스 유형

| 소스 | 설명 | LLM |
|------|------|-----|
| `trend_based` | 트렌드 분석 기반 생성 | Claude API |
| `debate` | 멀티에이전트 토론에서 생성 | Ollama (로컬) |
| `github_sync` | GitHub Issues에서 동기화 | - |

### 자동 점수화 시스템

토론 완료 후 아이디어 자동 점수화:
- **score >= 7.0**: `promoted` → 플랜 자동 생성
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

## 참고 링크

- **프로젝트 문서:** `docs/` 디렉토리
- **API 문서:** http://localhost:3001/docs (Swagger UI)
- **실제 IP 주소:** `CLAUDE.local.md` (gitignore 처리됨)
- **민감한 정보:** `.env.local` 파일에 저장
