"""
Repository pattern implementation for Agentic Orchestrator.

Provides data access layer for all models with common CRUD operations
and specialized queries.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from .models import (
    Signal,
    Trend,
    Idea,
    DebateSession,
    DebateMessage,
    Plan,
    APIUsage,
    SystemLog,
    AgentState,
)


class BaseRepository:
    """Base repository with common operations."""

    def __init__(self, session: Session):
        self.session = session


class SignalRepository(BaseRepository):
    """Repository for Signal operations."""

    def create(self, signal_data: Dict[str, Any]) -> Signal:
        """Create a new signal."""
        signal = Signal(**signal_data)
        self.session.add(signal)
        self.session.flush()
        return signal

    def create_many(self, signals_data: List[Dict[str, Any]]) -> List[Signal]:
        """Create multiple signals at once."""
        signals = [Signal(**data) for data in signals_data]
        self.session.add_all(signals)
        self.session.flush()
        return signals

    def get_by_id(self, signal_id: str) -> Optional[Signal]:
        """Get signal by ID."""
        return self.session.query(Signal).filter(Signal.id == signal_id).first()

    def get_recent(
        self,
        hours: int = 24,
        limit: int = 100,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Signal]:
        """Get recent signals with optional filters."""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = self.session.query(Signal).filter(
            Signal.collected_at >= since,
            Signal.score >= min_score
        )

        if source:
            query = query.filter(Signal.source == source)
        if category:
            query = query.filter(Signal.category == category)

        return query.order_by(desc(Signal.score)).limit(limit).all()

    def get_by_source(self, source: str, limit: int = 50) -> List[Signal]:
        """Get signals by source."""
        return (
            self.session.query(Signal)
            .filter(Signal.source == source)
            .order_by(desc(Signal.collected_at))
            .limit(limit)
            .all()
        )

    def get_by_category(self, category: str, limit: int = 50) -> List[Signal]:
        """Get signals by category."""
        return (
            self.session.query(Signal)
            .filter(Signal.category == category)
            .order_by(desc(Signal.collected_at))
            .limit(limit)
            .all()
        )

    def count_by_source(self) -> Dict[str, int]:
        """Get signal count by source."""
        results = (
            self.session.query(Signal.source, func.count(Signal.id))
            .group_by(Signal.source)
            .all()
        )
        return {source: count for source, count in results}

    def count_by_category(self) -> Dict[str, int]:
        """Get signal count by category."""
        results = (
            self.session.query(Signal.category, func.count(Signal.id))
            .group_by(Signal.category)
            .all()
        )
        return {category: count for category, count in results}

    def search(self, query: str, limit: int = 50) -> List[Signal]:
        """Search signals by title or summary."""
        pattern = f"%{query}%"
        return (
            self.session.query(Signal)
            .filter(or_(
                Signal.title.ilike(pattern),
                Signal.summary.ilike(pattern)
            ))
            .order_by(desc(Signal.collected_at))
            .limit(limit)
            .all()
        )

    def delete_older_than(self, days: int) -> int:
        """Delete signals older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self.session.query(Signal).filter(Signal.collected_at < cutoff).delete()
        self.session.flush()
        return result


class TrendRepository(BaseRepository):
    """Repository for Trend operations."""

    def create(self, trend_data: Dict[str, Any]) -> Trend:
        """Create a new trend."""
        trend = Trend(**trend_data)
        self.session.add(trend)
        self.session.flush()
        return trend

    def get_by_id(self, trend_id: str) -> Optional[Trend]:
        """Get trend by ID."""
        return self.session.query(Trend).filter(Trend.id == trend_id).first()

    def get_latest(self, period: str = "24h", limit: int = 10) -> List[Trend]:
        """Get latest trends for a period."""
        return (
            self.session.query(Trend)
            .filter(Trend.period == period)
            .order_by(desc(Trend.analyzed_at), desc(Trend.score))
            .limit(limit)
            .all()
        )

    def get_by_category(self, category: str, limit: int = 10) -> List[Trend]:
        """Get trends by category."""
        return (
            self.session.query(Trend)
            .filter(Trend.category == category)
            .order_by(desc(Trend.score))
            .limit(limit)
            .all()
        )


