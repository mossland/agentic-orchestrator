# Changelog

[한국어](CHANGELOG.ko.md) | **English**

All notable changes to the Mossland Agentic Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] "Bilingual" - 2026-01-24

### Added

#### Bilingual Content Support (EN/KO)
- **Bidirectional Translation**: ContentTranslator now detects source language and translates accordingly
  - Korean content → English (main field) + Korean (`*_ko` field)
  - English content → English (main field) + Korean translation (`*_ko` field)
- **Database Schema**: Added Korean fields to Ideas and Plans
  - `Idea`: `title_ko`, `summary_ko`, `description_ko`
  - `Plan`: `title_ko`, `final_plan_ko`
- **Frontend Localization**: UI respects EN/KO toggle for all content display
  - Ideas list, detail modal
  - Plans list, detail modal
  - Trends list, detail modal
- **Migration Script**: `migrate_bilingual.py` to backfill existing data with translations
- **IdeaContent Component**: Structured JSON idea display with sections:
  - Core Analysis with colored borders
  - Opportunity/Risk grid with visual indicators
  - Proposal with feature lists and tech stack badges
  - Roadmap timeline
  - KPIs with target metrics

### Fixed
- **TrendHeatmap Size**: Reduced cell height from `aspect-square` to `h-6` for better fit
- **AdapterDetailModal**: Fixed empty modal on first open - now auto-selects first adapter
- **Trend Analysis**: Changed LLM prompt to generate English-only content (Korean via translation)
- **Pipeline Modal**: Fixed VIEW ALL button for signals and trends stages

### Technical
- Added `ContentTranslator` class with `ensure_bilingual()`, `translate_to_english()`, `translate_to_korean()` methods
- Added `_detect_language()` helper for Korean/English detection
- Updated `_auto_score_and_save_ideas()` to use bilingual translation
- Added `getLocalizedText()` helper to frontend components
- Added `IdeaContent.tsx` component for structured JSON parsing and display
- Disabled signal translation for performance (signals are English-only)

---

## [0.5.0] - 2026-01-24

### Added

#### Enhanced Creativity Framework (Phase 1)
- **SCAMPER Creativity Prompts**: Divergence phase now uses structured SCAMPER techniques
  - Round 1: Substitute & Combine (replace components, merge concepts)
  - Round 2: Adapt & Modify (cross-industry inspiration, scale changes)
  - Round 3: Put to Other Use, Eliminate & Reverse (paradox thinking)
- **Lateral Thinking Prompts**: Alternating creativity techniques per round
  - Blue Sky Thinking (constraint-free imagination)
  - Paradox Approach (reverse problem solving)
  - Cross-Domain Innovation (industry pattern borrowing)
- **Higher Temperature**: Divergence temperature increased to 0.95 (from 0.9) for more creative outputs

#### Coingecko Market Adapter
- **Trending Coins**: Real-time search trend detection
- **Top Movers**: Top 5 gainers and losers (24h, >10% change threshold)
- **Volume Spikes**: Unusual trading activity detection (volume >50% of market cap)
- **Global Market Stats**: Total market cap changes, BTC dominance alerts
- **Tracked Coins**: 16 specific coins including MOC (Mossland)

#### Signal Time Decay
- **Freshness Weighting**: Signal scores now decay based on age
  - 0-1 hours: 100% weight
  - 1-6 hours: 90% weight
  - 6-12 hours: 80% weight
  - 12-24 hours: 60% weight
  - 24-48 hours: 40% weight
  - 48+ hours: 20% weight
- **Decay Logging**: Debug info shows decay distribution per analysis cycle

#### Dashboard UX Improvements
- **Skeleton Loaders**: Trends page and Ideas page now show proper loading skeletons
  - Trend cards with score, title, keywords placeholders
  - Pipeline view with stage indicators
  - List items with badge and content placeholders

### Changed
- Signal aggregator now includes Coingecko adapter by default
- Trend analysis applies time decay before processing signals

