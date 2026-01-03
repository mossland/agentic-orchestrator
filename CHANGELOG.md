# Changelog

[한국어](CHANGELOG.ko.md) | **English**

All notable changes to the Mossland Agentic Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