class IdeaRepository(BaseRepository):
    """Repository for Idea operations."""

    def create(self, idea_data: Dict[str, Any]) -> Idea:
        """Create a new idea."""
        idea = Idea(**idea_data)
        self.session.add(idea)
        self.session.flush()
        return idea

    def get_by_id(self, idea_id: str) -> Optional[Idea]:
        """Get idea by ID."""
        return self.session.query(Idea).filter(Idea.id == idea_id).first()

    def get_by_status(self, status: str, limit: int = 50) -> List[Idea]:
        """Get ideas by status."""
        return (
            self.session.query(Idea)
            .filter(Idea.status == status)
            .order_by(desc(Idea.created_at))
            .limit(limit)
            .all()
        )

    def get_pending(self, limit: int = 50) -> List[Idea]:
        """Get pending ideas."""
        return self.get_by_status("pending", limit)

    def get_in_debate(self, limit: int = 50) -> List[Idea]:
        """Get ideas currently in debate."""
        return self.get_by_status("in_debate", limit)

    def get_selected(self, limit: int = 50) -> List[Idea]:
        """Get selected ideas."""
        return self.get_by_status("selected", limit)

    def update_status(self, idea_id: str, status: str) -> Optional[Idea]:
        """Update idea status."""
        idea = self.get_by_id(idea_id)
        if idea:
            idea.status = status
            idea.updated_at = datetime.utcnow()
            self.session.flush()
        return idea

    def count_by_status(self) -> Dict[str, int]:
        """Get idea count by status."""
        results = (
            self.session.query(Idea.status, func.count(Idea.id))
            .group_by(Idea.status)
            .all()
        )
        return {status: count for status, count in results}

    def get_recent(self, days: int = 7, limit: int = 50) -> List[Idea]:
        """Get recent ideas."""
        since = datetime.utcnow() - timedelta(days=days)
        return (
            self.session.query(Idea)
            .filter(Idea.created_at >= since)
            .order_by(desc(Idea.created_at))
            .limit(limit)
            .all()
        )


class DebateRepository(BaseRepository):
    """Repository for Debate operations."""

    def create_session(self, session_data: Dict[str, Any]) -> DebateSession:
        """Create a new debate session."""
        debate = DebateSession(**session_data)
        self.session.add(debate)
        self.session.flush()
        return debate

    def add_message(self, message_data: Dict[str, Any]) -> DebateMessage:
        """Add a message to a debate session."""
        message = DebateMessage(**message_data)
        self.session.add(message)
        self.session.flush()
        return message

    def get_session_by_id(self, session_id: str) -> Optional[DebateSession]:
        """Get debate session by ID."""
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.id == session_id)
            .first()
        )

    def get_sessions_by_idea(self, idea_id: str) -> List[DebateSession]:
        """Get all debate sessions for an idea."""
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.idea_id == idea_id)
            .order_by(desc(DebateSession.created_at))
            .all()
        )

    def get_session_messages(self, session_id: str) -> List[DebateMessage]:
        """Get all messages for a debate session."""
        return (
            self.session.query(DebateMessage)
            .filter(DebateMessage.session_id == session_id)
            .order_by(DebateMessage.created_at)
            .all()
        )

    def get_active_sessions(self) -> List[DebateSession]:
        """Get all active debate sessions."""
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.status == "active")
            .order_by(desc(DebateSession.started_at))
            .all()
        )

    def get_sessions_by_phase(self, phase: str) -> List[DebateSession]:
        """Get sessions by phase."""
        return (
            self.session.query(DebateSession)
            .filter(DebateSession.phase == phase)
            .order_by(desc(DebateSession.started_at))
            .all()
        )

    def complete_session(
        self,
        session_id: str,
        outcome: str,
        summary: Optional[str] = None
    ) -> Optional[DebateSession]:
        """Mark a session as completed."""
        debate = self.get_session_by_id(session_id)
        if debate:
            debate.status = "completed"
            debate.outcome = outcome
            debate.summary = summary
            debate.completed_at = datetime.utcnow()
            self.session.flush()
        return debate

    def get_message_count_by_agent(self, session_id: str) -> Dict[str, int]:
        """Get message count by agent for a session."""
        results = (
            self.session.query(DebateMessage.agent_id, func.count(DebateMessage.id))
            .filter(DebateMessage.session_id == session_id)
            .group_by(DebateMessage.agent_id)
            .all()
        )
        return {agent_id: count for agent_id, count in results}


