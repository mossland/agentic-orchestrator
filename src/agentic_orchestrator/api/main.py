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


@app.get("/ideas/{idea_id}/lineage")
async def get_idea_lineage(
    idea_id: str,
    session: Session = Depends(get_session),
):
    """Get complete lineage for an idea showing signals → trend → idea → plans flow.

    Returns source signals, parent trend (if any), the idea, and generated plans.
    """
    from ..db.models import Signal, Trend

    idea_repo = IdeaRepository(session)
    plan_repo = PlanRepository(session)

    idea = idea_repo.get_by_id(idea_id)
    if not idea:
        return {"error": "Idea not found", "idea_id": idea_id}

    # Get related signals based on idea metadata or source
    signals = []
    trend = None

    # Check if idea has source trend info in metadata
    trend_id = None
    if idea.extra_metadata:
        trend_id = idea.extra_metadata.get('trend_id')
        source_signal_ids = idea.extra_metadata.get('source_signal_ids', [])

        # Fetch source signals if IDs are stored
        if source_signal_ids:
            for signal_id in source_signal_ids[:10]:  # Limit to 10
                signal = session.query(Signal).filter(Signal.id == signal_id).first()
                if signal:
                    signals.append({
                        "id": signal.id,
                        "title": signal.title,
                        "score": signal.score,
                        "source": signal.source,
                    })

    # If we have a trend_id, fetch the trend
    if trend_id:
        trend_obj = session.query(Trend).filter(Trend.id == trend_id).first()
        if trend_obj:
            trend = {
                "id": trend_obj.id,
                "name": trend_obj.name,
                "score": trend_obj.score,
                "signal_count": trend_obj.signal_count,
            }

    # If no signals found yet, try to find related signals by keywords/title
    if not signals:
        # Search for signals with similar keywords
        keywords = []
        if idea.extra_metadata and idea.extra_metadata.get('keywords'):
            keywords = idea.extra_metadata.get('keywords', [])[:5]

        if keywords:
            from sqlalchemy import or_, func
            keyword_filters = [Signal.title.ilike(f'%{kw}%') for kw in keywords]
            related_signals = (
                session.query(Signal)
                .filter(or_(*keyword_filters))
                .order_by(Signal.score.desc())
                .limit(5)
                .all()
            )
            for signal in related_signals:
                signals.append({
                    "id": signal.id,
                    "title": signal.title,
                    "score": signal.score,
                    "source": signal.source,
                })

    # If still no trend found, try to find by name similarity
    if not trend and idea.title:
        from sqlalchemy import func
        # Simple search by title words
        words = idea.title.split()[:3]
        for word in words:
            if len(word) > 4:  # Skip short words
                found_trend = (
                    session.query(Trend)
                    .filter(Trend.name.ilike(f'%{word}%'))
                    .order_by(Trend.score.desc())
                    .first()
                )
                if found_trend:
                    trend = {
                        "id": found_trend.id,
                        "name": found_trend.name,
                        "score": found_trend.score,
                        "signal_count": found_trend.signal_count,
                    }
                    break

    # Get plans
    plans = plan_repo.get_by_idea(idea_id)

    return {
        "signals": signals,
        "trend": trend,
        "idea": {
            "id": idea.id,
            "title": idea.title,
            "score": idea.score,
            "status": idea.status,
        },
        "plans": [
            {
                "id": p.id,
                "title": p.title,
                "version": p.version,
                "status": p.status,
            }
            for p in plans
        ],
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
    """Get recent system activity for the activity feed.

    Generates activity from real data tables (signals, trends, ideas, debates, plans)
    instead of relying on explicit system logs.
    """
    from ..db.models import Signal, Trend, Idea, DebateSession, Plan
    from sqlalchemy import desc, union_all, literal

    activities = []

    # Get recent signals (last 24 hours, limit to avoid too many)
    recent_signals = (
        session.query(Signal)
        .filter(Signal.collected_at.isnot(None))
        .order_by(desc(Signal.collected_at))
        .limit(20)
        .all()
    )
    for signal in recent_signals:
        activities.append({
            "timestamp": signal.collected_at,
            "time": signal.collected_at.strftime("%H:%M:%S") if signal.collected_at else "",
            "type": "trend",  # signals show as 'trend' type for SIGNAL prefix
            "message": f"Signal collected: {signal.title[:80]}..." if len(signal.title) > 80 else f"Signal collected: {signal.title}",
            "source": signal.source,
        })

    # Get recent trends
    recent_trends = (
        session.query(Trend)
        .filter(Trend.analyzed_at.isnot(None))
        .order_by(desc(Trend.analyzed_at))
        .limit(10)
        .all()
    )
    for trend in recent_trends:
        activities.append({
            "timestamp": trend.analyzed_at,
            "time": trend.analyzed_at.strftime("%H:%M:%S") if trend.analyzed_at else "",
            "type": "trend",
            "message": f"Trend analyzed: {trend.name[:60]}... (score: {trend.score:.1f})" if len(trend.name) > 60 else f"Trend analyzed: {trend.name} (score: {trend.score:.1f})",
            "signal_count": trend.signal_count,
        })

    # Get recent ideas
    recent_ideas = (
        session.query(Idea)
        .filter(Idea.created_at.isnot(None))
        .order_by(desc(Idea.created_at))
        .limit(10)
        .all()
    )
    for idea in recent_ideas:
        status_emoji = {"promoted": "🚀", "scored": "📊", "archived": "📦"}.get(idea.status, "💡")
        activities.append({
            "timestamp": idea.created_at,
            "time": idea.created_at.strftime("%H:%M:%S") if idea.created_at else "",
            "type": "idea",
            "message": f"Idea generated [{idea.status}]: {idea.title[:50]}..." if len(idea.title) > 50 else f"Idea generated [{idea.status}]: {idea.title}",
            "score": idea.score,
        })

    # Get recent debates
    recent_debates = (
        session.query(DebateSession)
        .order_by(desc(DebateSession.started_at))
        .limit(10)
        .all()
    )
    for debate in recent_debates:
        if debate.started_at:
            topic_short = (debate.topic[:40] + "...") if debate.topic and len(debate.topic) > 40 else (debate.topic or "Unknown topic")
            activities.append({
                "timestamp": debate.started_at,
                "time": debate.started_at.strftime("%H:%M:%S"),
                "type": "debate",
                "message": f"Debate started: {topic_short}",
                "phase": debate.phase,
            })
        if debate.completed_at:
            activities.append({
                "timestamp": debate.completed_at,
                "time": debate.completed_at.strftime("%H:%M:%S"),
                "type": "debate",
                "message": f"Debate completed: {debate.status} - {len(debate.ideas_generated or [])} ideas generated",
                "status": debate.status,
            })

    # Get recent plans
    recent_plans = (
        session.query(Plan)
        .filter(Plan.created_at.isnot(None))
        .order_by(desc(Plan.created_at))
        .limit(10)
        .all()
    )
    for plan in recent_plans:
        activities.append({
            "timestamp": plan.created_at,
            "time": plan.created_at.strftime("%H:%M:%S") if plan.created_at else "",
            "type": "plan",
            "message": f"Plan created [{plan.status}]: {plan.title[:50]}..." if len(plan.title) > 50 else f"Plan created [{plan.status}]: {plan.title}",
            "version": plan.version,
        })

    # Sort all activities by timestamp descending
    activities.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)

    # Limit to requested amount
    activities = activities[:limit]

    # Remove timestamp field (only used for sorting) and ensure time format
    for activity in activities:
        activity.pop("timestamp", None)

    return {
        "activities": activities,
        "total": len(activities),
    }