### Technical
- Added `SCAMPER_TECHNIQUES` and `LATERAL_THINKING` dictionaries to `DebateProtocol`
- Added `get_creativity_technique()` method to `DebateProtocol`
- Added `CoingeckoAdapter` class with trending, movers, global stats, tracked coins methods
- Added `_calculate_time_decay()` and `_apply_time_decay_to_signals()` functions to scheduler
- Added `TrendSkeleton`, `PipelineSkeleton`, `ListItemSkeleton`, `ListSkeleton` React components

---

## [0.4.2] - 2026-01-24

### Added

#### Idea Creativity & Diversity Improvements
- **Diversity-Aware Agent Selection**: Personality-axis balanced selection ensures diverse agent types in each debate round
- **Challenger Role Guarantee**: Each round now includes at least one challenger-type agent to prevent groupthink
- **Idea Similarity Feedback**: Agents receive Jaccard similarity scores and differentiation hints when generating ideas
- **Enhanced Novelty Weight**: Convergence phase now weights novelty at 30% (up from 20%) as the most important criterion

#### Signal Quality Improvements
- **Content Validation Layer**: Filters signals by minimum length, language (Korean/English), and spam patterns
- **Semantic Duplicate Removal**: Jaccard similarity-based deduplication removes semantically similar content from different sources
- **Engagement Thresholds**: Social adapters now filter low-engagement posts (Reddit: 10+ score, 3+ comments; Farcaster: 3+ likes or 1+ recast)
- **Sentiment Analysis**: Keyword-based sentiment detection (positive/negative/neutral) integrated into signal scoring

### Changed
- Signal deduplication now uses 3-phase approach: hash dedup → content validation → semantic dedup
- Convergence evaluation criteria restructured with explicit weighted scoring formula
- Twitter API search now filters tweets by engagement metrics

### Technical
- Added `_select_agents_with_diversity()`, `_ensure_challenger_presence()` methods to `MultiStageDebate`
- Added `_calculate_idea_similarity()`, `_get_similarity_feedback()` methods for differentiation hints
- Added `_validate_signal_content()`, `_is_semantic_duplicate()` methods to `SignalAggregator`
- Added `_analyze_sentiment()`, `_score_sentiment()` methods to `SignalScorer`
- Added `_meets_engagement_threshold()` methods to social adapters

---

## [0.4.1] - 2026-01-24

### Added

#### Expanded Signal Adapters (9 Adapters Total)
- **Twitter/X Adapter**: Nitter RSS pool with 10 instances, 20+ tracked accounts
- **Discord Adapter**: Bot API and webhook support, 7 tracked servers
- **Lens Protocol Adapter**: GraphQL API, 10 tracked profiles
- **Farcaster Adapter**: Neynar API, 10 tracked users and channels
- **OnChain Enhancements**: DEX volume, whale alerts, stablecoin flows via DefiLlama

#### Idea Quality Improvements
- **JSON Output Format**: Structured LLM responses for better parsing
- **Content Validation**: Required sections with minimum character counts
- **Title Quality Scoring**: 0-10 scale based on length, tech keywords, Mossland relevance

#### Dashboard UX Improvements
- **Adapter Detail Modal**: Click signals.conf to view detailed adapter info with health status
- **Skeleton Loading**: Activity feed now shows skeleton animation while loading
- **Real Activity Data**: `/activity` API returns actual DB data instead of mock timestamps

#### New API Endpoints
- `GET /adapters` - List all signal adapters with status, sources, and health info

### Changed
- Activity feed no longer uses mock data; displays real timestamps (HH:MM:SS format)
- Dashboard loads activity data with skeleton loading state

### Technical
- Added `AdapterInfo` type and `fetchAdapters()` API client method
- Added `isLoading` prop to `ActivityFeed` component

---

## [0.4.0] "Signal Storm" - 2026-01-22

### Added

#### Multi-Stage Debate System (34 Agents)
- **3 Debate Phases**: Divergence (12 agents) → Convergence (12 agents) → Planning (10 agents)
- **4-Axis Personality System**: Creativity, Analytical, Risk Tolerance, Collaboration (0-10 scale)
- **Debate Protocol**: `debate/protocol.py` - phases, message types, configuration
- **Multi-Stage Orchestration**: `debate/multi_stage.py` - complete debate flow management

