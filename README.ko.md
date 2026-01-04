# Mossland Agentic Orchestrator

**한국어** | [English](README.md)

모스랜드 생태계를 위한 마이크로 Web3 서비스를 발굴, 기획, 구현하는 자율 오케스트레이션 시스템입니다.

## 주요 기능

- **백로그 기반 워크플로우**: 아이디어와 계획을 GitHub Issues로 관리
- **휴먼 인 더 루프**: 라벨 프로모션을 통해 개발할 아이디어를 사람이 선택
- **멀티 에이전트 토론**: 4개 AI 역할(창업자, VC, Accelerator, 창업가 친구)간 토론으로 계획 정제
- **트렌드 기반 아이디어**: RSS 피드를 통해 현재 뉴스 트렌드에서 아이디어 생성
- **자율 생성**: 오케스트레이터가 지속적으로 아이디어를 생성하고 프로모션을 처리
- **자동 진행 없음**: 단계가 자동으로 진행되지 않음 - 무엇을 만들지 사람이 결정

## 작동 방식

```
┌─────────────────────────────────────────────────────────────────┐
│                    아이디어 백로그 (GitHub Issues)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  오케스트레이터가 아이디어 생성 → Issues로 저장           │  │
│  │  라벨: type:idea, status:backlog                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│              사람이 라벨 추가: promote:to-plan                  │
│                             ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                    계획 백로그 (GitHub Issues)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  오케스트레이터가 프로모션된 아이디어로 상세 계획 생성    │  │
│  │  라벨: type:plan, status:backlog                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│              사람이 라벨 추가: promote:to-dev                   │
│                             ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                    개발 (Repository)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  오케스트레이터가 프로젝트 스캐폴드 생성                  │  │
│  │  디렉토리: projects/<project_id>/                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 빠른 시작

### 1. 설치

```bash
# 클론 및 설치
git clone https://github.com/mossland/agentic-orchestrator.git
cd agentic-orchestrator
python -m venv venv
source venv/bin/activate
pip install -e .

# 환경 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. 라벨 설정

```bash
ao backlog setup
```

GitHub 저장소에 필요한 모든 라벨을 생성합니다.

### 3. 아이디어 생성

```bash
# 새 아이디어 2개 생성
ao backlog generate --count 2
```

아이디어가 `type:idea` 및 `status:backlog` 라벨과 함께 GitHub Issues로 나타납니다.

### 4. 아이디어 프로모션 (사람이 수행)

GitHub에서:
1. 아이디어 이슈로 이동
2. `promote:to-plan` 라벨 추가

### 5. 프로모션 처리

```bash
ao backlog process
```

오케스트레이터가 다음을 수행합니다:
- `promote:to-plan` 라벨이 있는 이슈 찾기
- 상세 기획 문서 생성
- 새로운 `type:plan` 이슈 생성
- 원본 아이디어에 `status:planned` 업데이트

### 6. 개발 시작 (사람이 수행)

GitHub에서:
1. 계획 이슈로 이동
2. `promote:to-dev` 라벨 추가

그런 다음 실행:
```bash
ao backlog process
```

오케스트레이터가 `projects/<id>/`에 프로젝트 스캐폴드를 생성합니다.

## CLI 명령어

### 백로그 명령어 (권장)

```bash
# 전체 사이클 실행: 아이디어 생성 + 프로모션 처리
ao backlog run

# 트렌드 분석 포함 실행 (전통적 1개 + 트렌드 기반 2개)
ao backlog run --ideas 1 --trend-ideas 2 --analyze-trends

# 전통적 아이디어만 생성
ao backlog generate --count 2

# 트렌드 기반 아이디어 생성
ao backlog generate-trends --count 2

# 트렌드 분석만 실행 (아이디어 생성 없음)
ao backlog analyze-trends

# 프로모션만 처리 (아이디어 생성 없음)
ao backlog process

# 백로그 상태 확인
ao backlog status

# 트렌드 분석 이력 확인
ao backlog trends-status

# 저장소에 라벨 설정
ao backlog setup
```

### 옵션

```bash
# 드라이 런 (실제 변경 없음)
ao backlog run --dry-run

# 특정 개수의 전통적 아이디어 생성
ao backlog run --ideas 3

# 트렌드 기반 아이디어 생성
ao backlog run --trend-ideas 2 --analyze-trends

# 아이디어 생성 건너뛰기
ao backlog run --no-ideas

# 처리할 프로모션 제한
ao backlog run --max-promotions 3
```

