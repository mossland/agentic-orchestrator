# Mossland Agentic Orchestrator

An autonomous orchestration system for discovering, planning, and implementing micro Web3 services for the Mossland ecosystem.

## Key Features

- **Backlog-Based Workflow**: Ideas and plans are stored as GitHub Issues
- **Human-in-the-Loop**: Humans select which ideas to develop via label promotion
- **Multi-Agent Debate**: Plans are refined through debate between 4 AI roles (Founder, VC, Accelerator, Founder Friend)
- **Trend-Based Ideas**: Generates ideas from current news trends via RSS feeds
- **Autonomous Generation**: Orchestrator continuously generates ideas and processes promotions
- **No Auto-Progression**: Stages don't advance automatically - humans decide what to build

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    IDEA BACKLOG (GitHub Issues)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orchestrator generates ideas → stored as Issues         │  │
│  │  Labels: type:idea, status:backlog                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│              Human adds label: promote:to-plan                  │
│                             ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                    PLAN BACKLOG (GitHub Issues)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orchestrator generates detailed plan from promoted idea │  │
│  │  Labels: type:plan, status:backlog                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│              Human adds label: promote:to-dev                   │
│                             ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                    DEVELOPMENT (Repository)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orchestrator creates project scaffold                   │  │
│  │  Directory: projects/<project_id>/                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone and install
git clone https://github.com/mossland/agentic-orchestrator.git
cd agentic-orchestrator
python -m venv venv
source venv/bin/activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Set Up Labels

```bash
ao backlog setup
```

This creates all required labels in your GitHub repository.

### 3. Generate Ideas

```bash
# Generate 2 new ideas
ao backlog generate --count 2
```

Ideas will appear as GitHub Issues with labels `type:idea` and `status:backlog`.

### 4. Promote an Idea (Human Action)

On GitHub:
1. Go to the idea issue
2. Add the `promote:to-plan` label

### 5. Process Promotions

```bash
ao backlog process
```

The orchestrator will:
- Find issues with `promote:to-plan` label
- Generate detailed planning documents
- Create new `type:plan` issues
- Update original idea with `status:planned`

### 6. Start Development (Human Action)

On GitHub:
1. Go to the plan issue
2. Add the `promote:to-dev` label

Then run:
```bash
ao backlog process
```

The orchestrator will create a project scaffold in `projects/<id>/`.

## CLI Commands

### Backlog Commands (Recommended)

```bash
# Run full cycle: generate ideas + process promotions
ao backlog run

# Run with trend analysis (1 traditional + 2 trend-based ideas)
ao backlog run --ideas 1 --trend-ideas 2 --analyze-trends

# Generate traditional ideas only
ao backlog generate --count 2

# Generate trend-based ideas
ao backlog generate-trends --count 2

# Analyze trends only (no idea generation)
ao backlog analyze-trends

# Process promotions only (no idea generation)
ao backlog process

# Check backlog status
ao backlog status

# Check trend analysis history
ao backlog trends-status

# Set up labels in repository
ao backlog setup
```

### Options

```bash
# Dry run (no actual changes)
ao backlog run --dry-run

# Generate specific number of traditional ideas
ao backlog run --ideas 3

# Generate trend-based ideas
ao backlog run --trend-ideas 2 --analyze-trends

# Skip idea generation
ao backlog run --no-ideas

# Limit promotions processed
ao backlog run --max-promotions 3
```

## Promotion Workflow

### Promoting an Idea to Planning

1. **Find an idea** you want to develop in GitHub Issues
2. **Add the label** `promote:to-plan`
3. **Wait for orchestrator** to run (or run `ao backlog process`)
4. **Result**: A new `[PLAN]` issue is created with detailed PRD, architecture, and tasks

### Promoting a Plan to Development

1. **Review the plan** issue and ensure it's ready
2. **Add the label** `promote:to-dev`
3. **Wait for orchestrator** to run (or run `ao backlog process`)
4. **Result**: Project scaffold created in `projects/<id>/`

### Rejecting a Plan

If the generated plan is not satisfactory:
1. **Add the label** `reject:plan` to the plan issue
2. **Wait for orchestrator** to run (or run `ao backlog process`)
3. **Result**: Plan is closed, original idea gets `promote:to-plan` restored for regeneration

Or use CLI:
```bash
ao backlog reject 123  # Reject plan issue #123
```

## Multi-Agent Debate System

When all 3 AI providers (Claude, ChatGPT, Gemini) are available, plans are generated through a debate process:

### Debate Roles

| Role | Perspective | Provider Rotation |
|------|-------------|-------------------|
| **Founder** | Vision, conviction, action | Rotates each round |
| **VC** | Market, investment, scalability | Rotates each round |
| **Accelerator** | Execution, validation, MVP | Rotates each round |
| **Founder Friend** | Peer support, creative ideas | Same as Founder |

### Debate Flow

```
Round 1-5 (or until "Sufficiently Improved"):
  1. Founder presents/updates plan
  2. VC provides market/investment feedback
  3. Accelerator provides execution feedback
  4. Founder Friend provides peer perspective
  5. Founder reflects, adopts/rejects feedback, updates plan
  6. Check termination condition
```

