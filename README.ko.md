# Mossland Agentic Orchestrator

**한국어** | [English](README.md)

모스랜드 생태계를 위한 마이크로 Web3 서비스를 발굴, 기획, 구현하는 자율 멀티 에이전트 오케스트레이션 시스템입니다.

**버전**: v0.5.1 "Bilingual"

## 주요 기능

- **멀티 스테이지 토론**: 34개 AI 에이전트가 3단계(발산 → 수렴 → 기획)를 거쳐 토론
- **다양한 시그널 소스**: RSS, GitHub Events, 온체인 데이터, 소셜 미디어, News API
- **하이브리드 LLM 라우팅**: 로컬 Ollama 모델 + 클라우드 API 폴백 지능형 라우팅
- **휴먼 인 더 루프**: 라벨 프로모션을 통해 개발할 아이디어를 사람이 선택
- **PM2 스케줄링**: PM2를 통한 자동화된 작업 스케줄링 (시그널, 토론, 백로그, 헬스체크)
- **CLI 스타일 대시보드**: https://ao.moss.land 레트로 터미널 테마 웹 인터페이스
- **REST API**: 프로그래밍 방식 접근을 위한 FastAPI 백엔드

## 대시보드

오케스트레이터를 실시간으로 모니터링하는 Next.js 기반 CLI 스타일 대시보드입니다.

**URL**: https://ao.moss.land

### 페이지

| 페이지 | 설명 |
|--------|------|
| `/` | 파이프라인, 활동 피드, 통계가 있는 대시보드 |
| `/trends` | 시그널 소스에서 수집한 트렌드 분석 결과 |
| `/backlog` | GitHub 링크가 있는 아이디어 및 계획 백로그 |
| `/system` | 시스템 아키텍처 및 멀티 에이전트 토론 시각화 |
| `/agents` | 3개 토론 단계의 34개 AI 에이전트 페르소나 |

### 로컬 실행

```bash
cd website
pnpm install
pnpm dev
```

http://localhost:3000 에서 대시보드를 확인할 수 있습니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           시그널 수집                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │   RSS   │ │ GitHub  │ │ 온체인  │ │ 소셜    │ │News API │           │
│  │ 어댑터  │ │ Events  │ │ 어댑터  │ │ 미디어  │ │ 어댑터  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┼───────────┴───────────┘                 │
│                               ▼                                          │
│                    ┌──────────────────┐                                  │
│                    │ 시그널 집계기     │                                  │
│                    │   + 스코어러     │                                  │
│                    └────────┬─────────┘                                  │
├─────────────────────────────┼───────────────────────────────────────────┤
│                             ▼                                            │
│                  멀티 스테이지 토론 (34 에이전트)                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ 1단계: 발산 (12 에이전트)                                        │     │
│  │   혁신가, 회의론자, 실용주의자, 비전가...                         │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ 2단계: 수렴 (12 에이전트)                                        │     │
│  │   통합자, 평가자, 우선순위 결정자, 리스크 평가자...               │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ 3단계: 기획 (10 에이전트)                                        │     │
│  │   아키텍트, 프로젝트 매니저, 테크니컬 리드...                     │     │
│  └────────────────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────────┤
│                        하이브리드 LLM 라우터                              │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │   로컬 (Ollama)     │ ←→  │   클라우드 API      │                    │
│  │   - Qwen 32B        │     │   - Claude          │                    │
│  │   - Llama 3         │     │   - GPT-4           │                    │
│  │   - Mistral         │     │   - Gemini          │                    │
│  └─────────────────────┘     └─────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 빠른 시작

### 1. 설치

```bash
# 클론 및 설치
git clone https://github.com/MosslandOpenDevs/agentic-orchestrator.git
cd agentic-orchestrator

# Python 가상환경 생성 (Python 3.12 필요)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install uvicorn fastapi pyyaml

# 환경 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. PM2로 서비스 시작

```bash
# PM2 전역 설치
npm install -g pm2

# 모든 서비스 시작
pm2 start ecosystem.config.js

# 또는 특정 서비스만 시작
pm2 start ecosystem.config.js --only moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-api
```

### 3. 대시보드 접속

- **웹 대시보드**: http://localhost:3000
- **API 문서**: http://localhost:3001/docs

## PM2 서비스

| 서비스 | 스케줄 | 설명 |
|--------|--------|------|
| `moss-ao-signals` | 30분마다 | 모든 어댑터에서 시그널 수집 |
| `moss-ao-debate` | 6시간마다 | 멀티 스테이지 AI 토론 실행 |
| `moss-ao-backlog` | 매일 자정 | 대기 중인 백로그 항목 처리 |
| `moss-ao-web` | 항시 실행 | Next.js 대시보드 (포트 3000) |
| `moss-ao-api` | 항시 실행 | FastAPI 백엔드 (포트 3001) |
| `moss-ao-health` | 5분마다 | 시스템 헬스 모니터링 |

### PM2 명령어

```bash
# 모든 서비스 보기
pm2 status

# 로그 보기
pm2 logs moss-ao-web
pm2 logs moss-ao-api

# 서비스 재시작
pm2 restart moss-ao-web

# 모든 서비스 중지
pm2 stop all

