"""Tests for FastAPI endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import (
    Base,
    Signal,
    Trend,
    Idea,
    DebateSession,
    DebateMessage,
    Plan,
    APIUsage,
    SystemLog,
)


# Create test database
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database with fresh tables for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session

    session = TestingSessionLocal()
    yield session
    session.close()

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_signals(test_db):
    """Create sample signals in the database."""
    signals = [
        Signal(
            source="rss",
            category="crypto",
            title="Bitcoin hits new high",
            summary="BTC reaches $100k",
            score=9.5,
            collected_at=datetime.utcnow(),
        ),
        Signal(
            source="github",
            category="ai",
            title="New AI model released",
            summary="GPT-5 announced",
            score=8.5,
            collected_at=datetime.utcnow(),
        ),
        Signal(
            source="rss",
            category="crypto",
            title="ETH upgrade complete",
            summary="Ethereum 3.0 live",
            score=7.5,
            collected_at=datetime.utcnow(),
        ),
    ]
    for signal in signals:
        test_db.add(signal)
    test_db.commit()
    return signals


@pytest.fixture
def sample_trends(test_db):
    """Create sample trends in the database."""
    trends = [
        Trend(
            period="24h",
            name="Bitcoin Rally",
            description="BTC showing strong momentum",
            score=9.0,
            signal_count=5,
            category="crypto",
            analyzed_at=datetime.utcnow(),
        ),
        Trend(
            period="24h",
            name="AI Developments",
            description="Major AI announcements",
            score=8.5,
            signal_count=3,
            category="ai",
            analyzed_at=datetime.utcnow(),
        ),
    ]
    for trend in trends:
        test_db.add(trend)
    test_db.commit()
    return trends


@pytest.fixture
def sample_ideas(test_db):
    """Create sample ideas in the database."""
    ideas = [
        Idea(
            title="DeFi Dashboard",
            summary="Build a DeFi analytics dashboard",
            source_type="trend_based",
            status="pending",
            score=8.0,
        ),
        Idea(
            title="AI Trading Bot",
            summary="Automated trading using AI",
            source_type="traditional",
            status="in_debate",
            score=7.5,
        ),
    ]
    for idea in ideas:
        test_db.add(idea)
    test_db.commit()
    return ideas


@pytest.fixture
def sample_debates(test_db, sample_ideas):
    """Create sample debate sessions in the database."""
    idea = sample_ideas[0]
    session = DebateSession(
        idea_id=idea.id,
        phase="divergence",
        round_number=1,
        max_rounds=3,
        status="active",
        participants=["agent1", "agent2"],
    )
    test_db.add(session)
    test_db.commit()

    # Add messages
    messages = [
        DebateMessage(
            session_id=session.id,
            agent_id="agent1",
            agent_name="Founder",
            message_type="propose",
            content="I propose we build this.",
        ),
        DebateMessage(
            session_id=session.id,
            agent_id="agent2",
            agent_name="VC",
            message_type="support",
            content="I support this proposal.",
        ),
    ]
    for msg in messages:
        test_db.add(msg)
    test_db.commit()

    return [session]


@pytest.fixture
def sample_plans(test_db, sample_ideas):
    """Create sample plans in the database."""
    idea = sample_ideas[0]
    plan = Plan(
        idea_id=idea.id,
        title="DeFi Dashboard Plan",
        version=1,
        status="draft",
        prd_content="Product requirements...",
        architecture_content="System design...",
    )
    test_db.add(plan)
    test_db.commit()
    return [plan]


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "0.5.0"


class TestRootEndpoint:
    """Tests for / endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MOSS.AO API"
        assert data["version"] == "0.5.0"
        assert "endpoints" in data
        assert "/signals" in data["endpoints"].values()
        assert "/trends" in data["endpoints"].values()
        assert "/ideas" in data["endpoints"].values()