class PlanRepository(BaseRepository):
    """Repository for Plan operations."""

    def create(self, plan_data: Dict[str, Any]) -> Plan:
        """Create a new plan."""
        plan = Plan(**plan_data)
        self.session.add(plan)
        self.session.flush()
        return plan

    def get_by_id(self, plan_id: str) -> Optional[Plan]:
        """Get plan by ID."""
        return self.session.query(Plan).filter(Plan.id == plan_id).first()

    def get_by_idea(self, idea_id: str) -> List[Plan]:
        """Get all plans for an idea."""
        return (
            self.session.query(Plan)
            .filter(Plan.idea_id == idea_id)
            .order_by(desc(Plan.version))
            .all()
        )

    def get_latest_by_idea(self, idea_id: str) -> Optional[Plan]:
        """Get the latest plan for an idea."""
        return (
            self.session.query(Plan)
            .filter(Plan.idea_id == idea_id)
            .order_by(desc(Plan.version))
            .first()
        )

    def get_by_status(self, status: str, limit: int = 50) -> List[Plan]:
        """Get plans by status."""
        return (
            self.session.query(Plan)
            .filter(Plan.status == status)
            .order_by(desc(Plan.created_at))
            .limit(limit)
            .all()
        )

    def update_status(self, plan_id: str, status: str) -> Optional[Plan]:
        """Update plan status."""
        plan = self.get_by_id(plan_id)
        if plan:
            plan.status = status
            plan.updated_at = datetime.utcnow()
            self.session.flush()
        return plan


