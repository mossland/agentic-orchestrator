# Mossland Agentic Orchestrator

An autonomous orchestration system that performs the complete software development lifecycle without human intervention:
**Idea Discovery → Detailed Planning → Development → Testing/Evaluation → Feedback Integration**

## Overview

This orchestrator automatically discovers, plans, implements, and validates micro Web3 services that benefit the Mossland ecosystem. It operates as a state machine that progresses through defined stages, using multiple AI models for different tasks:

- **Claude (Opus/Sonnet)**: Primary development and planning tasks
- **OpenAI GPT**: Independent code review and evaluation
- **Google Gemini**: Fast agentic tasks and secondary review

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agentic Orchestrator                         │
├─────────────────────────────────────────────────────────────────┤
│  State Machine (.agent/state.yaml)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────┐  ┌────┐      │
│  │ IDEATION │→ │ PLANNING │→ │   DEV    │→ │ QA │→ │DONE│      │
│  └──────────┘  └──────────┘  └──────────┘  └────┘  └────┘      │
│       ↑              ↓              ↓         ↓                 │
│       └──────────────┴──────────────┴─────────┘                 │
│                    (iteration loops)                            │
├─────────────────────────────────────────────────────────────────┤
│  LLM Providers                                                  │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐                  │
│  │   Claude   │  │  OpenAI  │  │   Gemini   │                  │
│  │ (Dev/Plan) │  │ (Review) │  │  (Review)  │                  │
│  └────────────┘  └──────────┘  └────────────┘                  │
├─────────────────────────────────────────────────────────────────┤
│  Output: projects/<id>/                                         │
│  ├── 01_ideation/   (idea documents)                           │
│  ├── 02_planning/   (PRD, architecture, tasks)                 │
│  ├── 03_implementation/ (source code)                          │
│  └── 04_quality/    (reviews, test results)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Stage Flow

| Stage | Description | Output |
|-------|-------------|--------|
| `IDEATION` | Generate micro Web3 service ideas for Mossland | `01_ideation/*.md` |
| `PLANNING_DRAFT` | Create detailed PRD, architecture, task breakdown | `02_planning/*.md` |
| `PLANNING_REVIEW` | External review (GPT/Gemini), iterate if needed | `02_planning/review_*.md` |
| `DEV` | Implement the planned features using Claude Code | `03_implementation/*` |
| `QA` | Run tests, external code review, quality checks | `04_quality/*.md` |
| `DONE` | Project complete, ready for next idea | Final commit |
| `PAUSED_QUOTA` | Paused due to API quota issues | `alerts/quota.md` |

## Installation

### Prerequisites

- Python 3.10+
- [Claude Code](https://claude.ai/code) installed and authenticated
- API keys for OpenAI and Google Gemini (optional, for review features)

### Setup

```bash
# Clone the repository
git clone https://github.com/mossland/agentic-orchestrator.git
cd agentic-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Keep Claude Code Updated

```bash
# Update Claude Code to the latest version
claude update
```

## Usage

### CLI Commands

```bash
# Initialize a new project
ao init

# Run a single step (advances state machine by one stage)
ao step

# Run in loop mode (continuous execution with guardrails)
ao loop

# Check current status
ao status

# Dry run mode (no API calls, for testing)
ao step --dry-run
```

### Running Options

#### 1. Manual Execution
```bash
# Run one step at a time
ao step
```

#### 2. Continuous Loop
```bash
# Run until completion or limit reached
ao loop --max-steps 50
```

#### 3. Cron Job (Unattended)
```bash
# Add to crontab (runs every hour)
0 * * * * cd /path/to/agentic-orchestrator && /path/to/venv/bin/ao step >> logs/cron.log 2>&1
```

#### 4. GitHub Actions Schedule
See `.github/workflows/orchestrator.yml` for scheduled execution setup.

## Configuration

### Model Configuration

Models can be configured via environment variables or `config.yaml`:

```yaml
# config.yaml
models:
  claude:
    default: opus
    fallback: sonnet
  openai:
    default: gpt-5.2-chat-latest
    fallback: gpt-5.2
    pinned: null  # Set for reproducibility
  gemini:
    default: gemini-3-flash-preview
    fallback: gemini-3-pro-preview
    pinned: null

limits:
  planning_max_iterations: 3
  dev_max_iterations: 5
  rate_limit_max_retries: 5
  rate_limit_max_wait_seconds: 3600
```

### State File Structure

`.agent/state.yaml`:
```yaml
stage: PLANNING_DRAFT
project_id: web3-token-tracker
iteration:
  planning: 1
  dev: 0
limits:
  planning_max: 3
  dev_max: 5
quality:
  review_score: null
  tests_passed: null
  required_score: 7.0
last_updated: 2025-01-03T10:00:00Z
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | For API mode |
| `OPENAI_API_KEY` | OpenAI API key for GPT review | Optional |
| `GEMINI_API_KEY` | Google Gemini API key | Optional |
| `GITHUB_TOKEN` | GitHub PAT for pushing commits | For auto-push |
| `CLAUDE_MODEL` | Default Claude model (opus/sonnet) | No |
| `DRY_RUN` | Run without API calls | No |

See `.env.example` for full list.

## Error Handling

### Rate Limiting (Claude/Anthropic)
- Automatically waits for rate limit reset
- Logs wait time and retries
- Maximum retry limit prevents infinite loops

### Quota Exhaustion (OpenAI/Gemini)
- Creates detailed alert in `alerts/quota.md`
- Sets state to `PAUSED_QUOTA`
- Documents required actions for resolution
- Does NOT loop infinitely - exits gracefully

## Commit Convention

All commits follow this format:

```
[stage] brief description

- Detailed change 1
- Detailed change 2

Generated by: Agentic Orchestrator
Stage: PLANNING_DRAFT
Project: web3-token-tracker
Iteration: planning=2, dev=0
```

Prefixes:
- `[ideation]` - Idea generation outputs
- `[planning]` - Planning documents
- `[review]` - Review results
- `[dev]` - Implementation code
- `[qa]` - Quality assurance results
- `[system]` - Orchestrator system changes

## Project Structure

```
agentic-orchestrator/
├── .agent/
│   ├── state.yaml         # Current state machine state
│   └── prompts/           # Stage-specific prompts
├── projects/
│   └── <project_id>/
│       ├── 01_ideation/
│       ├── 02_planning/
│       ├── 03_implementation/
│       └── 04_quality/
├── prompts/                # Prompt templates
├── src/
│   └── agentic_orchestrator/
│       ├── __init__.py
│       ├── cli.py          # CLI entry points
│       ├── orchestrator.py # Main orchestrator logic
│       ├── stages/         # Stage implementations
│       ├── providers/      # LLM provider adapters
│       └── utils/          # Utilities
├── tests/                  # Unit tests
├── alerts/                 # Quota/error alerts
├── .env.example
├── config.yaml
├── pyproject.toml
└── README.md
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Adding a New Stage
1. Create handler in `src/agentic_orchestrator/stages/`
2. Register in stage registry
3. Update state machine transitions
4. Add corresponding prompts

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

This project is designed for autonomous operation, but contributions to improve the orchestrator itself are welcome. Please submit issues and pull requests to the GitHub repository.

---

*Built for the Mossland ecosystem - autonomous innovation through AI orchestration.*
