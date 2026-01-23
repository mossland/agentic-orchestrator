# MOSS.AO - Claude Code 참조 문서

이 문서는 Claude Code가 프로젝트 작업 시 참조할 수 있는 정보를 담고 있습니다.

## 프로젝트 구조

```
agentic-orchestrator/
├── src/agentic_orchestrator/    # Python 백엔드
│   ├── api/                     # FastAPI 서버 (포트 3001)
│   ├── db/                      # SQLAlchemy 모델 & 리포지토리
│   ├── debate/                  # 멀티스테이지 토론 시스템
│   ├── llm/                     # LLM 라우터 (Ollama, Claude, OpenAI)
│   ├── personas/                # AI 에이전트 페르소나
│   ├── scheduler/               # PM2 스케줄 작업
│   └── signals/                 # 신호 수집기
├── website/                     # Next.js 프론트엔드 (포트 3000)
│   ├── src/app/                 # App Router 페이지
│   ├── src/components/          # React 컴포넌트
│   └── src/lib/                 # API 클라이언트, 타입, i18n
└── data/                        # SQLite DB, 트렌드 데이터
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
│              │   IP: <LIGHTSAIL_IP>    │                        │
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
│  │           IP: <DEV_SERVER_IP>               │                │
│  │  ┌─────────────────┐  ┌─────────────────┐   │                │
│  │  │ FastAPI Backend │  │ Next.js Frontend│   │                │
│  │  │   Port: 3001    │  │   Port: 3000    │   │                │
│  │  └─────────────────┘  └─────────────────┘   │                │
│  └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Nginx 프록시 설정

Lightsail 서버의 Nginx가 다음과 같이 프록시합니다:

| 경로 | 프록시 대상 | 설명 |
|------|------------|------|
| `/api/*` | `<DEV_SERVER_IP>:3001/` | API 백엔드 (FastAPI) |
| `/*` | `<DEV_SERVER_IP>:3000` | 프론트엔드 (Next.js) |

### Nginx 설정 예시

```nginx
server {
    listen 443 ssl http2;
    server_name ao.moss.land;

    ssl_certificate     /etc/letsencrypt/live/ao.moss.land/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ao.moss.land/privkey.pem;

    # API 먼저 (정확한 매칭)
    location ^~ /api/ {
        proxy_pass http://<DEV_SERVER_IP>:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 프론트엔드
    location / {
        proxy_pass http://<DEV_SERVER_IP>:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 환경 변수

### 웹사이트 (.env.local)

```bash
# 프로덕션: /api 사용 (Nginx 프록시 경유)
NEXT_PUBLIC_API_URL=/api

# 로컬 개발 시: 직접 백엔드 호출
# NEXT_PUBLIC_API_URL=http://localhost:3001
```

**중요:** `NEXT_PUBLIC_*` 변수는 빌드 시점에 포함되므로, 변경 후 반드시 `npm run build` 실행 필요.

## PM2 프로세스

```bash
# 상태 확인
pm2 status

# 주요 프로세스
moss-ao-web      # Next.js 프론트엔드 (포트 3000)
moss-ao-api      # FastAPI 백엔드 (포트 3001)
moss-ao-debate   # 토론 스케줄러 (6시간마다)
moss-ao-signals  # 신호 수집기 (30분마다)
moss-ao-health   # 헬스체크 (5분마다)
moss-ao-backlog  # 백로그 처리 (매일 자정)

# 재시작
pm2 restart moss-ao-web
pm2 restart moss-ao-api

# 로그 확인
pm2 logs moss-ao-api --lines 50
```

## 데이터베이스

- **위치:** `data/orchestrator.db` (SQLite)
- **주요 테이블:**
  - `signals` - 수집된 신호
  - `trends` - 분석된 트렌드
  - `ideas` - 생성된 아이디어
  - `debate_sessions` - 토론 세션
  - `debate_messages` - 토론 메시지
  - `plans` - 기획 문서
  - `api_usage` - API 사용량 추적

## 로컬 개발

```bash
# 백엔드 실행
cd /path/to/agentic-orchestrator
PYTHONPATH=./src .venv/bin/python -m uvicorn agentic_orchestrator.api.main:app --reload --port 3001

# 프론트엔드 실행
cd website
npm run dev

# 토론 수동 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate
```

## 참고사항

- 실제 IP 주소는 `CLAUDE.local.md` 파일에 있습니다 (gitignore 처리됨)
- 민감한 정보는 `.env.local` 파일에 저장하세요
- 변경 후 PM2 프로세스 재시작 필요: `pm2 restart <process-name>`
