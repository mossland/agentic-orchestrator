# Changelog

[한국어](CHANGELOG.ko.md) | **English**

All notable changes to the Mossland Agentic Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