# 리소스 모니터링
pm2 monit
```

## API 엔드포인트

FastAPI 백엔드는 REST API 접근을 제공합니다:

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/health` | GET | 헬스 체크 |
| `/status` | GET | 시스템 상태 |
| `/signals` | GET | 최근 시그널 목록 |
| `/debates` | GET | 토론 결과 목록 |
| `/agents` | GET | 에이전트 페르소나 목록 |
| `/docs` | GET | Swagger 문서 |

## 멀티 스테이지 토론 시스템

### 1단계: 발산 (12 에이전트)
다양한 아이디어와 관점 생성:
- **혁신가**: 창의적 혁신 아이디어
- **회의론자**: 비판적 분석 및 리스크 식별
- **실용주의자**: 실용적 구현 중심
- **비전가**: 장기 전략적 사고
- 외 8개 특화 에이전트...

### 2단계: 수렴 (12 에이전트)
아이디어 통합 및 평가:
- **통합자**: 관련 아이디어 결합
- **평가자**: 제안 점수화 및 순위 매김
- **우선순위 결정자**: 실행 순서 결정
- **리스크 평가자**: 잠재적 문제 식별
- 외 8개 특화 에이전트...

### 3단계: 기획 (10 에이전트)
실행 가능한 구현 계획 생성:
- **아키텍트**: 시스템 설계
- **프로젝트 매니저**: 태스크 분해
- **테크니컬 리드**: 기술 결정
- **리소스 기획자**: 리소스 배분
- 외 6개 특화 에이전트...

### 에이전트 성격 시스템

각 에이전트는 4축 성격 프로필을 가집니다:
- **창의성**: 혁신 vs. 관습 (0-10)
- **분석력**: 데이터 중심 vs. 직관 (0-10)
- **리스크 허용도**: 공격적 vs. 보수적 (0-10)
- **협업**: 팀 중심 vs. 독립적 (0-10)

## 시그널 소스

### RSS 피드
5개 카테고리의 17개 피드:
- **AI**: OpenAI, Google AI, arXiv, TechCrunch, Hacker News
- **Crypto**: CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate
- **Finance**: CNBC Finance
- **Security**: The Hacker News, Krebs on Security
- **Dev**: The Verge, Ars Technica, Stack Overflow Blog

### GitHub Events
- 저장소 활동 추적
- 트렌딩 프로젝트 모니터링
- 이슈 및 PR 분석

### 온체인 데이터
- MOC 토큰 트랜잭션
- 스마트 컨트랙트 이벤트
- DeFi 프로토콜 메트릭

### 소셜 미디어
- X (트위터) 멘션
- 커뮤니티 감성 분석

### News API
- 실시간 뉴스 집계
- 키워드 기반 필터링

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **예** |
| `GITHUB_OWNER` | 저장소 소유자 | **예** |
| `GITHUB_REPO` | 저장소 이름 | **예** |
| `ANTHROPIC_API_KEY` | Claude API 키 | 클라우드 모드용 |
| `OPENAI_API_KEY` | OpenAI API 키 | 클라우드 모드용 |
| `GEMINI_API_KEY` | Gemini API 키 | 클라우드 모드용 |
| `OLLAMA_HOST` | Ollama 서버 URL | 로컬 모드용 |

## 프로젝트 구조

```
agentic-orchestrator/
├── ecosystem.config.js      # PM2 설정
├── .venv/                   # Python 가상환경
├── src/agentic_orchestrator/
│   ├── adapters/            # 시그널 소스 어댑터
│   │   ├── rss.py
│   │   ├── github_events.py
│   │   ├── onchain.py
│   │   ├── social_media.py
│   │   └── news_api.py
│   ├── api/                 # FastAPI 백엔드
│   │   └── main.py
│   ├── cache/               # 캐싱 레이어
│   ├── db/                  # 데이터베이스 모델 & 레포지토리
│   ├── debate/              # 멀티 스테이지 토론 시스템
│   │   ├── protocol.py
│   │   └── multi_stage.py
│   ├── llm/                 # LLM 라우팅
│   │   └── router.py
│   ├── personas/            # 34개 에이전트 정의
│   ├── providers/           # LLM 프로바이더 (Ollama, APIs)
│   ├── scheduler/           # PM2 태스크 구현
│   │   ├── __main__.py
│   │   └── tasks.py
│   └── signals/             # 시그널 처리
├── website/                 # Next.js 대시보드
│   ├── src/
│   │   ├── app/             # 페이지
│   │   └── components/      # React 컴포넌트
│   └── package.json
└── logs/                    # PM2 로그 파일
```

## 개발

### 테스트 실행

```bash
pytest tests/ -v
```

### 웹사이트 빌드

```bash
cd website
pnpm build
```

### 수동 태스크 실행

```bash
# 시그널 수집
python -m agentic_orchestrator.scheduler signal-collect

# 토론 실행
python -m agentic_orchestrator.scheduler run-debate

# 백로그 처리
python -m agentic_orchestrator.scheduler process-backlog

# 헬스 체크
python -m agentic_orchestrator.scheduler health-check
```

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

---

*모스랜드 생태계를 위해 구축됨 - 사람이 가이드하고, AI가 구동하는 혁신.*

*v0.5.1 "Bilingual" - 이중 언어 콘텐츠 지원과 멀티 에이전트 오케스트레이션*