#### Diverse Signal Sources (5 Adapters)
- **RSS Adapter**: 17 feeds across AI, Crypto, Finance, Security, Dev categories
- **GitHub Events Adapter**: Repository activity, trending projects, issue/PR analysis
- **On-Chain Adapter**: MOC token transactions, smart contract events, DeFi metrics
- **Social Media Adapter**: X (Twitter) mentions, community sentiment analysis
- **News API Adapter**: Real-time news aggregation, keyword-based filtering

#### Hybrid LLM Router
- **Local Models**: Ollama integration (Qwen 32B, Llama 3, Mistral)
- **Cloud APIs**: Claude, GPT-4, Gemini fallback
- **Intelligent Routing**: Automatic fallback between local and cloud
- **Budget Management**: Cost tracking and limits

#### PM2 Process Management
- **6 Services**: signals (30min), debate (6hr), backlog (daily), web, api, health (5min)
- **Scheduler Module**: `scheduler/tasks.py` - async task implementations
- **CLI Entry Point**: `scheduler/__main__.py` - command line interface
- **Ecosystem Config**: `ecosystem.config.js` - PM2 configuration

#### FastAPI Backend
- **REST API**: `/health`, `/status`, `/signals`, `/debates`, `/agents`, `/docs`
- **API Module**: `api/main.py` - FastAPI application
- **Port 3001**: Separate from web dashboard

#### CLI-Style Web Interface
- **Retro Terminal Theme**: JetBrains Mono font, scanlines, glow effects
- **Terminal Components**: `TerminalWindow.tsx`, status indicators
- **Agents Page**: `/agents` - displays all 34 agent personas
- **Mobile Responsive**: Adapted for all screen sizes

### Changed

- Dashboard redesigned with CLI/terminal aesthetic
- Navigation updated with `$` prompt style
- Footer updated with version "Signal Storm"
- Replaced GitHub Actions scheduling with PM2

### Removed

- `.github/workflows/backlog.yml` - replaced by PM2 moss-ao-backlog
- `.github/workflows/orchestrator.yml` - replaced by PM2 moss-ao-debate

### Technical Details

- Python 3.12 required for API server
- Virtual environment setup: `.venv/`
- Service names prefixed with `moss-ao-` to avoid conflicts

## [0.5.0] - 2026-01-05

### Added

#### Dashboard Website (`website/`)
- **Next.js 14 App Router**: Modern React framework with TypeScript and Tailwind CSS
- **4 Pages**: Dashboard, Trends, Backlog, System Architecture
- **Real-time Components**: Pipeline visualization, Activity feed, Statistics cards
- **i18n Support**: English/Korean language toggle (default: English)
- **Responsive Design**: Mobile-friendly with Framer Motion animations

#### Dashboard Features
- **Pipeline Visualization**: Ideas → Plans → Development flow with animated progress
- **Activity Feed**: Terminal-style real-time activity log
- **Statistics Cards**: Ideas, Plans, Rejected, In Development counts with animations
- **Trend Cards**: Expandable cards with GitHub links to trend data
- **Idea Cards**: Clickable cards linking directly to GitHub Issues
- **System Architecture**: Multi-agent debate system visualization

#### Components (`website/src/components/`)
- `Navigation.tsx` - Top navigation with LIVE indicator and language toggle
- `Footer.tsx` - Mossland branding with social links (X, Medium, GitHub, Email)
- `Pipeline.tsx` - Animated pipeline stage visualization
- `ActivityFeed.tsx` - Terminal-style scrolling activity log
- `Stats.tsx` - Counter-animated statistics cards
- `TrendCard.tsx` - Expandable trend cards with details
- `IdeaCard.tsx` - GitHub-linked idea cards
- `DebateVisualization.tsx` - 4-role × 3-AI debate system diagram
- `SystemStatus.tsx` - System status display

#### Build & Deployment
- **Build System**: Next.js 16.1.1 with Turbopack
- **Package Manager**: pnpm with workspace support
- **Static Export**: All pages pre-rendered as static content
- **Domain Ready**: Configured for https://ao.moss.land

### Technical Details

- TypeScript strict mode enabled
- Tailwind CSS with custom configuration
- Framer Motion for animations
- ESLint for code quality
- All 4 pages build successfully as static content

## [0.4.0] - 2026-01-04

### Added

