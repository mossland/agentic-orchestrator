# GitHub Labels Guide

This document describes the labels used in the Mossland Agentic Orchestrator workflow.

> **Note**: The current system is **DB-centric**. GitHub Issues and labels are used for visibility and tracking, but the primary data store is SQLite. The label-based promotion workflow described below is for reference and future implementation.

## Quick Reference

| Label | Purpose | Who Adds It | Status |
|-------|---------|-------------|--------|
| `type:idea` | Marks an idea issue | Orchestrator | Active |
| `type:plan` | Marks a planning issue | Orchestrator | Active |
| `status:backlog` | In backlog, awaiting action | Orchestrator | Active |
| `status:promoted` | High-scoring idea (>=7.0) | Orchestrator | Active |
| `status:archived` | Low-scoring idea (<4.0) | Orchestrator | Active |
| `generated:by-orchestrator` | Auto-generated content | Orchestrator | Active |
| `source:debate` | Generated from debate | Orchestrator | Active |
| `promote:to-plan` | Promote idea to planning | Human | *Future* |
| `promote:to-dev` | Start development from plan | Human | *Future* |

## Current Workflow (DB-Centric)

The current system uses SQLite as the primary data store. GitHub Issues are created for visibility but are not the source of truth.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIGNAL COLLECTION                            │
│                           ↓                                      │
│                     TREND ANALYSIS                               │
│                           ↓                                      │
│                   MULTI-STAGE DEBATE                             │
│                           ↓                                      │
│                     AUTO-SCORING                                 │
│          ┌────────────┼────────────┐                            │
│          ↓            ↓            ↓                            │
│     promoted      scored       archived                         │
│      (>=7.0)      (4-7)        (<4.0)                           │
│          │            │            │                            │
│          ↓            ↓            ↓                            │
│   ┌─────────────────────────────────────────┐                   │
│   │           SQLite DB (Primary)            │                   │
│   │              ideas table                 │                   │
│   │              plans table                 │                   │
│   └─────────────────────────────────────────┘                   │
│                           │                                      │
│                           ↓ (optional)                           │
│   ┌─────────────────────────────────────────┐                   │
│   │      GitHub Issues (For Visibility)      │                   │
│   │   Labels: type:idea, status:backlog      │                   │
│   └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Debate completes** → Ideas generated with scores
2. **Auto-Scorer evaluates** → Assigns status based on score
3. **DB storage** → Primary record in `ideas` table
4. **GitHub Issue created** (optional) → For visibility and tracking

### Status Mapping

| DB Status | GitHub Labels | Description |
|-----------|---------------|-------------|
| `promoted` | `type:idea`, `status:promoted` | High-quality idea, ready for planning |
| `scored` | `type:idea`, `status:backlog` | Medium-quality, needs review |
| `archived` | `type:idea`, `archived` | Low-quality, not pursued |
| `planned` | `type:plan`, `status:backlog` | Plan document exists |

## Label Categories

### Type Labels

These indicate what kind of issue it is:

- **`type:idea`** - An idea for a new micro Web3 service
  - Created by: Orchestrator (auto-generated from debates)
  - Contains: Idea summary, auto-score results, debate context

- **`type:plan`** - A detailed planning document
  - Created by: Orchestrator (when promoted idea gets a plan)
  - Contains: Full implementation plan with architecture, timeline, KPIs

### Status Labels

These track the current state of an issue:

- **`status:backlog`** - In the backlog, waiting for review
- **`status:promoted`** - High-scoring idea ready for planning
- **`status:archived`** - Low-scoring idea, not actively pursued

### Source Labels

These indicate where the content came from:

- **`source:debate`** - Generated from multi-agent debate
- **`source:trend`** - Generated from trend analysis
- **`generated:by-orchestrator`** - Auto-generated (all orchestrator content)

---

## Future Feature: Label-Based Promotion

> **Status**: Not yet implemented. The following describes the planned workflow.

### Promotion Labels (Human Action)

These labels will allow humans to trigger actions:

- **`promote:to-plan`** - Tell the orchestrator to create a detailed plan
  - Add to any `type:idea` issue you want to develop
  - Planned behavior:
    1. Generate a detailed planning document
    2. Create a new `type:plan` issue
    3. Update the idea with `status:planned`

- **`promote:to-dev`** - Tell the orchestrator to start development
  - Add to any `type:plan` issue you want to implement
  - Planned behavior:
    1. Create project scaffold in `projects/` directory
    2. Set up directory structure based on plan
    3. Generate initial boilerplate code
    4. Update the plan with `status:in-dev`

### Planned Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        IDEA BACKLOG                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:idea + status:backlog                              │  │
│  │  (Auto-generated by orchestrator from debates)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Human adds: promote:to-plan                  │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                        PLAN BACKLOG                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:plan + status:backlog                              │  │
│  │  (Generated from promoted idea)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Human adds: promote:to-dev                   │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                      IN DEVELOPMENT                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:plan + status:in-dev                               │  │
│  │  Project scaffold created in: projects/<project-name>/   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Development complete                         │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                          DONE                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  status:done                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setting Up Labels

Run this command to create all required labels in your repository:

```bash
# Using GitHub CLI
gh label create "type:idea" --color "0052CC" --description "An idea for a new service"
gh label create "type:plan" --color "5319E7" --description "A detailed planning document"
gh label create "status:backlog" --color "FBCA04" --description "In backlog, awaiting action"
gh label create "status:promoted" --color "0E8A16" --description "High-scoring idea"
gh label create "status:archived" --color "666666" --description "Archived, not pursued"
gh label create "source:debate" --color "C5DEF5" --description "Generated from debate"
gh label create "generated:by-orchestrator" --color "BFD4F2" --description "Auto-generated content"
```

## Label Colors

| Label | Color | Hex |
|-------|-------|-----|
| type:idea | Blue | `#0052CC` |
| type:plan | Purple | `#5319E7` |
| status:backlog | Yellow | `#FBCA04` |
| status:promoted | Green | `#0E8A16` |
| status:archived | Gray | `#666666` |
| source:debate | Light Blue | `#C5DEF5` |
| generated:by-orchestrator | Light Blue | `#BFD4F2` |

## Common Scenarios

### "I want to see what ideas were generated"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, status, score FROM ideas ORDER BY created_at DESC LIMIT 10"

# Via API
curl https://ao.moss.land/api/ideas

# Via GitHub
# Filter issues by label:type:idea
```

### "I want to see high-quality ideas"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, score FROM ideas WHERE status='promoted' ORDER BY score DESC"

# Via API
curl "https://ao.moss.land/api/ideas?status=promoted"

# Via GitHub
# Filter issues by label:status:promoted
```

### "I want to check plan details"

```bash
# Via API
curl https://ao.moss.land/api/plans/{plan_id}

# Via GitHub
# Look for issues with label:type:plan
```
