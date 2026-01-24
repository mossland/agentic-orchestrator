"""
FastAPI main application for Mossland Agentic Orchestrator API.

Endpoints:
- GET /health - System health status
- GET /status - Overall system status
- GET /signals - Recent signals
- GET /debates - Recent debate results
- GET /trends - Trend analysis results
- GET /ideas - Ideas list
- GET /plans - Plans list
- GET /usage - API usage statistics
- GET /agents - Agent personas information
"""

from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.connection import get_db, Database
from ..db.repositories import (
    SignalRepository,
    TrendRepository,
    IdeaRepository,
    DebateRepository,
    PlanRepository,
    APIUsageRepository,
    SystemLogRepository,
)


app = FastAPI(
    title="MOSS.AO API",
    description="Mossland Agentic Orchestrator API",
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def get_session():
    """Dependency to get a database session."""
    db = get_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class StatusResponse(BaseModel):
    status: str
    timestamp: str
    components: dict
    stats: dict


class SignalResponse(BaseModel):
    id: str
    source: str
    title: str
    summary: Optional[str]
    score: float
    created_at: str


class DebateResponse(BaseModel):
    id: str
    topic: str
    phase: str
    ideas_count: int
    created_at: str


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    phase: str
    personality: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.5.0",
    )


@app.get("/status", response_model=StatusResponse)
async def system_status(session: Session = Depends(get_session)):
    """Get overall system status with real statistics."""
    from ..db.models import Signal, DebateSession, Idea, Plan
    from sqlalchemy import func
    from datetime import timedelta

    # Calculate real stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    signals_today = session.query(func.count(Signal.id)).filter(
        Signal.collected_at >= today
    ).scalar() or 0

    debates_today = session.query(func.count(DebateSession.id)).filter(
        DebateSession.started_at >= today
    ).scalar() or 0

    total_ideas = session.query(func.count(Idea.id)).scalar() or 0
    total_plans = session.query(func.count(Plan.id)).scalar() or 0

    # Check database health
    db = get_db()
    db_healthy = db.health_check()

    return StatusResponse(
        status="operational" if db_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        components={
            "api": {"status": "healthy"},
            "database": {"status": "healthy" if db_healthy else "unhealthy"},
            "cache": {"status": "healthy"},
            "llm_router": {"status": "healthy"},
        },
        stats={
            "signals_today": signals_today,
            "debates_today": debates_today,
            "ideas_generated": total_ideas,
            "plans_created": total_plans,
            "agents_active": 34,
        },
    )