#### Multi-Agent Debate System for PLAN Generation
- **4 Debate Roles**: Founder, VC (a16z/Sequoia level), Accelerator (YC/Techstars level), Founder Friend
- **3 AI Providers**: Claude, ChatGPT, Gemini rotate roles each round for diverse perspectives
- **Role Rotation**: Each round assigns different AI to different roles
- **Early Termination**: Debate ends when founder judges "Sufficiently Improved" or max 5 rounds
- **Discussion Records**: Full debate history saved as collapsible GitHub comments

#### Debate Module (`src/agentic_orchestrator/debate/`)
- `roles.py` - Role definitions with bilingual prompts (English + Korean)
- `moderator.py` - Round rotation matrix and termination logic
- `debate_session.py` - Full debate session orchestration
- `discussion_record.py` - GitHub comment formatting

#### Plan Rejection Workflow
- **`reject:plan` Label**: Reject a PLAN and regenerate from original idea
- **`ao backlog reject <plan_number>`**: CLI command to reject plans
- **Automatic Reset**: Rejected plan closes, original idea gets `promote:to-plan` restored

#### Bilingual Support
- All debate prompts in English with Korean translation request
- Discussion records display in "English / 한국어" format
- Plan extraction uses `[PLAN_START]`/`[PLAN_END]` markers for reliability

### Changed

- PlanGenerator now uses multi-agent debate when all 3 providers available
- Falls back to single-agent generation if providers unavailable
- Rejection processing runs before promotion processing in `run_cycle()`
- `_find_existing_plan_for_idea()` only searches open issues (ignores closed/rejected)

### Configuration

New `debate` section in `config.yaml`:
```yaml
debate:
  enabled: true
  max_rounds: 5
  min_rounds: 1
  require_all_approval: false
```

## [0.3.0] - 2026-01-04

### Added

#### Trend-Based Idea Generation
- **RSS Feed Integration**: Fetches articles from 17 RSS feeds across 5 categories (AI, Crypto, Finance, Security, Dev)
- **Trend Analysis**: Uses Claude to identify trending topics from news articles
- **Multi-Period Analysis**: Analyzes trends over 24 hours, 1 week, and 1 month periods
- **Trend-Based Ideas**: Generates Web3 micro-service ideas based on current trends
- **Trend Storage**: Stores trend analysis results as Markdown files with YAML frontmatter

#### New Trends Module
- `FeedFetcher` - RSS/Atom feed parsing with feedparser
- `TrendAnalyzer` - LLM-based trend extraction using Claude
- `TrendStorage` - Markdown file storage in `data/trends/YYYY/MM/`
- `TrendBasedIdeaGenerator` - Generates ideas from trending topics

#### New Labels
- `source:trend` - Tags ideas generated from trend analysis

#### New CLI Commands
- `ao backlog analyze-trends` - Fetch and analyze RSS feeds
- `ao backlog generate-trends` - Generate trend-based ideas
- `ao backlog trends-status` - Show trend analysis history

#### Updated CLI
- `ao backlog run` now supports `--trend-ideas` and `--analyze-trends` options
- `ao backlog status` shows trend-based idea count

#### GitHub Actions
- Schedule changed to 8 AM KST (23:00 UTC) daily
- New `run-with-trends` command (default daily run)
- Added `generate-trends`, `analyze-trends`, `trends-status` commands

### Changed

- Default daily run: 1 traditional idea + 2 trend-based ideas with trend analysis
- Trend data stored in `data/trends/` directory (90-day retention)

### Configuration

New `trends` section in `config.yaml`:
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

### Dependencies

- Added `feedparser>=6.0.0` for RSS/Atom parsing

## [0.2.1] - 2025-01-04

### Added

#### Stability Improvements
- **Idempotency Protection**: Prevents duplicate plan/dev creation by checking labels and existing artifacts
- **Lock Timeout Mechanism**: Detects and removes stale locks from crashed processes
- **Environment Validation**: Early validation of required environment variables with helpful error messages
- **Partial Failure Rollback**: Automatically closes plan issues if subsequent operations fail

#### New Tests
- 22 new tests for v0.2.1 features (idempotency, lock timeout, environment validation, rollback)
- Total test count increased from 83 to 105

