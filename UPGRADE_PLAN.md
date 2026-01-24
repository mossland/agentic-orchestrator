# Agentic Orchestrator v0.4.0 업그레이드 계획

> 작성일: 2026-01-22
> 대상 버전: v0.3.0 → v0.4.0

---

> **✅ 구현 완료 (2026-01-24)**
>
> 이 문서에 기술된 대부분의 기능이 v0.4.0 ~ v0.5.1에서 구현 완료되었습니다.
> - 다중 신호 어댑터 (10개) ✅
> - 멀티에이전트 토론 시스템 (34 에이전트) ✅
> - CLI 스타일 웹 인터페이스 ✅
> - PM2 기반 상시 운영 ✅
> - SQLite 데이터베이스 ✅
> - 하이브리드 LLM 라우터 (로컬 + 클라우드) ✅
>
> 현재 상태는 [PROGRESS.md](./PROGRESS.md)를 참조하세요.

---

> **📌 보완 문서 안내**
>
> 이 문서는 기본 업그레이드 계획입니다. 아래 항목은 [UPGRADE_PLAN_SUPPLEMENT.md](./UPGRADE_PLAN_SUPPLEMENT.md)에서 상세히 다룹니다:
>
> 1. **웹사이트 디자인** - Vibe Labs (vibelabs.hashed.com) 스타일 참조
> 2. **다양한 페르소나 에이전트** - 성격 유형별 34명의 에이전트 정의
> 3. **데이터베이스 아키텍처** - PostgreSQL/SQLite + Redis 기반 장기 운영

---

## 목차