@app.get("/adapters")
async def get_adapters():
    """Get detailed signal adapter information."""
    from ..adapters import (
        RSSAdapter, GitHubEventsAdapter, OnChainAdapter,
        SocialMediaAdapter, NewsAPIAdapter, TwitterAdapter,
        DiscordAdapter, LensAdapter, FarcasterAdapter
    )
    import asyncio

    adapters_info = []

    # Define all adapters with their details
    adapter_classes = [
        {
            "class": RSSAdapter,
            "category": "news",
            "description": "RSS/Atom 피드 수집기",
            "description_en": "RSS/Atom feed collector",
        },
        {
            "class": GitHubEventsAdapter,
            "category": "dev",
            "description": "GitHub 트렌딩 및 릴리스 추적",
            "description_en": "GitHub trending & releases tracker",
        },
        {
            "class": OnChainAdapter,
            "category": "crypto",
            "description": "DefiLlama TVL, DEX 볼륨, 웨일 알림, 스테이블코인 흐름",
            "description_en": "DefiLlama TVL, DEX volume, whale alerts, stablecoin flows",
        },
        {
            "class": SocialMediaAdapter,
            "category": "social",
            "description": "Reddit 서브레딧 모니터링",
            "description_en": "Reddit subreddit monitoring",
        },
        {
            "class": NewsAPIAdapter,
            "category": "news",
            "description": "NewsAPI, Cryptopanic, Hacker News",
            "description_en": "NewsAPI, Cryptopanic, Hacker News",
        },
        {
            "class": TwitterAdapter,
            "category": "social",
            "description": "Twitter/X Nitter RSS 풀 (20+ 계정)",
            "description_en": "Twitter/X via Nitter RSS pool (20+ accounts)",
        },
        {
            "class": DiscordAdapter,
            "category": "social",
            "description": "Discord 서버 공지사항 (7개 서버)",
            "description_en": "Discord server announcements (7 servers)",
        },
        {
            "class": LensAdapter,
            "category": "web3",
            "description": "Lens Protocol GraphQL API (10개 프로필)",
            "description_en": "Lens Protocol GraphQL API (10 profiles)",
        },
        {
            "class": FarcasterAdapter,
            "category": "web3",
            "description": "Farcaster/Warpcast (10개 유저, 10개 채널)",
            "description_en": "Farcaster/Warpcast (10 users, 10 channels)",
        },
    ]

    for adapter_info in adapter_classes:
        try:
            adapter = adapter_info["class"]()

            # Get health check info
            health = await adapter.health_check()

            # Build detailed info
            info = {
                "name": adapter.name,
                "category": adapter_info["category"],
                "description": adapter_info["description"],
                "description_en": adapter_info["description_en"],
                "enabled": adapter.is_enabled(),
                "last_fetch": health.get("last_fetch"),
                "health": health,
            }

            # Add adapter-specific details
            if hasattr(adapter, 'SUBREDDITS'):
                info["sources"] = adapter.SUBREDDITS
                info["source_count"] = len(adapter.SUBREDDITS)
            elif hasattr(adapter, 'TRACKED_ACCOUNTS'):
                info["sources"] = adapter.TRACKED_ACCOUNTS
                info["source_count"] = len(adapter.TRACKED_ACCOUNTS)
            elif hasattr(adapter, 'TRACKED_PROTOCOLS'):
                info["sources"] = adapter.TRACKED_PROTOCOLS
                info["source_count"] = len(adapter.TRACKED_PROTOCOLS)
            elif hasattr(adapter, 'TRACKED_PROFILES'):
                info["sources"] = adapter.TRACKED_PROFILES
                info["source_count"] = len(adapter.TRACKED_PROFILES)
            elif hasattr(adapter, 'TRACKED_USERS'):
                info["sources"] = adapter.TRACKED_USERS
                info["source_count"] = len(adapter.TRACKED_USERS)
            elif hasattr(adapter, 'TRACKED_SERVERS'):
                info["sources"] = [s["name"] for s in adapter.TRACKED_SERVERS]
                info["source_count"] = len(adapter.TRACKED_SERVERS)

            adapters_info.append(info)

        except Exception as e:
            adapters_info.append({
                "name": adapter_info["class"].__name__.replace("Adapter", "").lower(),
                "category": adapter_info["category"],
                "description": adapter_info["description"],
                "enabled": False,
                "error": str(e),
            })

    return {
        "adapters": adapters_info,
        "total": len(adapters_info),
        "enabled_count": sum(1 for a in adapters_info if a.get("enabled", False)),
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


@app.get("/signals/timeline")
async def get_signals_timeline(
    period: str = Query(default="24h", pattern="^(24h|7d)$"),
    session: Session = Depends(get_session),
):
    """Get signal collection timeline for visualization.

    Returns hourly counts for 24h or daily counts for 7d period.
    """
    from ..db.models import Signal
    from sqlalchemy import func, extract
    from datetime import timedelta

    now = datetime.utcnow()

    if period == "24h":
        # Get hourly counts for last 24 hours
        start_time = now - timedelta(hours=24)
        results = (
            session.query(
                extract('hour', Signal.collected_at).label('hour'),
                func.count(Signal.id).label('count')
            )
            .filter(Signal.collected_at >= start_time)
            .group_by(extract('hour', Signal.collected_at))
            .all()
        )

        # Build hourly slots
        hour_counts = {int(r.hour): r.count for r in results}
        slots = []
        for i in range(24):
            hour = (now.hour - 23 + i) % 24
            slots.append({
                "label": f"{hour:02d}:00",
                "count": hour_counts.get(hour, 0),
                "hour": hour,
            })
    else:
        # Get daily counts for last 7 days
        start_time = now - timedelta(days=7)
        results = (
            session.query(
                func.date(Signal.collected_at).label('date'),
                func.count(Signal.id).label('count')
            )
            .filter(Signal.collected_at >= start_time)
            .group_by(func.date(Signal.collected_at))
            .all()
        )

        # Build daily slots
        date_counts = {str(r.date): r.count for r in results}
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        slots = []
        for i in range(7):
            date = now - timedelta(days=6-i)
            date_str = date.strftime('%Y-%m-%d')
            slots.append({
                "label": days[date.weekday()],
                "count": date_counts.get(date_str, 0),
            })

    total = sum(s['count'] for s in slots)

    return {
        "slots": slots,
        "total": total,
        "period": period,
        "timestamp": now.isoformat(),
    }


@app.get("/pipeline/live")
async def get_pipeline_live(session: Session = Depends(get_session)):
    """Get real-time pipeline status with conversion rates and current processing items.

    Returns:
        - stages: Current counts for each pipeline stage (signals, trends, ideas, plans)
        - conversion_rates: Conversion rates between stages
        - processing: Currently processing items
        - rates: Hourly/daily generation rates
    """
    from ..db.models import Signal, Trend, Idea, DebateSession, Plan
    from sqlalchemy import func, desc
    from datetime import timedelta

    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Get counts for each stage
    total_signals = session.query(func.count(Signal.id)).scalar() or 0
    total_trends = session.query(func.count(Trend.id)).scalar() or 0
    total_ideas = session.query(func.count(Idea.id)).scalar() or 0
    total_plans = session.query(func.count(Plan.id)).scalar() or 0

    # Get hourly rates
    signals_last_hour = session.query(func.count(Signal.id)).filter(
        Signal.collected_at >= last_hour
    ).scalar() or 0

    trends_today = session.query(func.count(Trend.id)).filter(
        Trend.analyzed_at >= today
    ).scalar() or 0

    ideas_today = session.query(func.count(Idea.id)).filter(
        Idea.created_at >= today
    ).scalar() or 0

    plans_last_7d = session.query(func.count(Plan.id)).filter(
        Plan.created_at >= last_7d
    ).scalar() or 0

    # Calculate conversion rates
    signals_to_trends = (total_trends / total_signals * 100) if total_signals > 0 else 0
    trends_to_ideas = (total_ideas / total_trends * 100) if total_trends > 0 else 0
    ideas_to_plans = (total_plans / total_ideas * 100) if total_ideas > 0 else 0

    # Get currently processing items
    processing = []

    # Recent signals (last 5 minutes)
    recent_signals = (
        session.query(Signal)
        .filter(Signal.collected_at >= now - timedelta(minutes=5))
        .order_by(desc(Signal.collected_at))
        .limit(3)
        .all()
    )
    for signal in recent_signals:
        minutes_ago = int((now - signal.collected_at).total_seconds() / 60) if signal.collected_at else 0
        processing.append({
            "type": "SIGNAL",
            "title": signal.title[:60] + "..." if len(signal.title) > 60 else signal.title,
            "time_ago": f"{minutes_ago}m ago" if minutes_ago > 0 else "just now",
            "source": signal.source,
        })

    # Active debates
    active_debates = (
        session.query(DebateSession)
        .filter(DebateSession.status == "in-progress")
        .order_by(desc(DebateSession.started_at))
        .limit(2)
        .all()
    )
    for debate in active_debates:
        topic_short = (debate.topic[:50] + "...") if debate.topic and len(debate.topic) > 50 else (debate.topic or "Unknown")
        processing.append({
            "type": "DEBATE",
            "title": topic_short,
            "time_ago": f"R{debate.round_number}/{debate.max_rounds}",
            "phase": debate.phase,
        })

    # Recent trends being analyzed (last 30 minutes)
    recent_trends = (
        session.query(Trend)
        .filter(Trend.analyzed_at >= now - timedelta(minutes=30))
        .order_by(desc(Trend.analyzed_at))
        .limit(2)
        .all()
    )
    for trend in recent_trends:
        minutes_ago = int((now - trend.analyzed_at).total_seconds() / 60) if trend.analyzed_at else 0
        processing.append({
            "type": "TREND",
            "title": trend.name[:50] + "..." if len(trend.name) > 50 else trend.name,
            "time_ago": f"{minutes_ago}m ago",
            "score": trend.score,
        })

    return {
        "stages": {
            "signals": {
                "count": total_signals,
                "rate": f"+{signals_last_hour}/hr",
                "status": "active" if signals_last_hour > 0 else "idle",
            },
            "trends": {
                "count": total_trends,
                "rate": f"+{trends_today}/day",
                "status": "active" if trends_today > 0 else "idle",
            },
            "ideas": {
                "count": total_ideas,
                "rate": f"+{ideas_today}/day",
                "status": "active" if ideas_today > 0 else "idle",
            },
            "plans": {
                "count": total_plans,
                "rate": f"+{plans_last_7d}/wk",
                "status": "active" if plans_last_7d > 0 else "idle",
            },
        },
        "conversion_rates": {
            "signals_to_trends": round(signals_to_trends, 1),
            "trends_to_ideas": round(trends_to_ideas, 1),
            "ideas_to_plans": round(ideas_to_plans, 1),
        },
        "processing": processing[:5],  # Limit to 5 items
        "timestamp": now.isoformat(),
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
            "adapters": "/adapters",
            "pipeline/live": "/pipeline/live",
            "docs": "/docs",
        },
    }