### Output

- **PLAN Issue**: Contains final refined plan
- **Debate Record**: Full discussion history as collapsible comment
- **Bilingual**: All content in English with Korean translation

## Labels

| Label | Purpose | Added By |
|-------|---------|----------|
| `promote:to-plan` | **Promote idea to planning** | Human |
| `promote:to-dev` | **Start development** | Human |
| `reject:plan` | **Reject plan and regenerate** | Human |
| `type:idea` | Marks an idea issue | Orchestrator |
| `type:plan` | Marks a planning issue | Orchestrator |
| `status:backlog` | In backlog | Orchestrator |
| `status:planned` | Idea was planned | Orchestrator |
| `status:in-dev` | In development | Orchestrator |
| `source:trend` | Idea from trend analysis | Orchestrator |

See [docs/labels.md](docs/labels.md) for complete label documentation.

## Scheduled Operation

### GitHub Actions (Recommended)

The included workflow runs the orchestrator daily at 8 AM KST:

```yaml
# .github/workflows/backlog.yml
on:
  schedule:
    - cron: '0 23 * * *'  # Daily at 8 AM KST (23:00 UTC)
```

Default daily run generates:
- 1 traditional Mossland-focused idea
- 2 trend-based ideas from RSS feeds

### Cron Job

```bash
# Run daily at 8 AM KST (23:00 UTC)
0 23 * * * cd /path/to/repo && /path/to/venv/bin/ao backlog run --ideas 1 --trend-ideas 2 --analyze-trends >> logs/cron.log 2>&1
```

### Trend-Based Idea Generation

The orchestrator fetches articles from 17 RSS feeds across 5 categories:
- **AI**: OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News
- **Crypto**: CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate
- **Finance**: CNBC Finance
- **Security**: The Hacker News, Krebs on Security
- **Dev**: The Verge, Ars Technica, Stack Overflow Blog

Trend analysis results are stored in `data/trends/YYYY/MM/YYYY-MM-DD.md`.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **Yes** |
| `GITHUB_OWNER` | Repository owner | **Yes** |
| `GITHUB_REPO` | Repository name | **Yes** |
| `ANTHROPIC_API_KEY` | Claude API key | For API mode |
| `OPENAI_API_KEY` | OpenAI API key | For reviews |
| `GEMINI_API_KEY` | Gemini API key | For reviews |
| `DRY_RUN` | Run without changes | No |

### GitHub Token Permissions

Required scopes:
- `repo` - Full repository access (for Issues and Labels)

## Error Handling

### Rate Limiting (Claude)

- Automatically waits for rate limit reset
- Configurable max retries and wait time
- Logs all retry attempts

### Quota Exhaustion (OpenAI/Gemini)

- Creates alert in `alerts/quota.md`
- Logs provider, model, stage, and error
- Provides resolution steps
- Does NOT loop infinitely

### Concurrency Control

- Lock file prevents multiple simultaneous runs
- Safe for cron/scheduled execution

## Project Structure

```
agentic-orchestrator/
├── .agent/
│   └── orchestrator.lock    # Concurrency lock
├── .github/
│   ├── ISSUE_TEMPLATE/      # Idea and Plan templates
│   └── workflows/           # CI and scheduler
├── alerts/                  # Error/quota alerts
├── data/
│   └── trends/              # Trend analysis storage
│       └── YYYY/MM/         # Daily analysis files
├── docs/
│   └── labels.md            # Label documentation
├── projects/
│   └── <project_id>/        # Generated projects
│       ├── 01_ideation/
│       ├── 02_planning/
│       ├── 03_implementation/
│       └── 04_quality/
├── prompts/                 # Prompt templates
├── src/
│   └── agentic_orchestrator/
│       ├── backlog.py       # Backlog workflow
│       ├── cli.py           # CLI commands
│       ├── github_client.py # GitHub API
│       ├── orchestrator.py  # Legacy orchestrator
│       ├── providers/       # LLM adapters
│       ├── trends/          # Trend analysis module
│       ├── debate/          # Multi-agent debate system
│       └── utils/           # Utilities
└── tests/
```

## Idea Generation

### Traditional Ideas (Mossland-focused)
- **Micro Web3 services** - Small, achievable in 1-2 weeks
- **MOC token utility** - Enhance token value and usage
- **Ecosystem benefits** - Help Mossland community
- **Practical scope** - Avoid large platform development

### Trend-Based Ideas
- **Current trends** - Based on real-time news from RSS feeds
- **Web3 opportunities** - Identifies blockchain applications for trending topics
- **Timely relevance** - Capitalizes on hot topics while they're relevant
- **Cross-industry** - AI, crypto, security, dev trends

Examples:
- Token analytics dashboards
- Community governance tools
- NFT utility extensions
- AI agent integrations (from AI trends)
- DeFi protocol tools (from crypto trends)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Features

1. Modify `src/agentic_orchestrator/backlog.py` for workflow changes
2. Update CLI in `src/agentic_orchestrator/cli.py`
3. Add tests in `tests/`

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built for the Mossland ecosystem - human-guided, AI-powered innovation.*