### Changed

- Lock file now includes PID and timestamp for stale lock detection
- Config.get() now properly supports nested key lookups with defaults
- CLI commands validate environment before execution

### Technical Details

- Lock timeout defaults to 300 seconds (configurable via config.yaml)
- Process liveness check using signal 0
- Rollback adds `rollback:failed` label to closed issues

## [0.2.0] - 2025-01-03

### Added

#### Backlog-Based Workflow
- **GitHub Issues as UI/DB**: Ideas and plans are now stored as GitHub Issues
- **Human-in-the-Loop**: Label-based promotion system for stage transitions
- **GitHubClient**: Full GitHub API integration for Issues and Labels
- **BacklogOrchestrator**: New orchestrator for backlog-based workflow

#### Promotion System
- `promote:to-plan` label for promoting ideas to planning stage
- `promote:to-dev` label for promoting plans to development stage
- `processed:to-plan` and `processed:to-dev` labels for tracking
- Automatic label management after processing

#### New CLI Commands
- `ao backlog run`: Run full orchestration cycle
- `ao backlog generate`: Generate new idea issues
- `ao backlog process`: Process pending promotions
- `ao backlog status`: Show backlog status
- `ao backlog setup`: Set up required labels in repository

#### GitHub Integration
- Issue templates for ideas (`idea.yml`) and plans (`plan.yml`)
- Scheduled workflow (`backlog.yml`) for automated execution
- Labels documentation (`docs/labels.md`)

#### Concurrency Control
- File-based locking to prevent simultaneous runs
- Duplicate prevention via processed labels
- Safe for cron/scheduled execution

### Changed

- Workflow model changed from auto-progression to human-guided
- README.md rewritten for backlog-based workflow
- Updated `.env.example` with GitHub configuration variables

### Technical Details

- Uses `httpx` for async-capable HTTP client
- 83 unit tests passing
- Full dry-run support for testing

## [0.1.0] - 2025-01-03

### Added

#### Core Orchestrator
- State machine with stages: IDEATION → PLANNING_DRAFT → PLANNING_REVIEW → DEV → QA → DONE
- YAML-based state persistence (`.agent/state.yaml`)
- Iteration tracking with configurable limits for planning and development cycles
- Quality metrics tracking (review scores, test results)

#### LLM Provider Adapters
- **Claude Provider**: Supports both CLI mode (Claude Code) and API mode
- **OpenAI Provider**: GPT models for independent review (default: gpt-5.2-chat-latest)
- **Gemini Provider**: Fast agentic tasks (default: gemini-3-flash-preview)
- Automatic retry with exponential backoff for rate limits
- Fallback model support for all providers
- Quota exhaustion detection with proper error handling

#### Stage Handlers
- **Ideation**: Generates Web3 service ideas for Mossland ecosystem
- **Planning Draft**: Creates PRD, Architecture, Tasks, Acceptance Criteria
- **Planning Review**: External review using OpenAI/Gemini
- **Development**: Implements features using Claude Code
- **Quality Assurance**: Runs tests, code review, security checks
- **Done**: Creates completion report

#### CLI Commands
- `ao init`: Initialize new project
- `ao step`: Execute single pipeline step
- `ao loop`: Run in continuous mode with guardrails
- `ao status`: Show current status (supports --json)
- `ao resume`: Resume from paused state
- `ao reset`: Reset orchestrator state
- `ao push`: Push changes to remote

#### Error Handling
- Rate limit detection with automatic wait-and-retry
- Quota exhaustion alerts (`alerts/quota.md`)
- Sensitive data masking in logs and commits
- Maximum retry limits to prevent infinite loops

#### Infrastructure
- Prompt templates for all stages
- GitHub Actions CI workflow (test, lint)
- GitHub Actions orchestrator workflow (scheduled/manual)
- Comprehensive unit tests

### Configuration
- Environment variables via `.env`
- YAML configuration (`config.yaml`)
- Dry-run mode for testing
- Pinned model versions for reproducibility

## [Unreleased]

### Planned
- Enhanced smart contract development support
- Multi-project orchestration
- Web dashboard for monitoring
- Slack/Discord notifications
- Cost tracking and budget limits
