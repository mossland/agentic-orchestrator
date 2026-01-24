# MOSS.AO Dashboard

CLI-style retro terminal dashboard for the Mossland Agentic Orchestrator.

**Version**: v0.5.1 "Bilingual"

## Features

- **Terminal Aesthetic**: JetBrains Mono font, scanlines, glow effects
- **Real-time Monitoring**: Pipeline status, activity feed, statistics
- **Agent Personas**: View all 34 AI agents across 3 debate phases
- **Mobile Responsive**: Optimized for all screen sizes

## Pages

| Page | Description |
|------|-------------|
| `/` | Dashboard with pipeline, activity feed, and statistics |
| `/trends` | Trend analysis results from signal sources |
| `/backlog` | Ideas and plans backlog with GitHub links |
| `/system` | System architecture and multi-agent debate visualization |
| `/agents` | 34 AI agent personas across 3 debate phases |

## Getting Started

### Development

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### Production Build

```bash
pnpm build
pnpm start
```

### With PM2

```bash
# From project root
pm2 start ecosystem.config.js --only moss-ao-web
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Font**: JetBrains Mono

## Components

| Component | Description |
|-----------|-------------|
| `Navigation.tsx` | Top nav with `$` prompt style |
| `Footer.tsx` | Mossland branding with social links |
| `Pipeline.tsx` | Ideas → Plans → Dev flow visualization |
| `ActivityFeed.tsx` | Terminal-style scrolling log |
| `Stats.tsx` | Animated statistics cards |
| `SystemStatus.tsx` | System health indicators |
| `TerminalWindow.tsx` | Reusable terminal window component |

## Environment

The dashboard connects to the FastAPI backend on port 3001:

- **Frontend**: http://localhost:3000
- **API**: http://localhost:3001

## Deployment

Deployed via nginx reverse proxy:

- **URL**: https://ao.moss.land
- **API**: https://ao.moss.land/api/

## License

MIT License