class APIUsageRepository(BaseRepository):
    """Repository for API usage tracking."""

    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ) -> APIUsage:
        """Record API usage."""
        today = date.today()

        usage = (
            self.session.query(APIUsage)
            .filter(
                APIUsage.date == today,
                APIUsage.provider == provider,
                APIUsage.model == model
            )
            .first()
        )

        if usage:
            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.cost_usd += cost
            usage.request_count += 1
            usage.updated_at = datetime.utcnow()
        else:
            usage = APIUsage(
                date=today,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                request_count=1
            )
            self.session.add(usage)

        self.session.flush()
        return usage

    def get_today_usage(self) -> Dict[str, Any]:
        """Get today's total usage."""
        today = date.today()
        results = (
            self.session.query(
                func.sum(APIUsage.cost_usd).label("total_cost"),
                func.sum(APIUsage.input_tokens).label("total_input"),
                func.sum(APIUsage.output_tokens).label("total_output"),
                func.sum(APIUsage.request_count).label("total_requests")
            )
            .filter(APIUsage.date == today)
            .first()
        )
        return {
            "total_cost": float(results.total_cost or 0),
            "total_input_tokens": int(results.total_input or 0),
            "total_output_tokens": int(results.total_output or 0),
            "total_requests": int(results.total_requests or 0)
        }

    def get_today_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Get today's usage by provider."""
        today = date.today()
        results = (
            self.session.query(
                APIUsage.provider,
                func.sum(APIUsage.cost_usd).label("cost"),
                func.sum(APIUsage.input_tokens).label("input_tokens"),
                func.sum(APIUsage.output_tokens).label("output_tokens"),
                func.sum(APIUsage.request_count).label("requests")
            )
            .filter(APIUsage.date == today)
            .group_by(APIUsage.provider)
            .all()
        )
        return {
            r.provider: {
                "cost": float(r.cost or 0),
                "input_tokens": int(r.input_tokens or 0),
                "output_tokens": int(r.output_tokens or 0),
                "requests": int(r.requests or 0)
            }
            for r in results
        }

    def get_month_total(self) -> float:
        """Get this month's total cost."""
        first_of_month = date.today().replace(day=1)
        result = (
            self.session.query(func.sum(APIUsage.cost_usd))
            .filter(APIUsage.date >= first_of_month)
            .scalar()
        )
        return float(result or 0)

    def get_usage_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage history for the past N days."""
        since = date.today() - timedelta(days=days)
        results = (
            self.session.query(
                APIUsage.date,
                func.sum(APIUsage.cost_usd).label("cost"),
                func.sum(APIUsage.request_count).label("requests")
            )
            .filter(APIUsage.date >= since)
            .group_by(APIUsage.date)
            .order_by(APIUsage.date)
            .all()
        )
        return [
            {
                "date": r.date.isoformat(),
                "cost": float(r.cost or 0),
                "requests": int(r.requests or 0)
            }
            for r in results
        ]


class SystemLogRepository(BaseRepository):
    """Repository for system logs."""

    def log(
        self,
        level: str,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        trace: Optional[str] = None
    ) -> SystemLog:
        """Create a log entry."""
        log_entry = SystemLog(
            level=level,
            source=source,
            message=message,
            details=details,
            trace=trace
        )
        self.session.add(log_entry)
        self.session.flush()
        return log_entry

    def info(self, source: str, message: str, details: Optional[Dict[str, Any]] = None) -> SystemLog:
        """Log info message."""
        return self.log("info", source, message, details)

    def warn(self, source: str, message: str, details: Optional[Dict[str, Any]] = None) -> SystemLog:
        """Log warning message."""
        return self.log("warn", source, message, details)

    def error(
        self,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        trace: Optional[str] = None
    ) -> SystemLog:
        """Log error message."""
        return self.log("error", source, message, details, trace)

    def get_recent(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[SystemLog]:
        """Get recent logs with optional filters."""
        query = self.session.query(SystemLog)

        if level:
            query = query.filter(SystemLog.level == level)
        if source:
            query = query.filter(SystemLog.source == source)

        return query.order_by(desc(SystemLog.created_at)).limit(limit).all()

    def get_errors(self, hours: int = 24, limit: int = 50) -> List[SystemLog]:
        """Get recent errors."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.session.query(SystemLog)
            .filter(
                SystemLog.level == "error",
                SystemLog.created_at >= since
            )
            .order_by(desc(SystemLog.created_at))
            .limit(limit)
            .all()
        )

    def delete_older_than(self, days: int) -> int:
        """Delete logs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self.session.query(SystemLog).filter(SystemLog.created_at < cutoff).delete()
        self.session.flush()
        return result


class AgentStateRepository(BaseRepository):
    """Repository for agent state tracking."""

    def get_or_create(self, agent_id: str, name: str, handle: Optional[str] = None) -> AgentState:
        """Get or create an agent state."""
        state = self.session.query(AgentState).filter(AgentState.id == agent_id).first()
        if not state:
            state = AgentState(id=agent_id, name=name, handle=handle)
            self.session.add(state)
            self.session.flush()
        return state

    def update_status(self, agent_id: str, status: str, current_task: Optional[str] = None) -> Optional[AgentState]:
        """Update agent status."""
        state = self.session.query(AgentState).filter(AgentState.id == agent_id).first()
        if state:
            state.status = status
            state.current_task = current_task
            if status == "active":
                state.last_active_at = datetime.utcnow()
            state.updated_at = datetime.utcnow()
            self.session.flush()
        return state

    def increment_stats(self, agent_id: str, messages: int = 0, tokens: int = 0) -> Optional[AgentState]:
        """Increment agent statistics."""
        state = self.session.query(AgentState).filter(AgentState.id == agent_id).first()
        if state:
            state.total_messages += messages
            state.total_tokens += tokens
            state.updated_at = datetime.utcnow()
            self.session.flush()
        return state

    def get_active_agents(self) -> List[AgentState]:
        """Get all active agents."""
        return (
            self.session.query(AgentState)
            .filter(AgentState.status == "active")
            .all()
        )

    def get_all(self) -> List[AgentState]:
        """Get all agent states."""
        return self.session.query(AgentState).order_by(AgentState.name).all()