class TestStatusEndpoint:
    """Tests for /status endpoint."""

    def test_status_endpoint(self, client, sample_signals):
        """Test status endpoint returns system status."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["operational", "degraded"]
        assert "components" in data
        assert "stats" in data
        assert "agents_active" in data["stats"]


class TestSignalsEndpoint:
    """Tests for /signals endpoint."""

    def test_get_signals_empty(self, client):
        """Test getting signals when none exist."""
        response = client.get("/signals")
        assert response.status_code == 200
        data = response.json()
        assert data["signals"] == []
        assert data["total"] == 0

    def test_get_signals_with_data(self, client, sample_signals):
        """Test getting signals with data."""
        response = client.get("/signals")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 3
        assert data["total"] == 3

    def test_get_signals_with_limit(self, client, sample_signals):
        """Test getting signals with limit."""
        response = client.get("/signals?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        assert data["limit"] == 2

    def test_get_signals_filter_by_source(self, client, sample_signals):
        """Test filtering signals by source."""
        response = client.get("/signals?source=rss")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        for signal in data["signals"]:
            assert signal["source"] == "rss"

    def test_get_signals_filter_by_category(self, client, sample_signals):
        """Test filtering signals by category."""
        response = client.get("/signals?category=ai")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 1
        assert data["signals"][0]["category"] == "ai"

    def test_get_signals_filter_by_min_score(self, client, sample_signals):
        """Test filtering signals by minimum score."""
        response = client.get("/signals?min_score=8.0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        for signal in data["signals"]:
            assert signal["score"] >= 8.0


class TestTrendsEndpoint:
    """Tests for /trends endpoint."""

    def test_get_trends_empty(self, client):
        """Test getting trends when none exist."""
        response = client.get("/trends")
        assert response.status_code == 200
        data = response.json()
        assert data["trends"] == []

    def test_get_trends_with_data(self, client, sample_trends):
        """Test getting trends with data."""
        response = client.get("/trends")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) == 2
        assert data["period"] == "24h"

    def test_get_trends_filter_by_category(self, client, sample_trends):
        """Test filtering trends by category."""
        response = client.get("/trends?category=crypto")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) == 1
        assert data["trends"][0]["category"] == "crypto"


class TestIdeasEndpoint:
    """Tests for /ideas endpoint."""

    def test_get_ideas_empty(self, client):
        """Test getting ideas when none exist."""
        response = client.get("/ideas")
        assert response.status_code == 200
        data = response.json()
        assert data["ideas"] == []

    def test_get_ideas_with_data(self, client, sample_ideas):
        """Test getting ideas with data."""
        response = client.get("/ideas")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ideas"]) == 2
        assert "status_counts" in data

    def test_get_ideas_filter_by_status(self, client, sample_ideas):
        """Test filtering ideas by status."""
        response = client.get("/ideas?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ideas"]) == 1
        assert data["ideas"][0]["status"] == "pending"

    def test_get_idea_detail(self, client, sample_ideas):
        """Test getting idea detail."""
        idea_id = sample_ideas[0].id
        response = client.get(f"/ideas/{idea_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["idea"]["title"] == "DeFi Dashboard"

    def test_get_idea_detail_not_found(self, client):
        """Test getting non-existent idea."""
        response = client.get("/ideas/nonexistent-id")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestPlansEndpoint:
    """Tests for /plans endpoint."""

    def test_get_plans_empty(self, client):
        """Test getting plans when none exist."""
        response = client.get("/plans")
        assert response.status_code == 200
        data = response.json()
        assert data["plans"] == []

    def test_get_plans_with_data(self, client, sample_plans):
        """Test getting plans with data."""
        response = client.get("/plans")
        assert response.status_code == 200
        data = response.json()
        assert len(data["plans"]) == 1

    def test_get_plan_detail(self, client, sample_plans):
        """Test getting plan detail."""
        plan_id = sample_plans[0].id
        response = client.get(f"/plans/{plan_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "DeFi Dashboard Plan"
        assert "prd_content" in data


class TestDebatesEndpoint:
    """Tests for /debates endpoint."""

    def test_get_debates_empty(self, client):
        """Test getting debates when none exist."""
        response = client.get("/debates")
        assert response.status_code == 200
        data = response.json()
        assert data["debates"] == []

    def test_get_debates_with_data(self, client, sample_debates):
        """Test getting debates with data."""
        response = client.get("/debates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["debates"]) == 1

    def test_get_debates_filter_by_status(self, client, sample_debates):
        """Test filtering debates by status."""
        response = client.get("/debates?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["debates"]) == 1

    def test_get_debate_detail(self, client, sample_debates):
        """Test getting debate detail with messages."""
        session_id = sample_debates[0].id
        response = client.get(f"/debates/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["debate"]["phase"] == "divergence"
        assert data["message_count"] == 2
        assert len(data["messages"]) == 2


class TestUsageEndpoint:
    """Tests for /usage endpoint."""

    def test_get_usage_empty(self, client):
        """Test getting usage when none recorded."""
        response = client.get("/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["today"]["total_cost"] == 0
        assert data["month_total"] == 0


class TestActivityEndpoint:
    """Tests for /activity endpoint."""

    def test_get_activity_empty(self, client):
        """Test getting activity when none exist."""
        response = client.get("/activity")
        assert response.status_code == 200
        data = response.json()
        assert data["activities"] == []


class TestAgentsEndpoint:
    """Tests for /agents endpoint."""

    def test_get_all_agents(self, client):
        """Test getting all agents."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 34  # 16 + 8 + 10
        assert len(data["agents"]) == 34
        # Verify agent structure
        agent = data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "role" in agent
        assert "phase" in agent
        assert "personality" in agent
        assert "thinking" in agent["personality"]
        assert "decision" in agent["personality"]

    def test_get_agents_by_phase(self, client):
        """Test getting agents by phase."""
        response = client.get("/agents?phase=divergence")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 16
        for agent in data["agents"]:
            assert agent["phase"] == "divergence"

    def test_get_convergence_agents(self, client):
        """Test getting convergence agents."""
        response = client.get("/agents?phase=convergence")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 8
        for agent in data["agents"]:
            assert agent["phase"] == "convergence"

    def test_get_planning_agents(self, client):
        """Test getting planning agents."""
        response = client.get("/agents?phase=planning")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        for agent in data["agents"]:
            assert agent["phase"] == "planning"
