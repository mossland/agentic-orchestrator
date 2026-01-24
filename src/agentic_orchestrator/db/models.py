"""
SQLAlchemy models for Agentic Orchestrator.

Defines the database schema for signals, trends, ideas, debates, plans,
API usage tracking, and system logs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Index,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


# Enums
class SignalSource(str, enum.Enum):
    RSS = "rss"
    GITHUB = "github"
    ONCHAIN = "onchain"
    SOCIAL = "social"
    NEWS = "news"


class SignalCategory(str, enum.Enum):
    AI = "ai"
    CRYPTO = "crypto"
    FINANCE = "finance"
    SECURITY = "security"
    DEV = "dev"
    OTHER = "other"


class IdeaStatus(str, enum.Enum):
    PENDING = "pending"      # Awaiting scoring
    SCORED = "scored"        # Scored but not yet promoted (middle score)
    PROMOTED = "promoted"    # Auto-promoted to planning (high score)
    IN_DEBATE = "in_debate"  # Currently being debated
    SELECTED = "selected"    # Manually selected for planning
    REJECTED = "rejected"    # Manually rejected
    PLANNED = "planned"      # Plan created
    ARCHIVED = "archived"    # Archived (low score or old)


class DebatePhase(str, enum.Enum):
    DIVERGENCE = "divergence"
    CONVERGENCE = "convergence"
    PLANNING = "planning"


class DebateSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageType(str, enum.Enum):
    PROPOSE = "propose"
    SUPPORT = "support"
    CHALLENGE = "challenge"
    REFINE = "refine"
    MERGE = "merge"
    WITHDRAW = "withdraw"
    CONSENSUS = "consensus"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class AgentStatusEnum(str, enum.Enum):
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"


# Models
class Signal(Base):
    """Signal collected from various sources (RSS, GitHub, OnChain, Social, News)."""

    __tablename__ = "signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=False)
    title_ko = Column(Text)  # Korean translation
    summary = Column(Text)
    summary_ko = Column(Text)  # Korean translation
    url = Column(Text)
    raw_data = Column(JSON)
    score = Column(Float, default=0.0, index=True)
    sentiment = Column(String(20))  # positive, negative, neutral
    topics = Column(JSON)  # List of topics
    entities = Column(JSON)  # List of extracted entities
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_signals_source_category", "source", "category"),
        Index("idx_signals_collected_score", "collected_at", "score"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "title_ko": self.title_ko,
            "summary": self.summary,
            "summary_ko": self.summary_ko,
            "url": self.url,
            "score": self.score,
            "sentiment": self.sentiment,
            "topics": self.topics or [],
            "entities": self.entities or [],
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }


class Trend(Base):
    """Analyzed trend from collected signals."""

    __tablename__ = "trends"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period = Column(String(20), nullable=False, index=True)  # 24h, 7d, 30d
    name = Column(String(255), nullable=False)
    name_ko = Column(String(500))  # Korean translation
    description = Column(Text)
    description_ko = Column(Text)  # Korean translation
    score = Column(Float, nullable=False, index=True)
    signal_count = Column(Integer, default=0)
    category = Column(String(50))
    keywords = Column(JSON)  # List of keywords
    related_signals = Column(JSON)  # List of signal IDs
    analysis_data = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ideas = relationship("Idea", back_populates="source_trend")

    def to_dict(self) -> Dict[str, Any]:
        analysis = self.analysis_data or {}
        return {
            "id": self.id,
            "period": self.period,
            "name": self.name,
            "name_ko": self.name_ko,
            "description": self.description,
            "description_ko": self.description_ko,
            "score": self.score,
            "signal_count": self.signal_count,
            "category": self.category,
            "keywords": self.keywords or [],
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            # Rich analysis data
            "web3_relevance": analysis.get("web3_relevance", ""),
            "idea_seeds": analysis.get("idea_seeds", []),
            "sources": analysis.get("sources", []),
            "sample_headlines": analysis.get("sample_headlines", []),
        }


class Idea(Base):
    """Generated idea from signals and trends."""

    __tablename__ = "ideas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    description = Column(Text)
    source_type = Column(String(20), nullable=False)  # traditional, trend_based
    source_trend_id = Column(String(36), ForeignKey("trends.id"))
    source_signals = Column(JSON)  # List of signal IDs
    debate_session_id = Column(String(36), ForeignKey("debate_sessions.id"), nullable=True, index=True)
    status = Column(String(20), default="pending", index=True)
    github_issue_id = Column(Integer)
    github_issue_url = Column(Text)
    score = Column(Float, default=0.0)
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_trend = relationship("Trend", back_populates="ideas")
    source_debate = relationship("DebateSession", foreign_keys=[debate_session_id])
    debate_sessions = relationship("DebateSession", back_populates="idea", foreign_keys="DebateSession.idea_id")
    plans = relationship("Plan", back_populates="idea")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "description": self.description,
            "source_type": self.source_type,
            "status": self.status,
            "score": self.score,
            "debate_session_id": self.debate_session_id,
            "github_issue_url": self.github_issue_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DebateSession(Base):
    """Debate session for an idea or standalone topic."""

    __tablename__ = "debate_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id = Column(String(36), ForeignKey("ideas.id"), nullable=True, index=True)  # nullable for standalone debates
    topic = Column(Text)  # Topic for standalone debates (when no idea_id)
    context = Column(Text)  # Context/background for the debate
    phase = Column(String(20), nullable=False, index=True)  # divergence, convergence, planning
    round_number = Column(Integer, default=1)
    max_rounds = Column(Integer, default=3)
    status = Column(String(20), default="active", index=True)
    participants = Column(JSON)  # List of agent IDs
    summary = Column(Text)
    outcome = Column(String(20))  # selected, rejected, needs_refinement
    final_plan = Column(Text)  # Final plan content for standalone debates
    ideas_generated = Column(JSON)  # List of ideas generated during debate
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    extra_metadata = Column("metadata", JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    idea = relationship("Idea", back_populates="debate_sessions", foreign_keys=[idea_id])
    messages = relationship("DebateMessage", back_populates="session", order_by="DebateMessage.created_at")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "idea_id": self.idea_id,
            "topic": self.topic,
            "context": self.context,
            "phase": self.phase,
            "round_number": self.round_number,
            "max_rounds": self.max_rounds,
            "status": self.status,
            "participants": self.participants or [],
            "summary": self.summary,
            "outcome": self.outcome,
            "final_plan": self.final_plan,
            "ideas_generated": self.ideas_generated or [],
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "message_count": len(self.messages) if self.messages else 0,
        }


class DebateMessage(Base):
    """Individual message in a debate session."""

    __tablename__ = "debate_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("debate_sessions.id"), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    agent_handle = Column(String(100))
    message_type = Column(String(20), nullable=False)  # propose, support, challenge, etc.
    content = Column(Text, nullable=False)
    content_ko = Column(Text)  # Korean translation
    references = Column(JSON)  # List of referenced message IDs
    personality_traits = Column(JSON)
    token_count = Column(Integer)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("DebateSession", back_populates="messages")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_handle": self.agent_handle,
            "message_type": self.message_type,
            "content": self.content,
            "content_ko": self.content_ko,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Plan(Base):
    """Detailed plan document for an idea."""

    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id = Column(String(36), ForeignKey("ideas.id"), nullable=False, index=True)
    debate_session_id = Column(String(36), ForeignKey("debate_sessions.id"))
    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft", index=True)

    # Document sections
    prd_content = Column(Text)
    architecture_content = Column(Text)
    user_research_content = Column(Text)
    business_model_content = Column(Text)
    project_plan_content = Column(Text)
    final_plan = Column(Text)

    # GitHub integration
    github_issue_id = Column(Integer)
    github_issue_url = Column(Text)

    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    idea = relationship("Idea", back_populates="plans")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "idea_id": self.idea_id,
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "github_issue_url": self.github_issue_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class APIUsage(Base):
    """Track API usage and costs."""

    __tablename__ = "api_usage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # claude, openai, gemini, ollama
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    request_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_usage_date_provider_model", "date", "provider", "model", unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "request_count": self.request_count,
        }


class SystemLog(Base):
    """System logs for monitoring and debugging."""

    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(20), nullable=False, index=True)  # debug, info, warn, error
    source = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    trace = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_logs_level_source", "level", "source"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentState(Base):
    """Track agent states and statistics."""

    __tablename__ = "agent_states"

    id = Column(String(100), primary_key=True)  # agent ID
    name = Column(String(100), nullable=False)
    handle = Column(String(100))
    status = Column(String(20), default="idle")  # idle, active, error
    current_task = Column(Text)
    last_active_at = Column(DateTime)
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    personality_config = Column(JSON)
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "handle": self.handle,
            "status": self.status,
            "current_task": self.current_task,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
        }
