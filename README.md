# Mossland Agentic Orchestrator

[한국어](README.ko.md) | **English**

An autonomous multi-agent orchestration system for discovering, planning, and implementing micro Web3 services for the Mossland ecosystem.

**Version**: v0.5.1 "Bilingual"

## Key Features

- **Multi-Stage Debate**: 34 AI agents with diverse personas debate through 3 phases (Divergence → Convergence → Planning)
- **Diverse Signal Sources**: RSS, GitHub Events, On-Chain data, Social Media, News API
- **Hybrid LLM Routing**: Local Ollama models + Cloud API fallback with intelligent routing
- **Human-in-the-Loop**: Humans select which ideas to develop via label promotion
- **PM2 Scheduling**: Automated task scheduling with PM2 (signals, debates, backlog, health checks)
- **CLI-Style Dashboard**: Retro terminal-themed web interface at https://ao.moss.land
- **REST API**: FastAPI backend for programmatic access

## Dashboard

A Next.js-based CLI-style dashboard for monitoring the orchestrator in real-time.

**URL**: https://ao.moss.land

### Pages

| Page | Description |
|------|-------------|
| `/` | Dashboard with pipeline, activity feed, and statistics |
| `/trends` | Trend analysis results from signal sources |
| `/backlog` | Ideas and plans backlog with GitHub links |
| `/system` | System architecture and multi-agent debate visualization |
| `/agents` | 34 AI agent personas across 3 debate phases |

### Running Locally

```bash
cd website
pnpm install
pnpm dev
```

Open http://localhost:3000 to view the dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL COLLECTION                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │   RSS   │ │ GitHub  │ │On-Chain │ │ Social  │ │News API │           │
│  │ Adapter │ │ Events  │ │ Adapter │ │ Media   │ │ Adapter │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┼───────────┴───────────┘                 │
│                               ▼                                          │
│                    ┌──────────────────┐                                  │
│                    │ Signal Aggregator │                                  │
│                    │   + Scorer        │                                  │
│                    └────────┬─────────┘                                  │
├─────────────────────────────┼───────────────────────────────────────────┤
│                             ▼                                            │
│                  MULTI-STAGE DEBATE (34 Agents)                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Phase 1: DIVERGENCE (12 agents)                                 │     │
│  │   Innovator, Skeptic, Pragmatist, Visionary...                 │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ Phase 2: CONVERGENCE (12 agents)                                │     │
│  │   Synthesizer, Evaluator, Prioritizer, Risk Assessor...        │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ Phase 3: PLANNING (10 agents)                                   │     │
│  │   Architect, Project Manager, Technical Lead...                │     │
│  └────────────────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────────┤
│                         HYBRID LLM ROUTER                                │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │   Local (Ollama)    │ ←→  │   Cloud API         │                    │
│  │   - Qwen 32B        │     │   - Claude          │                    │
│  │   - Llama 3         │     │   - GPT-4           │                    │
│  │   - Mistral         │     │   - Gemini          │                    │
│  └─────────────────────┘     └─────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone and install
git clone https://github.com/MosslandOpenDevs/agentic-orchestrator.git
cd agentic-orchestrator

# Create Python virtual environment (Python 3.12 required)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install uvicorn fastapi pyyaml

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services with PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start all services
pm2 start ecosystem.config.js

# Or start specific services
pm2 start ecosystem.config.js --only moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-api
```

### 3. Access the Dashboard

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:3001/docs

## PM2 Services

| Service | Schedule | Description |
|---------|----------|-------------|
| `moss-ao-signals` | Every 30 min | Collect signals from all adapters |
| `moss-ao-debate` | Every 6 hours | Run multi-stage AI debate |
| `moss-ao-backlog` | Daily at midnight | Process pending backlog items |
| `moss-ao-web` | Always on | Next.js dashboard (port 3000) |
| `moss-ao-api` | Always on | FastAPI backend (port 3001) |
| `moss-ao-health` | Every 5 min | System health monitoring |

### PM2 Commands

```bash
# View all services
pm2 status

# View logs
pm2 logs moss-ao-web
pm2 logs moss-ao-api

# Restart a service
pm2 restart moss-ao-web

# Stop all services
pm2 stop all