## 프로모션 워크플로우

### 아이디어를 계획으로 프로모션

1. GitHub Issues에서 개발하고 싶은 **아이디어 찾기**
2. `promote:to-plan` **라벨 추가**
3. 오케스트레이터 실행 **대기** (또는 `ao backlog process` 실행)
4. **결과**: 상세 PRD, 아키텍처, 태스크가 포함된 새 `[PLAN]` 이슈 생성

### 계획을 개발로 프로모션

1. 계획 이슈를 **검토**하고 준비되었는지 확인
2. `promote:to-dev` **라벨 추가**
3. 오케스트레이터 실행 **대기** (또는 `ao backlog process` 실행)
4. **결과**: `projects/<id>/`에 프로젝트 스캐폴드 생성

### 계획 거부

생성된 계획이 만족스럽지 않은 경우:
1. 계획 이슈에 `reject:plan` **라벨 추가**
2. 오케스트레이터 실행 **대기** (또는 `ao backlog process` 실행)
3. **결과**: 계획이 닫히고, 원본 아이디어에 `promote:to-plan`이 복원되어 재생성

또는 CLI 사용:
```bash
ao backlog reject 123  # 계획 이슈 #123 거부
```

## 멀티 에이전트 토론 시스템

3개의 AI 프로바이더(Claude, ChatGPT, Gemini)가 모두 사용 가능할 때, 토론 과정을 통해 계획이 생성됩니다:

### 토론 역할

| 역할 | 관점 | 프로바이더 순환 |
|------|------|-----------------|
| **창업자** | 비전, 확신, 실행 | 매 라운드 순환 |
| **VC** | 시장, 투자, 확장성 | 매 라운드 순환 |
| **Accelerator** | 실행, 검증, MVP | 매 라운드 순환 |
| **창업가 친구** | 동료 지원, 창의적 아이디어 | 창업자와 동일 |

### 토론 흐름

```
라운드 1-5 (또는 "충분히 개선됨"까지):
  1. 창업자가 계획 제시/업데이트
  2. VC가 시장/투자 피드백 제공
  3. Accelerator가 실행 피드백 제공
  4. 창업가 친구가 동료 관점 제공
  5. 창업자가 피드백 반영, 채택/거부 결정, 계획 업데이트
  6. 종료 조건 확인
```

### 출력

- **PLAN Issue**: 최종 정제된 계획 포함
- **토론 기록**: 전체 토론 히스토리가 접기/펼치기 가능한 댓글로 저장
- **이중 언어**: 모든 콘텐츠가 영어 + 한국어 번역으로 제공

## 라벨

| 라벨 | 용도 | 추가하는 주체 |
|------|------|---------------|
| `promote:to-plan` | **아이디어를 계획으로 프로모션** | 사람 |
| `promote:to-dev` | **개발 시작** | 사람 |
| `reject:plan` | **계획 거부 및 재생성** | 사람 |
| `type:idea` | 아이디어 이슈 표시 | 오케스트레이터 |
| `type:plan` | 계획 이슈 표시 | 오케스트레이터 |
| `status:backlog` | 백로그에 있음 | 오케스트레이터 |
| `status:planned` | 아이디어가 계획됨 | 오케스트레이터 |
| `status:in-dev` | 개발 중 | 오케스트레이터 |
| `source:trend` | 트렌드 분석에서 생성된 아이디어 | 오케스트레이터 |

전체 라벨 문서는 [docs/labels.md](docs/labels.md)를 참조하세요.

## 스케줄 실행

### GitHub Actions (권장)

포함된 워크플로우가 매일 오전 8시 KST에 오케스트레이터를 실행합니다:

```yaml
# .github/workflows/backlog.yml
on:
  schedule:
    - cron: '0 23 * * *'  # 매일 오전 8시 KST (23:00 UTC)
```

기본 일일 실행:
- 전통적 모스랜드 중심 아이디어 1개
- RSS 피드 기반 트렌드 아이디어 2개

### Cron Job

```bash
# 매일 오전 8시 KST (23:00 UTC) 실행
0 23 * * * cd /path/to/repo && /path/to/venv/bin/ao backlog run --ideas 1 --trend-ideas 2 --analyze-trends >> logs/cron.log 2>&1
```