@app.get("/signals")
async def get_signals(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    source: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[float] = Query(default=0.0, ge=0.0),
    hours: int = Query(default=24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Get recent signals with filtering and pagination."""
    repo = SignalRepository(session)

    # Get signals with filters
    signals = repo.get_recent(
        hours=hours,
        limit=limit + offset,  # Get extra for offset handling
        source=source,
        category=category,
        min_score=min_score,
    )

    # Apply offset manually (simple pagination)
    paginated = signals[offset:offset + limit]

    # Get total count for pagination info
    total = len(signals)

    return {
        "signals": [s.to_dict() for s in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/debates")
async def get_debates(
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    phase: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get recent debate sessions with filtering."""
    repo = DebateRepository(session)

    # Get sessions based on filters
    if status == "active":
        sessions = repo.get_active_sessions()
    elif phase:
        sessions = repo.get_sessions_by_phase(phase)
    else:
        # Get all sessions - query directly for all sessions ordered by date
        from ..db.models import DebateSession
        from sqlalchemy import desc
        sessions = (
            session.query(DebateSession)
            .order_by(desc(DebateSession.started_at))
            .all()
        )

    # Apply pagination
    total = len(sessions)
    paginated = sessions[offset:offset + limit]

    # Build response with message counts
    debates = []
    for debate in paginated:
        debate_dict = debate.to_dict()
        debate_dict["message_count"] = len(debate.messages) if debate.messages else 0
        debates.append(debate_dict)

    return {
        "debates": debates,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/debates/{session_id}")
async def get_debate_detail(
    session_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed debate session with messages."""
    repo = DebateRepository(session)

    debate = repo.get_session_by_id(session_id)
    if not debate:
        return {"error": "Debate session not found", "session_id": session_id}

    messages = repo.get_session_messages(session_id)

    return {
        "debate": debate.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "message_count": len(messages),
    }


@app.get("/trends")
async def get_trends(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    period: Optional[str] = Query(default="all", pattern="^(all|24h|7d|30d)$"),
    category: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get trend analysis results."""
    repo = TrendRepository(session)

    if category:
        trends = repo.get_by_category(category, limit=limit + offset)
        total = len(trends)
    elif period == "all":
        trends = repo.get_all(limit=limit + offset)
        total = repo.count_all()
    else:
        trends = repo.get_latest(period=period, limit=limit + offset)
        total = len(trends)

    # Apply offset
    paginated = trends[offset:offset + limit]

    return {
        "trends": [t.to_dict() for t in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
        "period": period,
    }


@app.get("/ideas")
async def get_ideas(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get ideas list with filtering."""
    repo = IdeaRepository(session)

    # Get status counts for summary and total count
    status_counts = repo.count_by_status()

    if status:
        ideas = repo.get_by_status(status, limit=limit + offset)
        total = status_counts.get(status, 0)
    else:
        ideas = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()

    paginated = ideas if status is None else ideas[offset:offset + limit]

    return {
        "ideas": [i.to_dict() for i in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
        "status_counts": status_counts,
    }


@app.get("/ideas/{idea_id}")
async def get_idea_detail(
    idea_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed idea information with related debates and plans.

    Returns full description and debate messages for the source debate session.
    """
    idea_repo = IdeaRepository(session)
    debate_repo = DebateRepository(session)
    plan_repo = PlanRepository(session)

    idea = idea_repo.get_by_id(idea_id)
    if not idea:
        return {"error": "Idea not found", "idea_id": idea_id}

    # Get source debate session (via FK or metadata for backward compatibility)
    source_debate_id = idea.debate_session_id
    if not source_debate_id and idea.extra_metadata:
        source_debate_id = idea.extra_metadata.get('debate_session_id')

    debates = []
    seen_ids = set()

    # Add source debate with messages first
    if source_debate_id:
        source_debate = debate_repo.get_session_by_id(source_debate_id)
        if source_debate:
            messages = debate_repo.get_session_messages(source_debate_id)
            debate_dict = source_debate.to_dict()
            debate_dict['messages'] = [m.to_dict() for m in messages]
            debates.append(debate_dict)
            seen_ids.add(source_debate_id)

    # Also get any debates linked via idea_id (backward compatibility)
    linked_debates = debate_repo.get_sessions_by_idea(idea_id)
    for d in linked_debates:
        if d.id not in seen_ids:
            messages = debate_repo.get_session_messages(d.id)
            debate_dict = d.to_dict()
            debate_dict['messages'] = [m.to_dict() for m in messages]
            debates.append(debate_dict)
            seen_ids.add(d.id)

    plans = plan_repo.get_by_idea(idea_id)

    return {
        "idea": idea.to_dict(),
        "debates": debates,
        "plans": [p.to_dict() for p in plans],
    }


@app.get("/plans")
async def get_plans(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get plans list with filtering."""
    repo = PlanRepository(session)

    if status:
        plans = repo.get_by_status(status, limit=limit + offset)
        total = repo.count_by_status(status)
        paginated = plans[offset:offset + limit]
    else:
        plans = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()
        paginated = plans

    return {
        "plans": [p.to_dict() for p in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/plans/{plan_id}")
async def get_plan_detail(
    plan_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed plan information."""
    repo = PlanRepository(session)

    plan = repo.get_by_id(plan_id)
    if not plan:
        return {"error": "Plan not found", "plan_id": plan_id}

    # Include full plan content
    return {
        "id": plan.id,
        "idea_id": plan.idea_id,
        "title": plan.title,
        "version": plan.version,
        "status": plan.status,
        "prd_content": plan.prd_content,
        "architecture_content": plan.architecture_content,
        "user_research_content": plan.user_research_content,
        "business_model_content": plan.business_model_content,
        "project_plan_content": plan.project_plan_content,
        "final_plan": plan.final_plan,
        "github_issue_url": plan.github_issue_url,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@app.get("/usage")
async def get_usage(
    days: int = Query(default=7, ge=1, le=90),
    session: Session = Depends(get_session),
):
    """Get API usage statistics."""
    repo = APIUsageRepository(session)

    today_usage = repo.get_today_usage()
    today_by_provider = repo.get_today_by_provider()
    month_total = repo.get_month_total()
    history = repo.get_usage_history(days=days)

    return {
        "today": today_usage,
        "today_by_provider": today_by_provider,
        "month_total": month_total,
        "history": history,
        "days": days,
    }


@app.get("/activity")
async def get_activity(
    limit: int = Query(default=20, le=100),
    session: Session = Depends(get_session),
):
    """Get recent system activity for the activity feed."""
    log_repo = SystemLogRepository(session)

    logs = log_repo.get_recent(limit=limit)

    activities = []
    for log in logs:
        activities.append({
            "time": log.created_at.strftime("%H:%M") if log.created_at else "",
            "type": log.source,
            "message": log.message,
            "level": log.level,
        })

    return {
        "activities": activities,
        "total": len(activities),
    }


@app.get("/agents")
async def get_agents(phase: Optional[str] = None):
    """Get agent personas information."""
    from ..personas import get_divergence_agents, get_convergence_agents, get_planning_agents

    def agent_to_dict(agent, phase_name: str) -> dict:
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "phase": phase_name,
            "handle": agent.handle,
            "expertise": agent.expertise,
            "personality": {
                "thinking": agent.personality.thinking.value,
                "decision": agent.personality.decision.value,
                "communication": agent.personality.communication.value,
                "action": agent.personality.action.value,
            },
        }

    agents = []

    if phase is None or phase == "divergence":
        for agent in get_divergence_agents():
            agents.append(agent_to_dict(agent, "divergence"))

    if phase is None or phase == "convergence":
        for agent in get_convergence_agents():
            agents.append(agent_to_dict(agent, "convergence"))

    if phase is None or phase == "planning":
        for agent in get_planning_agents():
            agents.append(agent_to_dict(agent, "planning"))

    return {
        "agents": agents,
        "total": len(agents),
    }


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "MOSS.AO API",
        "version": "0.5.0",
        "description": "Mossland Agentic Orchestrator API",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "signals": "/signals",
            "trends": "/trends",
            "ideas": "/ideas",
            "plans": "/plans",
            "debates": "/debates",
            "usage": "/usage",
            "activity": "/activity",
            "agents": "/agents",
            "docs": "/docs",
        },
    }