# Monitor resources
pm2 monit
```

## API Endpoints

The FastAPI backend provides REST API access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/signals` | GET | List recent signals |
| `/debates` | GET | List debate results |
| `/agents` | GET | List agent personas |
| `/docs` | GET | Swagger documentation |

## Multi-Stage Debate System

### Phase 1: Divergence (12 Agents)
Generate diverse ideas and perspectives:
- **Innovator**: Creative breakthrough ideas
- **Skeptic**: Critical analysis and risk identification
- **Pragmatist**: Practical implementation focus
- **Visionary**: Long-term strategic thinking
- And 8 more specialized agents...

### Phase 2: Convergence (12 Agents)
Synthesize and evaluate ideas:
- **Synthesizer**: Combine related ideas
- **Evaluator**: Score and rank proposals
- **Prioritizer**: Determine execution order
- **Risk Assessor**: Identify potential issues
- And 8 more specialized agents...

### Phase 3: Planning (10 Agents)
Create actionable implementation plans:
- **Architect**: System design
- **Project Manager**: Task breakdown
- **Technical Lead**: Technology decisions
- **Resource Planner**: Resource allocation
- And 6 more specialized agents...

### Agent Personality System

Each agent has a 4-axis personality profile:
- **Creativity**: Innovation vs. Convention (0-10)
- **Analytical**: Data-driven vs. Intuitive (0-10)
- **Risk Tolerance**: Aggressive vs. Conservative (0-10)
- **Collaboration**: Team-oriented vs. Independent (0-10)

## Signal Sources

### RSS Feeds
17 feeds across 5 categories:
- **AI**: OpenAI, Google AI, arXiv, TechCrunch, Hacker News
- **Crypto**: CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate
- **Finance**: CNBC Finance
- **Security**: The Hacker News, Krebs on Security
- **Dev**: The Verge, Ars Technica, Stack Overflow Blog

### GitHub Events
- Repository activity tracking
- Trending projects monitoring
- Issue and PR analysis

### On-Chain Data
- MOC token transactions
- Smart contract events
- DeFi protocol metrics

### Social Media
- X (Twitter) mentions
- Community sentiment analysis

### News API
- Real-time news aggregation
- Keyword-based filtering

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **Yes** |
| `GITHUB_OWNER` | Repository owner | **Yes** |
| `GITHUB_REPO` | Repository name | **Yes** |
| `ANTHROPIC_API_KEY` | Claude API key | For cloud mode |
| `OPENAI_API_KEY` | OpenAI API key | For cloud mode |
| `GEMINI_API_KEY` | Gemini API key | For cloud mode |
| `OLLAMA_HOST` | Ollama server URL | For local mode |

## Project Structure

```
agentic-orchestrator/
├── ecosystem.config.js      # PM2 configuration
├── .venv/                   # Python virtual environment
├── src/agentic_orchestrator/
│   ├── adapters/            # Signal source adapters
│   │   ├── rss.py
│   │   ├── github_events.py
│   │   ├── onchain.py
│   │   ├── social_media.py
│   │   └── news_api.py
│   ├── api/                 # FastAPI backend
│   │   └── main.py
│   ├── cache/               # Caching layer
│   ├── db/                  # Database models & repositories
│   ├── debate/              # Multi-stage debate system
│   │   ├── protocol.py
│   │   └── multi_stage.py
│   ├── llm/                 # LLM routing
│   │   └── router.py
│   ├── personas/            # 34 agent definitions
│   ├── providers/           # LLM providers (Ollama, APIs)
│   ├── scheduler/           # PM2 task implementations
│   │   ├── __main__.py
│   │   └── tasks.py
│   └── signals/             # Signal processing
├── website/                 # Next.js dashboard
│   ├── src/
│   │   ├── app/             # Pages
│   │   └── components/      # React components
│   └── package.json
└── logs/                    # PM2 log files
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Building the Website

```bash
cd website
pnpm build
```

### Manual Task Execution

```bash
# Signal collection
python -m agentic_orchestrator.scheduler signal-collect

# Run debate
python -m agentic_orchestrator.scheduler run-debate

# Process backlog
python -m agentic_orchestrator.scheduler process-backlog

# Health check
python -m agentic_orchestrator.scheduler health-check
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built for the Mossland ecosystem - human-guided, AI-powered innovation.*

*v0.5.1 "Bilingual" - Multi-agent orchestration with bilingual content support*