### 트렌드 기반 아이디어 생성

오케스트레이터는 5개 카테고리의 17개 RSS 피드에서 기사를 수집합니다:
- **AI**: OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News
- **Crypto**: CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate
- **Finance**: CNBC Finance
- **Security**: The Hacker News, Krebs on Security
- **Dev**: The Verge, Ars Technica, Stack Overflow Blog

트렌드 분석 결과는 `data/trends/YYYY/MM/YYYY-MM-DD.md`에 저장됩니다.

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **예** |
| `GITHUB_OWNER` | 저장소 소유자 | **예** |
| `GITHUB_REPO` | 저장소 이름 | **예** |
| `ANTHROPIC_API_KEY` | Claude API 키 | API 모드용 |
| `OPENAI_API_KEY` | OpenAI API 키 | 리뷰용 |
| `GEMINI_API_KEY` | Gemini API 키 | 리뷰용 |
| `DRY_RUN` | 변경 없이 실행 | 아니오 |

### GitHub 토큰 권한

필요한 스코프:
- `repo` - 전체 저장소 접근 (Issues 및 Labels용)

## 오류 처리

### Rate Limiting (Claude)

- 자동으로 rate limit 리셋 대기
- 최대 재시도 및 대기 시간 설정 가능
- 모든 재시도 시도 로깅

### Quota Exhaustion (OpenAI/Gemini)

- `alerts/quota.md`에 알림 생성
- 프로바이더, 모델, 스테이지, 오류 로깅
- 해결 단계 제공
- 무한 루프 없음

### 동시성 제어

- 락 파일로 동시 실행 방지
- cron/스케줄 실행에 안전

## 프로젝트 구조

```
agentic-orchestrator/
├── .agent/
│   └── orchestrator.lock    # 동시성 락
├── .github/
│   ├── ISSUE_TEMPLATE/      # 아이디어 및 계획 템플릿
│   └── workflows/           # CI 및 스케줄러
├── alerts/                  # 오류/할당량 알림
├── data/
│   └── trends/              # 트렌드 분석 저장소
│       └── YYYY/MM/         # 일별 분석 파일
├── docs/
│   └── labels.md            # 라벨 문서
├── projects/
│   └── <project_id>/        # 생성된 프로젝트
│       ├── 01_ideation/
│       ├── 02_planning/
│       ├── 03_implementation/
│       └── 04_quality/
├── prompts/                 # 프롬프트 템플릿
├── src/
│   └── agentic_orchestrator/
│       ├── backlog.py       # 백로그 워크플로우
│       ├── cli.py           # CLI 명령어
│       ├── github_client.py # GitHub API
│       ├── orchestrator.py  # 레거시 오케스트레이터
│       ├── providers/       # LLM 어댑터
│       ├── trends/          # 트렌드 분석 모듈
│       ├── debate/          # 멀티 에이전트 토론 시스템
│       └── utils/           # 유틸리티
└── tests/
```

## 아이디어 생성

### 전통적 아이디어 (모스랜드 중심)
- **마이크로 Web3 서비스** - 1-2주 내 달성 가능한 작은 규모
- **MOC 토큰 유틸리티** - 토큰 가치 및 사용성 향상
- **생태계 이점** - 모스랜드 커뮤니티 지원
- **실용적 범위** - 대규모 플랫폼 개발 지양

### 트렌드 기반 아이디어
- **현재 트렌드** - RSS 피드의 실시간 뉴스 기반
- **Web3 기회** - 트렌딩 토픽에 대한 블록체인 응용 식별
- **시의성** - 핫 토픽이 관련성 있을 때 활용
- **크로스 산업** - AI, 암호화폐, 보안, 개발 트렌드

예시:
- 토큰 분석 대시보드
- 커뮤니티 거버넌스 도구
- NFT 유틸리티 확장
- AI 에이전트 통합 (AI 트렌드 기반)
- DeFi 프로토콜 도구 (암호화폐 트렌드 기반)

## 개발

### 테스트 실행

```bash
pytest tests/ -v
```

### 새 기능 추가

1. 워크플로우 변경은 `src/agentic_orchestrator/backlog.py` 수정
2. `src/agentic_orchestrator/cli.py`에서 CLI 업데이트
3. `tests/`에 테스트 추가

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

---

*모스랜드 생태계를 위해 구축됨 - 사람이 가이드하고, AI가 구동하는 혁신.*