1. [현재 상태 분석](#1-현재-상태-분석)
2. [업그레이드 개요](#2-업그레이드-개요)
3. [Phase 1: 다중 신호 어댑터 시스템](#3-phase-1-다중-신호-어댑터-시스템)
4. [Phase 2: Local LLM 기반 다중 에이전트 토론 시스템](#4-phase-2-local-llm-기반-다중-에이전트-토론-시스템)
5. [Phase 3: 다양한 페르소나 에이전트 시스템](#5-phase-3-다양한-페르소나-에이전트-시스템)
6. [Phase 4: CLI 스타일 레트로 웹 인터페이스](#6-phase-4-cli-스타일-레트로-웹-인터페이스)
7. [Phase 5: PM2 기반 상시 운영 시스템](#7-phase-5-pm2-기반-상시-운영-시스템)
8. [기술 스택 및 아키텍처](#8-기술-스택-및-아키텍처)
9. [구현 일정](#9-구현-일정)
10. [리스크 및 대응 방안](#10-리스크-및-대응-방안)

---

## 1. 현재 상태 분석

### 1.1 기존 구현 현황

| 구성요소 | 현재 상태 | 설명 |
|---------|----------|------|
| **신호 수집** | RSS 피드만 (17개) | AI, Crypto, Finance, Security, Dev 카테고리 |
| **LLM 프로바이더** | 3개 (Claude, OpenAI, Gemini) | 모두 유료 API |
| **에이전트 역할** | 4개 (Founder, VC, Accelerator, Friend) | 고정된 역할, 외부 API만 사용 |
| **토론 시스템** | 단일 스레드, 5라운드 | 발산/수렴 없이 순차적 피드백 |
| **웹 인터페이스** | Next.js 대시보드 | 일반적인 UI, 모바일 미최적화 |
| **스케줄링** | GitHub Actions | 일일 1회 실행 |

### 1.2 기존 아키텍처

```
RSS Feeds (17개)
    ↓
TrendAnalyzer (Claude API)
    ↓
IdeaGenerator
    ↓
GitHub Issues [IDEA]
    ↓ (인간: promote:to-plan)
PlanGenerator (Debate: Claude only)
    ↓
GitHub Issues [PLAN]
```

### 1.3 개선이 필요한 영역

1. **신호 다양성 부족**: RSS만으로는 실시간 트렌드 및 온체인 신호 포착 불가
2. **비용 효율성**: 모든 작업에 유료 API 사용으로 비용 증가
3. **토론 깊이 부족**: 단순 순차 피드백, 진정한 발산/수렴 프로세스 없음
4. **페르소나 다양성**: 4개 고정 역할로 다각적 관점 부족
5. **UI/UX**: 일반적인 대시보드, 차별화 없음
6. **운영 안정성**: GitHub Actions 의존, 세밀한 스케줄 제어 어려움

---

## 2. 업그레이드 개요

### 2.1 핵심 목표

```
┌─────────────────────────────────────────────────────────────────┐
│                    v0.4.0 "Signal Storm"                        │
├─────────────────────────────────────────────────────────────────┤
│  🔊 다양한 신호 → 🧠 Local LLM 토론 → 💡 정제된 아이디어        │
│                                                                 │
│  • 20+ 신호 소스 (RSS, GitHub, 온체인, 소셜)                    │
│  • 5개 Local LLM + 2개 외부 API (비용 90% 절감)                 │
│  • 10+ 다양한 페르소나 에이전트                                 │
│  • 발산(3회) → 수렴(2회) 토론 사이클                            │
│  • 레트로 CLI 스타일 웹 인터페이스                              │
│  • PM2 기반 24/7 상시 운영                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 새로운 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │   RSS   │  │ GitHub  │  │OnChain  │  │ Social  │  │  News   │       │
│  │  Feeds  │  │ Events  │  │  Data   │  │  Media  │  │   API   │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       └────────────┴────────────┴────────────┴────────────┘            │
│                              ↓                                          │
│                    ┌─────────────────────┐                              │
│                    │   Signal Aggregator │                              │
│                    └─────────┬───────────┘                              │
└──────────────────────────────┼──────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      LOCAL LLM LAYER (Ollama)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    IDEA GENERATION (Local)                       │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │   │
│  │  │ phi4    │  │ qwen2.5 │  │ qwen2.5 │  │ llama3.2│              │   │
│  │  │  14b    │  │   14b   │  │   32b   │  │   3b    │              │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                               ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 DIVERGENCE DEBATE (3 Rounds)                     │   │
│  │                                                                  │   │
│  │   [Developer] ←→ [Designer] ←→ [Marketer] ←→ [Analyst]          │   │
│  │   [Engineer]  ←→ [Startup CEO] ←→ [User] ←→ [Investor]          │   │
│  │                                                                  │   │
│  │   llama3.3:70b (Moderator) orchestrates debate                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                               ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 CONVERGENCE DEBATE (2 Rounds)                    │   │
│  │                                                                  │   │
│  │   [VC] ←→ [Accelerator] ←→ [Founder] ←→ [Expert]                │   │
│  │                                                                  │   │
│  │   qwen2.5:32b (Evaluator) scores and filters                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL API LAYER (Critical Only)                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    FINAL REFINEMENT                              │   │
│  │                                                                  │   │
│  │   Claude Opus 4.5: Final plan generation & quality check         │   │
│  │   GPT-5.2: Technical architecture validation                     │   │
│  │                                                                  │   │
│  │   Usage Budget: $50/day max, ~$1,500/month                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                    │
│  │ GitHub  │  │  Plan   │  │ Project │  │  Web    │                    │
│  │ Issues  │  │  Docs   │  │Scaffold │  │Dashboard│                    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: 다중 신호 어댑터 시스템

### 3.1 신호 소스 카탈로그

#### 3.1.1 RSS 피드 어댑터 (기존 확장)

| 카테고리 | 현재 | 추가 예정 | 총계 |
|---------|------|----------|------|
| AI/ML | 5 | 5 | 10 |
| Crypto/Web3 | 5 | 10 | 15 |
| Finance | 1 | 4 | 5 |
| Security | 2 | 3 | 5 |
| Dev/Tech | 4 | 6 | 10 |
| **합계** | **17** | **28** | **45** |

**추가 RSS 소스**:
```yaml
ai_ml:
  - https://huggingface.co/blog/feed.xml
  - https://www.deepmind.com/blog/rss.xml
  - https://bair.berkeley.edu/blog/feed.xml
  - https://lilianweng.github.io/index.xml
  - https://newsletter.ruder.io/feed

crypto_web3:
  - https://research.paradigm.xyz/feed.xml
  - https://a16zcrypto.com/feed/
  - https://blog.ethereum.org/feed.xml
  - https://blog.chain.link/rss/
  - https://solana.com/news/rss.xml
  - https://near.org/blog/feed/
  - https://blog.cosmos.network/feed
  - https://polygon.technology/blog/feed
  - https://arbitrum.io/blog/rss.xml
  - https://blog.zksync.io/rss

finance:
  - https://www.bloomberg.com/feed/podcast/decrypted.xml
  - https://www.ft.com/tech?format=rss
  - https://feeds.a]reuters.com/reuters/businessNews
  - https://www.wsj.com/xml/rss/3_7014.xml

security:
  - https://blog.trailofbits.com/feed/
  - https://www.schneier.com/feed/atom/
  - https://nakedsecurity.sophos.com/feed/

dev_tech:
  - https://github.blog/feed/
  - https://engineering.fb.com/feed/
  - https://netflixtechblog.com/feed
  - https://blog.cloudflare.com/rss/
  - https://aws.amazon.com/blogs/aws/feed/
  - https://discord.com/blog/rss.xml
```

#### 3.1.2 GitHub 이벤트 어댑터 (신규)

```python
# src/agentic_orchestrator/adapters/github_events.py

class GitHubEventsAdapter:
    """
    GitHub 트렌드 및 이벤트 수집

    수집 대상:
    - Trending repositories (daily/weekly)
    - New releases in watched repos
    - Issue/PR activity in key projects
    - GitHub Discussions trends
    """

    WATCHED_REPOS = [
        # AI/ML
        "openai/openai-python",
        "langchain-ai/langchain",
        "huggingface/transformers",
        "anthropics/anthropic-sdk-python",

        # Web3/Crypto
        "ethereum/go-ethereum",
        "solana-labs/solana",
        "paradigmxyz/reth",
        "foundry-rs/foundry",
        "alloy-rs/alloy",
        "wevm/viem",
        "wagmi-dev/wagmi",

        # Infrastructure
        "vercel/next.js",
        "denoland/deno",
        "oven-sh/bun",

        # Mossland
        "mossland/*"
    ]

    TRENDING_TOPICS = [
        "web3", "defi", "nft", "ai-agents",
        "llm", "blockchain", "metaverse",
        "dao", "tokenomics"
    ]
```

**수집 데이터**:
```yaml
github_signals:
  trending:
    - repository: "owner/repo"
      stars_today: 500
      description: "..."
      language: "TypeScript"
      topics: ["web3", "defi"]

  releases:
    - repository: "ethereum/go-ethereum"
      version: "v1.15.0"
      release_notes: "..."
      published_at: "2026-01-22T10:00:00Z"

  discussions:
    - repository: "langchain-ai/langchain"
      title: "RFC: Agent memory system"
      participants: 45
      reactions: 120
```

#### 3.1.3 온체인 데이터 어댑터 (신규)

```python
# src/agentic_orchestrator/adapters/onchain.py

class OnChainAdapter:
    """
    Ethereum 및 MOC 토큰 온체인 데이터 수집

    데이터 소스:
    - Ethereum mainnet (via public RPC)
    - Polygon (MOC 관련)
    - Dune Analytics API
    - DefiLlama API
    - The Graph Protocol
    """

    ENDPOINTS = {
        "ethereum_rpc": "https://eth-mainnet.g.alchemy.com/v2/demo",
        "polygon_rpc": "https://polygon-rpc.com",
        "dune_api": "https://api.dune.com/api/v1",
        "defillama": "https://api.llama.fi",
        "thegraph": "https://api.thegraph.com/subgraphs/name/"
    }

    METRICS = [
        "moc_token_transfers",      # MOC 토큰 전송 활동
        "moc_holder_count",         # 홀더 수 변화
        "defi_tvl_changes",         # DeFi TVL 변동
        "nft_sales_volume",         # NFT 거래량
        "gas_price_trends",         # 가스비 트렌드
        "new_contracts_deployed",   # 신규 컨트랙트 배포
        "whale_movements"           # 대량 전송 감지
    ]
```

**수집 데이터**:
```yaml
onchain_signals:
  moc_token:
    - metric: "daily_transfers"
      value: 1234
      change_24h: "+15%"

    - metric: "unique_holders"
      value: 45678
      change_7d: "+3.2%"

  defi_trends:
    - protocol: "Uniswap"
      tvl: "$5.2B"
      change_24h: "-2.1%"

    - protocol: "Aave"
      tvl: "$12.1B"
      change_24h: "+0.8%"

  emerging_contracts:
    - address: "0x..."
      type: "ERC-721"
      interactions_24h: 5000
      verified: true
```

#### 3.1.4 소셜 미디어 어댑터 (신규)

```python
# src/agentic_orchestrator/adapters/social.py

class SocialMediaAdapter:
    """
    소셜 미디어 트렌드 수집

    플랫폼:
    - X (Twitter) via Nitter/RSS
    - Reddit (via API)
    - Discord (public servers)
    - Farcaster (decentralized social)
    - Lens Protocol
    """

    # Twitter/X 트렌드 (Nitter RSS 활용)
    TWITTER_ACCOUNTS = [
        "VitalikButerin", "caborinho", "punk6529",
        "coaborinho", "MessariCrypto", "DefiLlama",
        "a16zcrypto", "hasufl", "rleshner"
    ]

    # Reddit 서브레딧
    SUBREDDITS = [
        "ethereum", "cryptocurrency", "defi",
        "web3", "nft", "CryptoTechnology",
        "MachineLearning", "LocalLLaMA"
    ]

    # Farcaster 채널
    FARCASTER_CHANNELS = [
        "/ethereum", "/defi", "/nft",
        "/ai", "/dev", "/founders"
    ]
```

**수집 데이터**:
```yaml
social_signals:
  twitter:
    - account: "@VitalikButerin"
      recent_topic: "Account abstraction"
      engagement: "high"
      timestamp: "2026-01-22T09:00:00Z"

  reddit:
    - subreddit: "r/ethereum"
      hot_topics:
        - "EIP-7702 discussion"
        - "L2 comparison thread"
      sentiment: "bullish"

  farcaster:
    - channel: "/defi"
      trending_cast: "..."
      reactions: 500
```

#### 3.1.5 뉴스 API 어댑터 (신규)

```python
# src/agentic_orchestrator/adapters/news.py

class NewsAPIAdapter:
    """
    뉴스 API 통합

    소스:
    - NewsAPI.org (무료 티어)
    - Cryptopanic API
    - Messari News API
    - Alpha Vantage News
    """

    QUERIES = [
        "blockchain",
        "web3 startup",
        "crypto regulation",
        "AI agents",
        "metaverse",
        "NFT gaming"
    ]
```

### 3.2 신호 집계 시스템

```python
# src/agentic_orchestrator/signals/aggregator.py

class SignalAggregator:
    """
    모든 어댑터로부터 신호를 수집하고 정규화

    기능:
    - 중복 제거 (deduplication)
    - 신호 점수화 (scoring)
    - 카테고리 분류
    - 우선순위 결정
    """

    def __init__(self):
        self.adapters = [
            RSSFeedAdapter(),
            GitHubEventsAdapter(),
            OnChainAdapter(),
            SocialMediaAdapter(),
            NewsAPIAdapter()
        ]

    async def collect_all(self) -> List[Signal]:
        """모든 어댑터에서 병렬로 신호 수집"""
        tasks = [adapter.fetch() for adapter in self.adapters]
        results = await asyncio.gather(*tasks)

        signals = self._flatten(results)
        signals = self._deduplicate(signals)
        signals = self._score(signals)

        return sorted(signals, key=lambda s: s.score, reverse=True)
```

### 3.3 신호 데이터 모델

```python
# src/agentic_orchestrator/signals/models.py

@dataclass
class Signal:
    id: str                      # 고유 ID
    source: str                  # 소스 어댑터 이름
    category: str                # ai, crypto, finance, etc.
    title: str                   # 제목
    summary: str                 # 요약
    url: Optional[str]           # 원본 URL
    timestamp: datetime          # 수집 시간
    score: float                 # 관련성 점수 (0-1)
    metadata: Dict[str, Any]     # 추가 메타데이터

    # 선택적 필드
    sentiment: Optional[str]     # positive, negative, neutral
    topics: List[str]            # 관련 토픽
    entities: List[str]          # 추출된 엔티티
```

### 3.4 구현 파일 구조

```
src/agentic_orchestrator/
├── adapters/
│   ├── __init__.py
│   ├── base.py                 # BaseAdapter 인터페이스
│   ├── rss.py                  # RSS 피드 (기존 확장)
│   ├── github_events.py        # GitHub 이벤트 (신규)
│   ├── onchain.py              # 온체인 데이터 (신규)
│   ├── social.py               # 소셜 미디어 (신규)
│   └── news.py                 # 뉴스 API (신규)
├── signals/
│   ├── __init__.py
│   ├── models.py               # Signal 데이터 모델
│   ├── aggregator.py           # 신호 집계
│   ├── scorer.py               # 신호 점수화
│   └── storage.py              # 신호 저장
```

---

## 4. Phase 2: Local LLM 기반 다중 에이전트 토론 시스템

### 4.1 사용 가능한 Local LLM 현황

```
┌─────────────────────────────────────────────────────────────┐
│                    Ollama 모델 현황                         │
├──────────────┬────────┬─────────────────────────────────────┤
│ 모델         │ 크기   │ 추천 용도                           │
├──────────────┼────────┼─────────────────────────────────────┤
│ llama3.3:70b │ 42 GB  │ 중재자, 최종 평가, 복잡한 추론      │
│ qwen2.5:32b  │ 19 GB  │ 수렴 토론, 평가, 기술 검토          │
│ phi4:14b     │ 9.1 GB │ 아이디어 생성, 일반 토론            │
│ qwen2.5:14b  │ 9.0 GB │ 아이디어 생성, 일반 토론            │
│ llama3.2:3b  │ 2.0 GB │ 빠른 요약, 필터링, 분류             │
└──────────────┴────────┴─────────────────────────────────────┘
```

### 4.2 LLM 계층 구조

```python
# src/agentic_orchestrator/llm/hierarchy.py

class LLMHierarchy:
    """
    LLM 사용 계층 구조

    Tier 1 (무료, 무제한):
      - 아이디어 생성, 초기 토론, 요약, 분류
      - ollama 모델 사용

    Tier 2 (유료, 제한적):
      - 최종 계획 생성, 품질 검증
      - Claude, OpenAI API 사용
    """

    TIER_1_MODELS = {
        "moderator": "llama3.3:70b",      # 토론 중재
        "evaluator": "qwen2.5:32b",        # 평가 및 수렴
        "generator_a": "phi4:14b",         # 아이디어 생성
        "generator_b": "qwen2.5:14b",      # 아이디어 생성
        "fast_task": "llama3.2:3b"         # 빠른 작업
    }

    TIER_2_MODELS = {
        "final_plan": "claude-opus-4-5",   # 최종 계획
        "tech_review": "gpt-5.2"           # 기술 검토
    }
```

### 4.3 Ollama 프로바이더 구현

```python
# src/agentic_orchestrator/providers/ollama.py

import httpx
from typing import AsyncIterator

class OllamaProvider:
    """
    Ollama Local LLM 프로바이더

    특징:
    - 완전 무료 (로컬 실행)
    - 스트리밍 지원
    - 다중 모델 동시 실행
    - GPU 메모리 관리
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300)

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = None,
        stream: bool = False
    ) -> str:
        """동기식 생성"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        return response.json()["response"]

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str = None
    ) -> AsyncIterator[str]:
        """스트리밍 생성"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        if system:
            payload["system"] = system

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                data = json.loads(line)
                if "response" in data:
                    yield data["response"]

    async def chat(
        self,
        model: str,
        messages: List[Dict],
        system: str = None
    ) -> str:
        """채팅 형식"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        if system:
            payload["system"] = system

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        return response.json()["message"]["content"]
```

### 4.4 API 사용량 컨트롤러

```python
# src/agentic_orchestrator/llm/budget.py

from dataclasses import dataclass
from datetime import datetime, date
import json
from pathlib import Path

@dataclass
class UsageBudget:
    daily_limit_usd: float = 50.0
    monthly_limit_usd: float = 1500.0

@dataclass
class UsageRecord:
    date: date
    claude_tokens: int = 0
    claude_cost: float = 0.0
    openai_tokens: int = 0
    openai_cost: float = 0.0
    gemini_tokens: int = 0
    gemini_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        return self.claude_cost + self.openai_cost + self.gemini_cost

class BudgetController:
    """
    유료 API 사용량 제어

    기능:
    - 일일/월간 예산 추적
    - 임계값 도달 시 경고
    - 예산 초과 시 Local LLM 자동 폴백
    - 사용량 리포트 생성
    """

    PRICING = {
        "claude-opus-4-5": {"input": 15.0, "output": 75.0},  # per 1M tokens
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "gpt-5.2": {"input": 2.5, "output": 10.0},
        "gemini-3-pro": {"input": 1.25, "output": 5.0}
    }

    def __init__(self, budget: UsageBudget = None, storage_path: str = "data/usage"):
        self.budget = budget or UsageBudget()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def can_use_api(self, model: str, estimated_tokens: int) -> bool:
        """API 사용 가능 여부 확인"""
        today = self.get_today_usage()
        estimated_cost = self._estimate_cost(model, estimated_tokens)

        return (today.total_cost + estimated_cost) <= self.budget.daily_limit_usd

    def record_usage(self, model: str, input_tokens: int, output_tokens: int):
        """사용량 기록"""
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        today = self.get_today_usage()

        if "claude" in model.lower():
            today.claude_tokens += input_tokens + output_tokens
            today.claude_cost += cost
        elif "gpt" in model.lower():
            today.openai_tokens += input_tokens + output_tokens
            today.openai_cost += cost
        elif "gemini" in model.lower():
            today.gemini_tokens += input_tokens + output_tokens
            today.gemini_cost += cost

        self._save_usage(today)

    def get_remaining_budget(self) -> Dict[str, float]:
        """남은 예산 조회"""
        today = self.get_today_usage()
        month = self.get_month_usage()

        return {
            "daily_remaining": self.budget.daily_limit_usd - today.total_cost,
            "monthly_remaining": self.budget.monthly_limit_usd - month,
            "daily_used_percent": (today.total_cost / self.budget.daily_limit_usd) * 100,
            "monthly_used_percent": (month / self.budget.monthly_limit_usd) * 100
        }
```

### 4.5 하이브리드 LLM 라우터

```python
# src/agentic_orchestrator/llm/router.py

class HybridLLMRouter:
    """
    Local LLM과 API LLM 간 지능적 라우팅

    라우팅 전략:
    1. 기본적으로 Local LLM 사용
    2. 복잡한 작업 or 최종 출력은 API 사용
    3. 예산 초과 시 Local LLM 폴백
    4. 품질 요구 수준에 따른 선택
    """

    def __init__(self):
        self.ollama = OllamaProvider()
        self.claude = ClaudeProvider()
        self.openai = OpenAIProvider()
        self.budget = BudgetController()

    async def route(
        self,
        task_type: str,
        prompt: str,
        quality_required: str = "normal",  # low, normal, high, critical
        force_local: bool = False
    ) -> LLMResponse:
        """작업 유형에 따른 LLM 라우팅"""

        # 강제 로컬 모드
        if force_local:
            return await self._use_local(task_type, prompt)

        # 품질 요구 수준에 따른 라우팅
        if quality_required == "critical":
            # 최종 계획, 공개 출력 등
            if self.budget.can_use_api("claude-opus-4-5", 10000):
                return await self.claude.generate(prompt)
            else:
                # 예산 초과 시 최고급 로컬 모델 사용
                return await self.ollama.generate("llama3.3:70b", prompt)

        elif quality_required == "high":
            # 기술 검토, 평가 등
            if self.budget.can_use_api("gpt-5.2", 5000):
                return await self.openai.generate(prompt)
            else:
                return await self.ollama.generate("qwen2.5:32b", prompt)

        else:
            # 일반 작업은 로컬 우선
            return await self._use_local(task_type, prompt)

    async def _use_local(self, task_type: str, prompt: str) -> LLMResponse:
        """로컬 LLM 선택 및 사용"""
        model_map = {
            "moderation": "llama3.3:70b",
            "evaluation": "qwen2.5:32b",
            "generation": "phi4:14b",
            "generation_alt": "qwen2.5:14b",
            "summary": "llama3.2:3b",
            "classification": "llama3.2:3b"
        }
        model = model_map.get(task_type, "qwen2.5:14b")
        return await self.ollama.generate(model, prompt)
```

### 4.6 구현 파일 구조

```
src/agentic_orchestrator/
├── llm/
│   ├── __init__.py
│   ├── hierarchy.py            # LLM 계층 정의
│   ├── router.py               # 하이브리드 라우터
│   └── budget.py               # 예산 컨트롤러
├── providers/
│   ├── __init__.py
│   ├── base.py                 # 기존
│   ├── ollama.py               # Ollama 프로바이더 (신규)
│   ├── claude.py               # 기존
│   ├── openai.py               # 기존
│   └── gemini.py               # 기존
```

---

## 5. Phase 3: 다양한 페르소나 에이전트 시스템

### 5.1 에이전트 페르소나 카탈로그

#### 5.1.1 아이디어 발산 에이전트 (Divergence Phase)

| 페르소나 | 모델 | 역할 | 관점 |
|---------|------|------|------|
| **Frontend Developer** | phi4:14b | 사용자 경험 중심 | UI/UX, 접근성, 반응성 |
| **Backend Engineer** | qwen2.5:14b | 시스템 아키텍처 | 확장성, 성능, 보안 |
| **Blockchain Expert** | phi4:14b | Web3 기술 | 스마트 컨트랙트, DeFi, 토큰 |
| **Product Designer** | qwen2.5:14b | 디자인 씽킹 | 문제 정의, 솔루션, 프로토타입 |
| **Data Scientist** | phi4:14b | 데이터 중심 | 분석, ML, 인사이트 |
| **Marketing Strategist** | qwen2.5:14b | 시장 관점 | GTM, 브랜딩, 성장 |
| **Community Manager** | llama3.2:3b | 커뮤니티 | 참여, 피드백, 소통 |
| **Security Researcher** | phi4:14b | 보안 관점 | 취약점, 리스크, 규정 |

#### 5.1.2 아이디어 수렴 에이전트 (Convergence Phase)

| 페르소나 | 모델 | 역할 | 평가 기준 |
|---------|------|------|----------|
| **VC Partner** | qwen2.5:32b | 투자 관점 | 시장 규모, 성장성, 팀 |
| **Accelerator Mentor** | qwen2.5:32b | 실행 관점 | MVP, 검증, 마일스톤 |
| **Startup CEO** | llama3.3:70b | 창업자 관점 | 비전, 실행력, 리소스 |
| **Domain Expert** | qwen2.5:32b | 전문 지식 | 기술 타당성, 차별화 |

#### 5.1.3 기획서 작성 에이전트 (Planning Phase)

| 페르소나 | 모델 | 담당 문서 |
|---------|------|----------|
| **Product Manager** | llama3.3:70b | PRD (제품 요구사항) |
| **Tech Lead** | qwen2.5:32b | 기술 아키텍처 |
| **UX Researcher** | qwen2.5:14b | 사용자 리서치 |
| **Business Analyst** | phi4:14b | 비즈니스 모델 |
| **Project Manager** | qwen2.5:14b | 프로젝트 계획 |

### 5.2 에이전트 페르소나 정의

```python
# src/agentic_orchestrator/personas/catalog.py

from dataclasses import dataclass
from enum import Enum
from typing import List

class PersonaCategory(Enum):
    DIVERGENCE = "divergence"   # 발산 단계
    CONVERGENCE = "convergence" # 수렴 단계
    PLANNING = "planning"       # 기획 단계

@dataclass
class Persona:
    id: str
    name: str
    category: PersonaCategory
    model: str
    role: str
    perspective: str
    system_prompt: str
    evaluation_criteria: List[str]

# 발산 단계 페르소나
FRONTEND_DEVELOPER = Persona(
    id="frontend_dev",
    name="Frontend Developer",
    category=PersonaCategory.DIVERGENCE,
    model="phi4:14b",
    role="사용자 경험 전문가",
    perspective="UI/UX, 접근성, 반응성",
    system_prompt="""
당신은 10년 경력의 시니어 프론트엔드 개발자입니다.
React, Vue, Svelte 등 다양한 프레임워크 경험이 있습니다.

아이디어를 평가할 때 다음 관점에서 생각합니다:
- 사용자가 이 기능을 어떻게 사용할 것인가?
- UI/UX가 직관적인가?
- 모바일과 데스크톱 모두 지원 가능한가?
- 성능과 접근성은 고려되었는가?
- 구현 복잡도는 어떠한가?

기술적으로 실현 가능한 아이디어를 선호하되,
사용자 경험을 최우선으로 생각합니다.
""",
    evaluation_criteria=[
        "user_experience",
        "technical_feasibility",
        "mobile_compatibility",
        "accessibility"
    ]
)

BLOCKCHAIN_EXPERT = Persona(
    id="blockchain_expert",
    name="Blockchain Expert",
    category=PersonaCategory.DIVERGENCE,
    model="phi4:14b",
    role="Web3 기술 전문가",
    perspective="스마트 컨트랙트, DeFi, 토큰 이코노믹스",
    system_prompt="""
당신은 블록체인 기술 전문가로, Ethereum, Solana, Polygon 등
다양한 체인에서 프로젝트를 진행한 경험이 있습니다.

아이디어를 평가할 때 다음 관점에서 생각합니다:
- 이 아이디어가 블록체인을 필요로 하는가?
- 어떤 체인이 가장 적합한가?
- 스마트 컨트랙트 구조는 어떻게 될 것인가?
- 가스비와 확장성 문제는 어떻게 해결하는가?
- MOC 토큰을 어떻게 활용할 수 있는가?

탈중앙화의 가치를 중요시하되,
실용적인 구현 방안을 제시합니다.
""",
    evaluation_criteria=[
        "blockchain_necessity",
        "chain_selection",
        "smart_contract_design",
        "token_utility"
    ]
)

STARTUP_CEO = Persona(
    id="startup_ceo",
    name="Startup CEO",
    category=PersonaCategory.CONVERGENCE,
    model="llama3.3:70b",
    role="스타트업 창업자",
    perspective="비전, 실행력, 리소스 관리",
    system_prompt="""
당신은 3개의 스타트업을 창업하고 1개를 성공적으로 엑싯한 경험이 있는
연쇄 창업자입니다. Web3와 AI 분야에 깊은 이해가 있습니다.

아이디어를 평가할 때 다음 관점에서 생각합니다:
- 이 아이디어로 회사를 만들 수 있는가?
- 팀이 실행할 수 있는 범위인가?
- 시장 타이밍은 적절한가?
- 차별화 포인트는 명확한가?
- 피벗 가능성은 있는가?

실현 가능하면서도 큰 비전을 가진 아이디어를 선호합니다.
작게 시작해서 크게 성장할 수 있는 길을 찾습니다.
""",
    evaluation_criteria=[
        "vision_clarity",
        "execution_feasibility",
        "market_timing",
        "differentiation",
        "scalability"
    ]
)
```

### 5.3 다단계 토론 시스템

```python
# src/agentic_orchestrator/debate/multi_stage.py

class MultiStageDebate:
    """
    발산-수렴 다단계 토론 시스템

    프로세스:
    1. 발산 단계 (Divergence) - 3라운드
       - 다양한 관점에서 아이디어 확장
       - 각 에이전트가 독립적으로 아이디어 제안
       - 브레인스토밍 모드

    2. 수렴 단계 (Convergence) - 2라운드
       - 아이디어 평가 및 필터링
       - 실현 가능성 검토
       - 최종 후보 선정

    3. 기획 단계 (Planning)
       - 선정된 아이디어에 대한 상세 기획
       - 전문가별 문서 작성
    """

    def __init__(self):
        self.router = HybridLLMRouter()
        self.divergence_agents = self._init_divergence_agents()
        self.convergence_agents = self._init_convergence_agents()
        self.planning_agents = self._init_planning_agents()

    async def run_full_cycle(
        self,
        signals: List[Signal],
        context: Dict
    ) -> DebateResult:
        """전체 토론 사이클 실행"""

        # 1. 발산 단계
        diverged_ideas = await self._divergence_phase(signals, context)

        # 2. 수렴 단계
        selected_ideas = await self._convergence_phase(diverged_ideas)

        # 3. 기획 단계 (선정된 아이디어에 대해서만)
        plans = []
        for idea in selected_ideas:
            plan = await self._planning_phase(idea)
            plans.append(plan)

        return DebateResult(
            signals=signals,
            diverged_ideas=diverged_ideas,
            selected_ideas=selected_ideas,
            plans=plans
        )

    async def _divergence_phase(
        self,
        signals: List[Signal],
        context: Dict
    ) -> List[Idea]:
        """발산 단계: 다양한 관점에서 아이디어 생성"""

        all_ideas = []

        for round_num in range(3):  # 3라운드
            round_ideas = []

            # 각 에이전트가 병렬로 아이디어 생성
            tasks = []
            for agent in self.divergence_agents:
                task = self._generate_idea(
                    agent=agent,
                    signals=signals,
                    context=context,
                    existing_ideas=all_ideas,
                    round_num=round_num
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            round_ideas.extend(results)

            # 중재자가 라운드 정리
            summary = await self._moderate_round(
                round_num=round_num,
                ideas=round_ideas
            )

            all_ideas.extend(round_ideas)

        return all_ideas

    async def _convergence_phase(
        self,
        ideas: List[Idea]
    ) -> List[Idea]:
        """수렴 단계: 아이디어 평가 및 선정"""

        # 1라운드: 각 에이전트가 독립적으로 평가
        evaluations = []
        for agent in self.convergence_agents:
            eval_result = await self._evaluate_ideas(agent, ideas)
            evaluations.append(eval_result)

        # 2라운드: 토론 및 최종 선정
        final_selection = await self._final_selection(
            ideas=ideas,
            evaluations=evaluations
        )

        return final_selection

    async def _planning_phase(
        self,
        idea: Idea
    ) -> Plan:
        """기획 단계: 상세 기획서 작성"""

        # 각 전문가가 담당 영역 작성
        tasks = {
            "prd": self._write_prd(idea),
            "architecture": self._write_architecture(idea),
            "user_research": self._write_user_research(idea),
            "business_model": self._write_business_model(idea),
            "project_plan": self._write_project_plan(idea)
        }

        results = await asyncio.gather(*tasks.values())

        # 최종 통합 (Claude API 사용)
        final_plan = await self._integrate_plan(
            idea=idea,
            documents=dict(zip(tasks.keys(), results))
        )

        return final_plan
```

### 5.4 토론 프로토콜

```python
# src/agentic_orchestrator/debate/protocol.py

class DebateProtocol:
    """
    에이전트 간 토론 프로토콜

    규칙:
    1. 각 에이전트는 자신의 관점을 명확히 표현
    2. 다른 에이전트의 의견을 인용할 때 명시
    3. 동의/반대 시 근거 제시
    4. 새로운 아이디어 제안 시 연결고리 설명
    5. 중재자는 합의점 도출 시도
    """

    MESSAGE_TYPES = [
        "PROPOSE",      # 새 아이디어 제안
        "SUPPORT",      # 기존 아이디어 지지
        "CHALLENGE",    # 기존 아이디어 반박
        "REFINE",       # 기존 아이디어 개선
        "MERGE",        # 여러 아이디어 통합
        "WITHDRAW",     # 아이디어 철회
        "CONSENSUS"     # 합의 도달
    ]

    @dataclass
    class DebateMessage:
        agent_id: str
        message_type: str
        content: str
        references: List[str]  # 참조하는 이전 메시지 ID
        timestamp: datetime
        metadata: Dict[str, Any]
```

### 5.5 구현 파일 구조

```
src/agentic_orchestrator/
├── personas/
│   ├── __init__.py
│   ├── catalog.py              # 페르소나 카탈로그
│   ├── divergence.py           # 발산 에이전트 정의
│   ├── convergence.py          # 수렴 에이전트 정의
│   └── planning.py             # 기획 에이전트 정의
├── debate/
│   ├── __init__.py
│   ├── multi_stage.py          # 다단계 토론 시스템
│   ├── protocol.py             # 토론 프로토콜
│   ├── moderator.py            # 중재자 (기존 확장)
│   ├── debate_session.py       # 세션 관리 (기존 확장)
│   └── discussion_record.py    # 기록 (기존)
```

---

## 6. Phase 4: CLI 스타일 레트로 웹 인터페이스

### 6.1 디자인 컨셉

```
┌──────────────────────────────────────────────────────────────────────┐
│ ████████╗██╗  ██╗███████╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗ │
│ ╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝ │
│    ██║   ███████║█████╗      ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║    │
│    ██║   ██╔══██║██╔══╝      ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║    │
│    ██║   ██║  ██║███████╗    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║    │
│    ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    │
│                        ORCHESTRATOR v0.4.0                               │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌─ SIGNALS ─────────────────┐ ┌─ DEBATE ──────────────────────────────┐ │
│ │ > RSS: 45 feeds active    │ │ [DIVERGENCE] Round 2/3               │ │
│ │ > GitHub: watching 25 repos│ │                                      │ │
│ │ > OnChain: ETH, MOC       │ │ @FrontendDev: "This could work with  │ │
│ │ > Social: 12 channels     │ │ a React-based dashboard that..."     │ │
│ │                           │ │                                      │ │
│ │ Last sync: 2 min ago      │ │ @BlockchainExpert: "I agree, but we  │ │
│ │ Next sync: 13 min         │ │ should consider gas optimization..." │ │
│ │                           │ │                                      │ │
│ │ ████████████░░░░ 75%      │ │ @DataScientist: "The user data shows │ │
│ │ Processing signals...     │ │ potential for ML integration..."     │ │
│ └───────────────────────────┘ └──────────────────────────────────────┘ │
│ ┌─ PROCESSES ───────────────┐ ┌─ OUTPUT ─────────────────────────────┐ │
│ │ PID   NAME          STATUS│ │ > Idea #42 selected for planning     │ │
│ │ 1001  signal-fetch  ACTIVE│ │ > Writing PRD...                     │ │
│ │ 1002  debate-01     ACTIVE│ │ > Architecture review: PASSED        │ │
│ │ 1003  debate-02     IDLE  │ │ > Creating GitHub Issue...           │ │
│ │ 1004  llm-router    ACTIVE│ │ > Done: IDEA-2026-0122-001           │ │
│ │ 1005  budget-mon    ACTIVE│ │                                      │ │
│ └───────────────────────────┘ └──────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│ wooram@agent-orch:~$ █                                                   │
│                                                                          │
│ ┌─ COMMANDS ────────────────────────────────────────────────────────────┐│
│ │  [↑↓] Navigate  [ENTER] Select  [ESC] Cancel                         ││
│ │                                                                       ││
│ │  > run cycle          Start full orchestration cycle                  ││
│ │    view signals       Show current signal analysis                    ││
│ │    view debate        Watch ongoing debate session                    ││
│ │    view budget        Check API usage and budget                      ││
│ │    config             Modify settings                                 ││
│ │    help               Show all commands                               ││
│ └───────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 디자인 시스템

```css
/* website/src/styles/retro.css */

:root {
  /* 레트로 컬러 팔레트 */
  --bg-primary: #0a0a0a;        /* 깊은 검정 */
  --bg-secondary: #1a1a2e;       /* 어두운 남색 */
  --bg-terminal: #0d1117;        /* 터미널 배경 */

  --text-primary: #00ff41;       /* 매트릭스 그린 */
  --text-secondary: #39ff14;     /* 네온 그린 */
  --text-muted: #4a9f4a;         /* 음소거 그린 */
  --text-warning: #ffb000;       /* 앰버 */
  --text-error: #ff073a;         /* 네온 레드 */
  --text-info: #00d4ff;          /* 사이버 블루 */

  --border-color: #2d5a2d;       /* 어두운 그린 */
  --border-glow: #00ff41;        /* 글로우 그린 */

  --accent-purple: #9d00ff;      /* 네온 퍼플 */
  --accent-pink: #ff00ff;        /* 마젠타 */
  --accent-orange: #ff6600;      /* 오렌지 */

  /* 레트로 폰트 */
  --font-mono: 'IBM Plex Mono', 'JetBrains Mono', 'Fira Code', monospace;
  --font-pixel: 'Press Start 2P', monospace;

  /* 글로우 효과 */
  --glow-green: 0 0 5px #00ff41, 0 0 10px #00ff41, 0 0 15px #00ff41;
  --glow-blue: 0 0 5px #00d4ff, 0 0 10px #00d4ff;
  --glow-amber: 0 0 5px #ffb000, 0 0 10px #ffb000;
}

/* 스캔라인 효과 */
.scanlines::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.15),
    rgba(0, 0, 0, 0.15) 1px,
    transparent 1px,
    transparent 2px
  );
  pointer-events: none;
  z-index: 100;
}

/* CRT 곡면 효과 */
.crt-curve {
  border-radius: 20px;
  box-shadow:
    inset 0 0 100px rgba(0, 255, 65, 0.1),
    0 0 20px rgba(0, 255, 65, 0.2);
}

/* 타이핑 커서 */
.cursor {
  display: inline-block;
  width: 10px;
  height: 20px;
  background: var(--text-primary);
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

/* 터미널 프롬프트 */
.prompt {
  color: var(--text-info);
}

.prompt::before {
  content: "$ ";
  color: var(--text-secondary);
}
```

### 6.3 React 컴포넌트 구조

```typescript
// website/src/components/Terminal/Terminal.tsx

import { useState, useEffect, useRef } from 'react';

interface Command {
  id: string;
  label: string;
  description: string;
  action: () => void;
}

export function Terminal() {
  const [history, setHistory] = useState<string[]>([]);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedCommand, setSelectedCommand] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: Command[] = [
    { id: 'run-cycle', label: 'run cycle', description: 'Start full orchestration cycle', action: handleRunCycle },
    { id: 'view-signals', label: 'view signals', description: 'Show current signal analysis', action: handleViewSignals },
    { id: 'view-debate', label: 'view debate', description: 'Watch ongoing debate session', action: handleViewDebate },
    { id: 'view-budget', label: 'view budget', description: 'Check API usage and budget', action: handleViewBudget },
    { id: 'config', label: 'config', description: 'Modify settings', action: handleConfig },
    { id: 'help', label: 'help', description: 'Show all commands', action: handleHelp },
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        setShowCommands(true);
      } else if (e.key === 'Escape') {
        setShowCommands(false);
      } else if (e.key === 'ArrowUp' && showCommands) {
        setSelectedCommand(prev => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowDown' && showCommands) {
        setSelectedCommand(prev => Math.min(commands.length - 1, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showCommands, commands.length]);

  return (
    <div className="terminal crt-curve scanlines">
      <div className="terminal-header">
        <span className="text-muted">wooram@agent-orch</span>
        <span className="text-primary">:~$</span>
        <span className="cursor" />
      </div>

      {showCommands && (
        <CommandPalette
          commands={commands}
          selectedIndex={selectedCommand}
          onSelect={(cmd) => {
            cmd.action();
            setShowCommands(false);
          }}
        />
      )}

      <div className="terminal-hint">
        Press <kbd>ENTER</kbd> to open command palette
      </div>
    </div>
  );
}
```

```typescript
// website/src/components/Terminal/CommandPalette.tsx

interface CommandPaletteProps {
  commands: Command[];
  selectedIndex: number;
  onSelect: (cmd: Command) => void;
}

export function CommandPalette({ commands, selectedIndex, onSelect }: CommandPaletteProps) {
  return (
    <div className="command-palette">
      <div className="palette-header">
        <span>[↑↓] Navigate</span>
        <span>[ENTER] Select</span>
        <span>[ESC] Cancel</span>
      </div>

      <ul className="command-list">
        {commands.map((cmd, index) => (
          <li
            key={cmd.id}
            className={`command-item ${index === selectedIndex ? 'selected' : ''}`}
            onClick={() => onSelect(cmd)}
          >
            <span className="command-label">
              {index === selectedIndex ? '> ' : '  '}
              {cmd.label}
            </span>
            <span className="command-desc">{cmd.description}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 6.4 실시간 로그 패널

```typescript
// website/src/components/LogPanel/LogPanel.tsx

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  source: string;
  message: string;
}

export function LogPanel({ title, source }: { title: string; source: string }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const { lastMessage } = useWebSocket(`ws://localhost:8080/logs/${source}`);

  useEffect(() => {
    if (lastMessage) {
      const entry = JSON.parse(lastMessage.data) as LogEntry;
      setLogs(prev => [...prev.slice(-100), entry]); // 최근 100개만 유지
    }
  }, [lastMessage]);

  return (
    <div className="log-panel">
      <div className="panel-header">
        <span className="panel-title">─ {title} ─</span>
      </div>

      <div className="log-content">
        {logs.map((log, i) => (
          <div key={i} className={`log-entry log-${log.level}`}>
            <span className="log-time">[{log.timestamp}]</span>
            <span className="log-source">[{log.source}]</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 6.5 모바일 반응형 레이아웃

```typescript
// website/src/components/Layout/ResponsiveLayout.tsx

import { useState, useEffect } from 'react';

export function ResponsiveLayout({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState(false);
  const [activePanel, setActivePanel] = useState<'signals' | 'debate' | 'output'>('debate');

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (isMobile) {
    return (
      <div className="mobile-layout">
        <MobileHeader />

        <div className="mobile-tabs">
          <button
            className={activePanel === 'signals' ? 'active' : ''}
            onClick={() => setActivePanel('signals')}
          >
            SIGNALS
          </button>
          <button
            className={activePanel === 'debate' ? 'active' : ''}
            onClick={() => setActivePanel('debate')}
          >
            DEBATE
          </button>
          <button
            className={activePanel === 'output' ? 'active' : ''}
            onClick={() => setActivePanel('output')}
          >
            OUTPUT
          </button>
        </div>

        <div className="mobile-content">
          {activePanel === 'signals' && <SignalsPanel />}
          {activePanel === 'debate' && <DebatePanel />}
          {activePanel === 'output' && <OutputPanel />}
        </div>

        <MobileCommandBar />
      </div>
    );
  }

  return (
    <div className="desktop-layout">
      <Header />
      <div className="main-grid">
        <div className="left-column">
          <SignalsPanel />
          <ProcessesPanel />
        </div>
        <div className="center-column">
          <DebatePanel />
        </div>
        <div className="right-column">
          <OutputPanel />
          <BudgetPanel />
        </div>
      </div>
      <Terminal />
    </div>
  );
}
```

### 6.6 모바일 커맨드 바

```typescript
// website/src/components/Mobile/MobileCommandBar.tsx

export function MobileCommandBar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mobile-command-bar">
      <button
        className="command-trigger"
        onClick={() => setIsOpen(true)}
      >
        <span className="prompt">$</span>
        <span className="hint">Tap to open commands</span>
      </button>

      {isOpen && (
        <div className="command-sheet">
          <div className="sheet-header">
            <span>Commands</span>
            <button onClick={() => setIsOpen(false)}>×</button>
          </div>

          <div className="command-grid">
            <CommandButton icon="▶" label="Run Cycle" />
            <CommandButton icon="📡" label="Signals" />
            <CommandButton icon="💬" label="Debate" />
            <CommandButton icon="💰" label="Budget" />
            <CommandButton icon="⚙" label="Config" />
            <CommandButton icon="?" label="Help" />
          </div>
        </div>
      )}
    </div>
  );
}
```

### 6.7 구현 파일 구조

```
website/
├── src/
│   ├── app/
│   │   ├── page.tsx                 # 메인 대시보드
│   │   ├── layout.tsx               # 레이아웃
│   │   └── globals.css              # 전역 스타일
│   ├── components/
│   │   ├── Terminal/
│   │   │   ├── Terminal.tsx         # 터미널 UI
│   │   │   ├── CommandPalette.tsx   # 커맨드 팔레트
│   │   │   └── TerminalHistory.tsx  # 히스토리
│   │   ├── LogPanel/
│   │   │   ├── LogPanel.tsx         # 로그 패널
│   │   │   └── LogEntry.tsx         # 로그 항목
│   │   ├── Panels/
│   │   │   ├── SignalsPanel.tsx     # 신호 패널
│   │   │   ├── DebatePanel.tsx      # 토론 패널
│   │   │   ├── OutputPanel.tsx      # 출력 패널
│   │   │   ├── ProcessesPanel.tsx   # 프로세스 패널
│   │   │   └── BudgetPanel.tsx      # 예산 패널
│   │   ├── Layout/
│   │   │   ├── ResponsiveLayout.tsx # 반응형 레이아웃
│   │   │   ├── Header.tsx           # 헤더
│   │   │   └── MobileHeader.tsx     # 모바일 헤더
│   │   └── Mobile/
│   │       ├── MobileCommandBar.tsx # 모바일 커맨드
│   │       └── MobileTabs.tsx       # 모바일 탭
│   ├── styles/
│   │   ├── retro.css               # 레트로 스타일
│   │   ├── terminal.css            # 터미널 스타일
│   │   └── mobile.css              # 모바일 스타일
│   ├── hooks/
│   │   ├── useWebSocket.ts         # WebSocket 훅
│   │   └── useTerminal.ts          # 터미널 훅
│   └── lib/
│       ├── api.ts                  # API 클라이언트
│       └── ws.ts                   # WebSocket 클라이언트
```

---

## 7. Phase 5: PM2 기반 상시 운영 시스템

### 7.1 PM2 에코시스템 설정

```javascript
// ecosystem.config.js

module.exports = {
  apps: [
    // 메인 오케스트레이터
    {
      name: 'orchestrator-main',
      script: 'python',
      args: '-m agentic_orchestrator.server',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/path/to/agentic-orchestrator/src',
        OLLAMA_HOST: 'http://localhost:11434'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: 'logs/orchestrator-error.log',
      out_file: 'logs/orchestrator-out.log',
      merge_logs: true
    },

    // 신호 수집기
    {
      name: 'signal-collector',
      script: 'python',
      args: '-m agentic_orchestrator.signals.collector',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      cron_restart: '*/15 * * * *',  // 15분마다 재시작
      autorestart: true,
      max_memory_restart: '512M'
    },

    // 토론 워커 (여러 인스턴스)
    {
      name: 'debate-worker',
      script: 'python',
      args: '-m agentic_orchestrator.debate.worker',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      instances: 2,
      exec_mode: 'fork',
      autorestart: true,
      max_memory_restart: '4G'
    },

    // 웹 서버
    {
      name: 'web-server',
      script: 'npm',
      args: 'start',
      cwd: '/path/to/agentic-orchestrator/website',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      instances: 1,
      autorestart: true
    },

    // WebSocket 서버
    {
      name: 'ws-server',
      script: 'python',
      args: '-m agentic_orchestrator.ws_server',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      env: {
        WS_PORT: '8080'
      },
      autorestart: true
    },

    // 예산 모니터
    {
      name: 'budget-monitor',
      script: 'python',
      args: '-m agentic_orchestrator.llm.budget_monitor',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      cron_restart: '0 * * * *',  // 매 시간 재시작
      autorestart: true,
      max_memory_restart: '256M'
    },

    // 스케줄러
    {
      name: 'scheduler',
      script: 'python',
      args: '-m agentic_orchestrator.scheduler',
      cwd: '/path/to/agentic-orchestrator',
      interpreter: 'none',
      autorestart: true,
      max_memory_restart: '256M'
    }
  ]
};
```

### 7.2 스케줄러 구현

```python
# src/agentic_orchestrator/scheduler.py

import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class OrchestratorScheduler:
    """
    PM2와 함께 작동하는 스케줄러

    스케줄:
    - 매 15분: 신호 수집
    - 매 시간: 트렌드 분석
    - 매 4시간: 아이디어 발산 토론
    - 매일 09:00 KST: 수렴 토론 및 기획
    - 매일 00:00 KST: 예산 리셋 및 리포트
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        # 신호 수집 (15분마다)
        self.scheduler.add_job(
            self.collect_signals,
            CronTrigger(minute='*/15'),
            id='signal_collection',
            name='Signal Collection'
        )

        # 트렌드 분석 (매 시간)
        self.scheduler.add_job(
            self.analyze_trends,
            CronTrigger(minute=0),
            id='trend_analysis',
            name='Trend Analysis'
        )

        # 발산 토론 (4시간마다)
        self.scheduler.add_job(
            self.run_divergence_debate,
            CronTrigger(hour='*/4', minute=30),
            id='divergence_debate',
            name='Divergence Debate'
        )

        # 수렴 토론 및 기획 (매일 09:00 KST)
        self.scheduler.add_job(
            self.run_convergence_and_planning,
            CronTrigger(hour=0, minute=0, timezone='UTC'),  # 00:00 UTC = 09:00 KST
            id='daily_planning',
            name='Daily Planning'
        )

        # 예산 리포트 (매일 자정)
        self.scheduler.add_job(
            self.daily_budget_report,
            CronTrigger(hour=15, minute=0, timezone='UTC'),  # 15:00 UTC = 00:00 KST
            id='budget_report',
            name='Budget Report'
        )

    async def collect_signals(self):
        """신호 수집 작업"""
        from agentic_orchestrator.signals.aggregator import SignalAggregator

        aggregator = SignalAggregator()
        signals = await aggregator.collect_all()

        # 저장
        from agentic_orchestrator.signals.storage import SignalStorage
        storage = SignalStorage()
        await storage.save(signals)

        print(f"[{datetime.now()}] Collected {len(signals)} signals")

    async def analyze_trends(self):
        """트렌드 분석 작업"""
        from agentic_orchestrator.trends.analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()
        trends = await analyzer.analyze_recent()

        print(f"[{datetime.now()}] Analyzed {len(trends)} trends")

    async def run_divergence_debate(self):
        """발산 토론 작업"""
        from agentic_orchestrator.debate.multi_stage import MultiStageDebate
        from agentic_orchestrator.signals.storage import SignalStorage

        storage = SignalStorage()
        recent_signals = await storage.get_recent(hours=4)

        if not recent_signals:
            print(f"[{datetime.now()}] No signals to process")
            return

        debate = MultiStageDebate()
        ideas = await debate._divergence_phase(recent_signals, {})

        print(f"[{datetime.now()}] Generated {len(ideas)} ideas from divergence debate")

    async def run_convergence_and_planning(self):
        """수렴 토론 및 기획 작업"""
        from agentic_orchestrator.debate.multi_stage import MultiStageDebate

        debate = MultiStageDebate()

        # 최근 아이디어 가져오기
        ideas = await self._get_pending_ideas()

        if not ideas:
            print(f"[{datetime.now()}] No ideas to process")
            return

        # 수렴 토론
        selected = await debate._convergence_phase(ideas)

        # 기획서 작성
        for idea in selected:
            plan = await debate._planning_phase(idea)
            await self._create_github_issue(plan)

        print(f"[{datetime.now()}] Created {len(selected)} plans")

    async def daily_budget_report(self):
        """일일 예산 리포트"""
        from agentic_orchestrator.llm.budget import BudgetController

        budget = BudgetController()
        report = budget.generate_daily_report()

        # 슬랙/이메일 등으로 전송 가능
        print(f"[{datetime.now()}] Budget Report:\n{report}")

    def start(self):
        """스케줄러 시작"""
        self.scheduler.start()
        print(f"[{datetime.now()}] Scheduler started")

    def stop(self):
        """스케줄러 중지"""
        self.scheduler.shutdown()
        print(f"[{datetime.now()}] Scheduler stopped")


if __name__ == '__main__':
    scheduler = OrchestratorScheduler()
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        scheduler.stop()
```

### 7.3 PM2 관리 스크립트

```bash
#!/bin/bash
# scripts/pm2-manage.sh

# PM2 명령어 래퍼

case "$1" in
  start)
    echo "Starting all services..."
    pm2 start ecosystem.config.js
    ;;

  stop)
    echo "Stopping all services..."
    pm2 stop all
    ;;

  restart)
    echo "Restarting all services..."
    pm2 restart all
    ;;

  status)
    pm2 status
    ;;

  logs)
    if [ -z "$2" ]; then
      pm2 logs --lines 100
    else
      pm2 logs "$2" --lines 100
    fi
    ;;

  monitor)
    pm2 monit
    ;;

  reload)
    echo "Zero-downtime reload..."
    pm2 reload ecosystem.config.js
    ;;

  save)
    echo "Saving PM2 process list..."
    pm2 save
    ;;

  startup)
    echo "Setting up PM2 startup script..."
    pm2 startup
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs|monitor|reload|save|startup}"
    exit 1
    ;;
esac
```

### 7.4 헬스 체크 엔드포인트

```python
# src/agentic_orchestrator/health.py

from fastapi import FastAPI, Response
from datetime import datetime
import psutil

app = FastAPI()

@app.get("/health")
async def health_check():
    """PM2 헬스 체크용 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": get_uptime(),
        "memory_usage": psutil.virtual_memory().percent,
        "cpu_usage": psutil.cpu_percent()
    }

@app.get("/health/ollama")
async def ollama_health():
    """Ollama 서버 상태 체크"""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            return {
                "status": "healthy",
                "models": [m["name"] for m in models]
            }
    except Exception as e:
        return Response(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@app.get("/health/budget")
async def budget_health():
    """예산 상태 체크"""
    from agentic_orchestrator.llm.budget import BudgetController

    budget = BudgetController()
    remaining = budget.get_remaining_budget()

    status = "healthy"
    if remaining["daily_used_percent"] > 90:
        status = "warning"
    if remaining["daily_used_percent"] >= 100:
        status = "critical"

    return {
        "status": status,
        **remaining
    }
```

### 7.5 구현 파일 구조

```
/
├── ecosystem.config.js          # PM2 설정
├── scripts/
│   ├── pm2-manage.sh           # PM2 관리 스크립트
│   ├── setup-pm2.sh            # PM2 초기 설정
│   └── deploy.sh               # 배포 스크립트
├── src/agentic_orchestrator/
│   ├── scheduler.py            # 스케줄러
│   ├── server.py               # 메인 서버
│   ├── ws_server.py            # WebSocket 서버
│   └── health.py               # 헬스 체크
```

---

## 8. 기술 스택 및 아키텍처

### 8.1 전체 기술 스택

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Next.js 16 │ React 19 │ TypeScript │ Tailwind CSS │ Framer Motion │
│  WebSocket │ 레트로 CSS │ 반응형 디자인                             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP/WebSocket
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Python 3.10+ │ FastAPI │ AsyncIO │ APScheduler │ Click CLI        │
│  WebSocket Server │ Health Checks                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
┌──────────────────────┐ ┌───────────────┐ ┌──────────────────────────┐
│     LOCAL LLM        │ │   API LLM     │ │     DATA ADAPTERS        │
├──────────────────────┤ ├───────────────┤ ├──────────────────────────┤
│ Ollama               │ │ Claude API    │ │ RSS Feed Adapter         │
│ - llama3.3:70b       │ │ OpenAI API    │ │ GitHub Events Adapter    │
│ - qwen2.5:32b        │ │ Gemini API    │ │ OnChain Data Adapter     │
│ - phi4:14b           │ │               │ │ Social Media Adapter     │
│ - qwen2.5:14b        │ │ Budget Control│ │ News API Adapter         │
│ - llama3.2:3b        │ │ $50/day max   │ │                          │
└──────────────────────┘ └───────────────┘ └──────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         STORAGE                                     │
├─────────────────────────────────────────────────────────────────────┤
│  GitHub Issues (Ideas/Plans) │ Markdown Files │ YAML Config        │
│  data/signals/ │ data/trends/ │ data/usage/ │ logs/                │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         OPERATIONS                                  │
├─────────────────────────────────────────────────────────────────────┤
│  PM2 Process Manager │ Scheduler │ Health Monitoring               │
│  Mac mini (M-series) │ 24/7 Operation                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 데이터 흐름 다이어그램

```
                    ┌─────────────────────────────────────────────────┐
                    │              SIGNAL SOURCES                     │
                    │  RSS(45) │ GitHub(25) │ OnChain │ Social(12)   │
                    └────────────────────┬────────────────────────────┘
                                         │
                                         ↓ (15분마다)
                    ┌─────────────────────────────────────────────────┐
                    │           SIGNAL AGGREGATOR                     │
                    │     수집 → 정규화 → 중복제거 → 점수화           │
                    └────────────────────┬────────────────────────────┘
                                         │
                                         ↓ (1시간마다)
                    ┌─────────────────────────────────────────────────┐
                    │            TREND ANALYZER                       │
                    │   llama3.2:3b (분류) → phi4:14b (분석)          │
                    └────────────────────┬────────────────────────────┘
                                         │
                                         ↓ (4시간마다)
┌─────────────────────────────────────────────────────────────────────────┐
│                        DIVERGENCE DEBATE (3 rounds)                     │
│                                                                         │
│  [FrontendDev]    [BackendEng]    [BlockchainExpert]    [Designer]     │
│     phi4:14b       qwen2.5:14b         phi4:14b        qwen2.5:14b     │
│                                                                         │
│  [DataScientist]  [Marketer]     [CommunityMgr]      [Security]        │
│     phi4:14b      qwen2.5:14b       llama3.2:3b        phi4:14b        │
│                                                                         │
│                    ↓ Moderated by llama3.3:70b                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ↓ (매일 09:00 KST)
┌─────────────────────────────────────────────────────────────────────────┐
│                       CONVERGENCE DEBATE (2 rounds)                     │
│                                                                         │
│       [VC Partner]        [Accelerator]        [Startup CEO]           │
│        qwen2.5:32b         qwen2.5:32b         llama3.3:70b            │
│                                                                         │
│                       [Domain Expert]                                   │
│                        qwen2.5:32b                                      │
│                                                                         │
│                    ↓ Evaluated by qwen2.5:32b                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         PLANNING PHASE                                  │
│                                                                         │
│  [PM] PRD       [TechLead] Arch   [UXRes] Research   [BA] Business     │
│  llama3.3:70b    qwen2.5:32b       qwen2.5:14b         phi4:14b        │
│                                                                         │
│                    ↓ Final integration by Claude Opus                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ↓
                    ┌─────────────────────────────────────────────────┐
                    │              OUTPUT                              │
                    │   GitHub Issue [PLAN] + Detailed Documents      │
                    └─────────────────────────────────────────────────┘
```

### 8.3 의존성 추가

```toml
# pyproject.toml 추가 의존성

[project.dependencies]
# 기존 의존성...

# 신호 수집
feedparser = ">=6.0.0"
httpx = ">=0.25.0"
web3 = ">=6.0.0"           # 온체인 데이터
praw = ">=7.0.0"           # Reddit API

# 스케줄링
apscheduler = ">=3.10.0"

# 서버
fastapi = ">=0.100.0"
uvicorn = ">=0.23.0"
websockets = ">=11.0"

# 모니터링
psutil = ">=5.9.0"
```

---

## 9. 구현 일정

### Phase 1: 다중 신호 어댑터 (1-2주)

```
Week 1:
  - [ ] RSS 피드 확장 (17 → 45개)
  - [ ] GitHub 이벤트 어댑터 구현
  - [ ] 신호 집계 시스템 구현

Week 2:
  - [ ] 온체인 데이터 어댑터 구현
  - [ ] 소셜 미디어 어댑터 구현
  - [ ] 뉴스 API 어댑터 구현
  - [ ] 통합 테스트
```

### Phase 2: Local LLM 시스템 (1-2주)

```
Week 3:
  - [ ] Ollama 프로바이더 구현
  - [ ] 하이브리드 LLM 라우터 구현
  - [ ] 예산 컨트롤러 구현

Week 4:
  - [ ] LLM 계층 구조 구현
  - [ ] 성능 최적화
  - [ ] 폴백 로직 테스트
```

### Phase 3: 페르소나 에이전트 (2주)

```
Week 5:
  - [ ] 발산 에이전트 8개 구현
  - [ ] 수렴 에이전트 4개 구현
  - [ ] 기획 에이전트 5개 구현

Week 6:
  - [ ] 다단계 토론 시스템 구현
  - [ ] 토론 프로토콜 구현
  - [ ] 통합 테스트
```

### Phase 4: 레트로 웹 인터페이스 (2주)

```
Week 7:
  - [ ] 디자인 시스템 구축
  - [ ] 터미널 컴포넌트 구현
  - [ ] 로그 패널 구현

Week 8:
  - [ ] 반응형 레이아웃 구현
  - [ ] 모바일 최적화
  - [ ] WebSocket 연동
```

### Phase 5: PM2 운영 시스템 (1주)

```
Week 9:
  - [ ] PM2 에코시스템 설정
  - [ ] 스케줄러 구현
  - [ ] 헬스 체크 구현
  - [ ] 배포 스크립트 작성
```

---

## 10. 리스크 및 대응 방안

### 10.1 기술적 리스크

| 리스크 | 영향 | 확률 | 대응 방안 |
|--------|------|------|----------|
| Ollama 성능 부족 | 높음 | 중간 | 모델 양자화, 배치 처리 최적화 |
| 메모리 부족 | 높음 | 낮음 | 모델 언로드 전략, 메모리 모니터링 |
| API 비용 초과 | 중간 | 낮음 | 엄격한 예산 컨트롤, 알림 시스템 |
| 신호 소스 불안정 | 중간 | 중간 | 폴백 소스, 캐싱, 재시도 로직 |

### 10.2 운영 리스크

| 리스크 | 영향 | 확률 | 대응 방안 |
|--------|------|------|----------|
| 서버 다운타임 | 높음 | 낮음 | PM2 자동 재시작, 헬스 체크 |
| 데이터 손실 | 높음 | 매우 낮음 | 정기 백업, Git 기반 저장 |
| 보안 취약점 | 높음 | 낮음 | API 키 관리, 접근 제어 |

### 10.3 비용 예측

```
월간 예상 비용:
  - Claude API: $1,000 (최종 계획 생성)
  - OpenAI API: $300 (기술 검토)
  - Gemini API: $200 (빠른 작업)
  - 전기료: ~$50 (Mac mini 24/7)
  - 기타: ~$50 (도메인, SSL 등)

총 예상: ~$1,600/월

절감 효과:
  - 기존 (모든 작업 API): ~$5,000/월
  - 신규 (하이브리드): ~$1,600/월
  - 절감율: 약 68%
```

---

## 부록 A: 파일 구조 전체

```
agentic-orchestrator/
├── .agent/
├── .claude/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
│       ├── backlog.yml
│       └── ci.yml
├── alerts/
├── data/
│   ├── signals/          # 신규
│   ├── trends/
│   └── usage/            # 신규
├── docs/
├── logs/
├── projects/
├── prompts/
├── scripts/              # 신규
│   ├── pm2-manage.sh
│   ├── setup-pm2.sh
│   └── deploy.sh
├── src/agentic_orchestrator/
│   ├── __init__.py
│   ├── backlog.py
│   ├── cli.py
│   ├── github_client.py
│   ├── health.py         # 신규
│   ├── orchestrator.py
│   ├── scheduler.py      # 신규
│   ├── server.py         # 신규
│   ├── state.py
│   ├── ws_server.py      # 신규
│   ├── adapters/         # 신규
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── rss.py
│   │   ├── github_events.py
│   │   ├── onchain.py
│   │   ├── social.py
│   │   └── news.py
│   ├── debate/
│   │   ├── __init__.py
│   │   ├── debate_session.py
│   │   ├── discussion_record.py
│   │   ├── moderator.py
│   │   ├── multi_stage.py    # 신규
│   │   ├── protocol.py       # 신규
│   │   └── roles.py
│   ├── llm/              # 신규
│   │   ├── __init__.py
│   │   ├── budget.py
│   │   ├── hierarchy.py
│   │   └── router.py
│   ├── personas/         # 신규
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   ├── convergence.py
│   │   ├── divergence.py
│   │   └── planning.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── claude.py
│   │   ├── gemini.py
│   │   ├── ollama.py     # 신규
│   │   └── openai.py
│   ├── signals/          # 신규
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── models.py
│   │   ├── scorer.py
│   │   └── storage.py
│   ├── stages/
│   ├── trends/
│   └── utils/
├── tests/
├── website/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── Layout/       # 신규
│   │   │   ├── LogPanel/     # 신규
│   │   │   ├── Mobile/       # 신규
│   │   │   ├── Panels/       # 신규
│   │   │   └── Terminal/     # 신규
│   │   ├── hooks/            # 신규
│   │   ├── lib/
│   │   └── styles/           # 신규
│   └── public/
├── config.yaml
├── ecosystem.config.js   # 신규
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── PROGRESS.md
└── UPGRADE_PLAN.md       # 이 문서
```

---

## 부록 B: 환경 설정 예시

```bash
# .env.example (업데이트)

# GitHub
GITHUB_TOKEN=ghp_xxxxx
GITHUB_OWNER=mossland
GITHUB_REPO=agentic-orchestrator

# LLM APIs (유료)
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
GEMINI_API_KEY=AIzaSyxxxxx

# Ollama (로컬)
OLLAMA_HOST=http://localhost:11434

# 예산 설정
DAILY_BUDGET_USD=50.0
MONTHLY_BUDGET_USD=1500.0

# 신호 수집
NEWS_API_KEY=xxxxx
ALCHEMY_API_KEY=xxxxx    # 온체인 데이터
REDDIT_CLIENT_ID=xxxxx
REDDIT_CLIENT_SECRET=xxxxx

# 서버 설정
WEB_PORT=3000
WS_PORT=8080
HEALTH_PORT=8081

# 스케줄 설정
SIGNAL_COLLECT_INTERVAL=15  # 분
TREND_ANALYZE_INTERVAL=60   # 분
DIVERGENCE_INTERVAL=240     # 분
DAILY_PLANNING_HOUR=0       # UTC (09:00 KST)
```

---

*이 문서는 Agentic Orchestrator v0.4.0 "Signal Storm" 업그레이드 계획입니다.*
