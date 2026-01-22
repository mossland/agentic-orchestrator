"""Tests for multi-stage debate system."""

import pytest
from datetime import datetime
from agentic_orchestrator.debate.protocol import (
    DebatePhase,
    MessageType,
    DebateMessage,
    DebateRound,
    PhaseResult,
    DebateProtocolConfig,
)


class TestDebatePhase:
    """Tests for DebatePhase enum."""

    def test_phase_values(self):
        """Test phase enum values."""
        assert DebatePhase.DIVERGENCE.value == "divergence"
        assert DebatePhase.CONVERGENCE.value == "convergence"
        assert DebatePhase.PLANNING.value == "planning"

    def test_all_phases(self):
        """Test all phases are defined."""
        phases = list(DebatePhase)
        assert len(phases) == 3


class TestMessageType:
    """Tests for MessageType enum."""

    def test_divergence_message_types(self):
        """Test divergence-related message types."""
        assert MessageType.INITIAL_IDEA.value == "initial_idea"
        assert MessageType.ANALYSIS.value == "analysis"

    def test_convergence_message_types(self):
        """Test convergence-related message types."""
        assert MessageType.EVALUATION.value == "evaluation"
        assert MessageType.VOTE.value == "vote"

    def test_planning_message_types(self):
        """Test planning-related message types."""
        assert MessageType.PLAN_DRAFT.value == "plan_draft"
        assert MessageType.PLAN_REVIEW.value == "plan_review"
        assert MessageType.FINAL_PLAN.value == "final_plan"


class TestDebateMessage:
    """Tests for DebateMessage dataclass."""

    def test_message_creation(self):
        """Test creating a debate message."""
        msg = DebateMessage(
            id="msg-001",
            phase=DebatePhase.DIVERGENCE,
            round=1,
            agent_id="agent-001",
            agent_name="Innovator",
            message_type=MessageType.INITIAL_IDEA,
            content="Here's my idea for a new feature.",
        )
        assert msg.id == "msg-001"
        assert msg.phase == DebatePhase.DIVERGENCE
        assert msg.round == 1
        assert msg.agent_id == "agent-001"
        assert msg.agent_name == "Innovator"
        assert msg.message_type == MessageType.INITIAL_IDEA
        assert msg.content == "Here's my idea for a new feature."

    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = DebateMessage(
            id="msg-002",
            phase=DebatePhase.CONVERGENCE,
            round=1,
            agent_id="agent-002",
            agent_name="Analyst",
            message_type=MessageType.EVALUATION,
            content="I support this idea.",
            metadata={"confidence": 0.85, "reasoning": "Strong market fit"},
        )
        assert msg.metadata["confidence"] == 0.85
        assert "reasoning" in msg.metadata

    def test_message_with_references(self):
        """Test message referencing other messages."""
        msg = DebateMessage(
            id="msg-003",
            phase=DebatePhase.CONVERGENCE,
            round=2,
            agent_id="agent-003",
            agent_name="Synthesizer",
            message_type=MessageType.SYNTHESIS,
            content="Merging ideas from messages 1 and 2.",
            references=["msg-001", "msg-002"],
        )
        assert len(msg.references) == 2
        assert "msg-001" in msg.references

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = DebateMessage(
            id="msg-004",
            phase=DebatePhase.PLANNING,
            round=1,
            agent_id="agent-004",
            agent_name="Planner",
            message_type=MessageType.PLAN_DRAFT,
            content="Draft plan content.",
            score=0.9,
        )
        data = msg.to_dict()
        assert data["id"] == "msg-004"
        assert data["phase"] == "planning"
        assert data["message_type"] == "plan_draft"
        assert data["score"] == 0.9

    def test_message_default_timestamp(self):
        """Test message has default timestamp."""
        msg = DebateMessage(
            id="msg-005",
            phase=DebatePhase.DIVERGENCE,
            round=1,
            agent_id="agent-001",
            agent_name="Test",
            message_type=MessageType.INITIAL_IDEA,
            content="Test content",
        )
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)


class TestDebateRound:
    """Tests for DebateRound dataclass."""

    def test_round_creation(self):
        """Test creating a debate round."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Generate ideas for DeFi dashboard",
        )
        assert round_obj.round_num == 1
        assert round_obj.phase == DebatePhase.DIVERGENCE
        assert round_obj.topic == "Generate ideas for DeFi dashboard"
        assert round_obj.messages == []

    def test_add_message_to_round(self):
        """Test adding messages to a round."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Test topic",
        )
        msg = DebateMessage(
            id="msg-001",
            phase=DebatePhase.DIVERGENCE,
            round=1,
            agent_id="agent-001",
            agent_name="Test",
            message_type=MessageType.INITIAL_IDEA,
            content="Test idea",
        )
        round_obj.add_message(msg)
        assert len(round_obj.messages) == 1
        assert round_obj.messages[0].id == "msg-001"

    def test_round_with_summary(self):
        """Test round with summary."""
        round_obj = DebateRound(
            round_num=2,
            phase=DebatePhase.CONVERGENCE,
            topic="Evaluate ideas",
            summary="Three main ideas emerged: A, B, and C.",
            key_points=["Idea A has strong market fit", "Idea B is technically feasible"],
        )
        assert round_obj.summary is not None
        assert len(round_obj.key_points) == 2

    def test_round_with_decisions(self):
        """Test round with decisions."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.PLANNING,
            topic="Create final plan",
            decisions=[
                {"idea_id": "idea-001", "action": "approve", "votes": 4},
                {"idea_id": "idea-002", "action": "reject", "votes": 2},
            ],
        )
        assert len(round_obj.decisions) == 2
        assert round_obj.decisions[0]["action"] == "approve"

    def test_round_to_dict(self):
        """Test round serialization."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Test topic",
        )
        data = round_obj.to_dict()
        assert data["round_num"] == 1
        assert data["phase"] == "divergence"
        assert data["messages"] == []


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """Test creating a phase result."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Test topic",
        )
        result = PhaseResult(
            phase=DebatePhase.DIVERGENCE,
            rounds=[round_obj],
            output={"ideas_generated": 15, "top_ideas": ["idea-1", "idea-2"]},
            duration_seconds=120.5,
            total_tokens=5000,
            total_cost=0.15,
        )
        assert result.phase == DebatePhase.DIVERGENCE
        assert len(result.rounds) == 1
        assert result.output["ideas_generated"] == 15
        assert result.duration_seconds == 120.5
        assert result.total_cost == 0.15

    def test_phase_result_to_dict(self):
        """Test phase result serialization."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.CONVERGENCE,
            topic="Evaluate",
        )
        result = PhaseResult(
            phase=DebatePhase.CONVERGENCE,
            rounds=[round_obj],
            output={"selected_ideas": 5},
            duration_seconds=90.0,
            total_tokens=3000,
            total_cost=0.10,
        )
        data = result.to_dict()
        assert data["phase"] == "convergence"
        assert len(data["rounds"]) == 1
        assert data["output"]["selected_ideas"] == 5


class TestDebateProtocolConfig:
    """Tests for DebateProtocolConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DebateProtocolConfig()
        # Divergence defaults
        assert config.divergence_rounds == 3
        assert config.divergence_agents_per_round == 8
        assert config.min_ideas_to_generate == 20
        # Convergence defaults
        assert config.convergence_rounds == 2
        assert config.top_ideas_to_keep == 5
        # Planning defaults
        assert config.planning_rounds == 2
        assert config.min_approval_ratio == 0.7

    def test_custom_config(self):
        """Test custom configuration."""
        config = DebateProtocolConfig(
            divergence_rounds=5,
            convergence_rounds=3,
            planning_rounds=3,
            top_ideas_to_keep=10,
        )
        assert config.divergence_rounds == 5
        assert config.convergence_rounds == 3
        assert config.top_ideas_to_keep == 10

    def test_temperature_settings(self):
        """Test temperature configuration for different phases."""
        config = DebateProtocolConfig()
        # Higher temperature for creativity in divergence
        assert config.temperature_divergence == 0.9
        # Lower temperature for analysis in convergence
        assert config.temperature_convergence == 0.5
        # Medium temperature for planning
        assert config.temperature_planning == 0.7

    def test_timeout_settings(self):
        """Test timeout configuration."""
        config = DebateProtocolConfig()
        assert config.agent_timeout_seconds == 120
        assert config.round_timeout_seconds == 600

    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = DebateProtocolConfig(
            divergence_rounds=4,
            min_ideas_to_generate=30,
        )
        data = config.to_dict()
        assert data["divergence_rounds"] == 4
        assert data["min_ideas_to_generate"] == 30
        assert "top_ideas_to_keep" in data


class TestDebateFlow:
    """Integration-like tests for debate flow."""

    def test_complete_divergence_round(self):
        """Test a complete divergence round with multiple messages."""
        round_obj = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Generate DeFi dashboard ideas",
        )

        # Simulate multiple agents contributing ideas
        agents = [
            ("agent-001", "Visionary"),
            ("agent-002", "Technologist"),
            ("agent-003", "Market Analyst"),
        ]

        for i, (agent_id, name) in enumerate(agents):
            msg = DebateMessage(
                id=f"msg-{i+1:03d}",
                phase=DebatePhase.DIVERGENCE,
                round=1,
                agent_id=agent_id,
                agent_name=name,
                message_type=MessageType.INITIAL_IDEA,
                content=f"Idea from {name}",
                score=0.8 + i * 0.05,
            )
            round_obj.add_message(msg)

        assert len(round_obj.messages) == 3
        # Verify all messages have unique IDs
        ids = [m.id for m in round_obj.messages]
        assert len(ids) == len(set(ids))

    def test_phase_transition(self):
        """Test transitioning between phases."""
        # Divergence result
        div_round = DebateRound(
            round_num=1,
            phase=DebatePhase.DIVERGENCE,
            topic="Generate ideas",
        )
        div_result = PhaseResult(
            phase=DebatePhase.DIVERGENCE,
            rounds=[div_round],
            output={"ideas": ["idea-1", "idea-2", "idea-3"]},
            duration_seconds=60.0,
            total_tokens=2000,
            total_cost=0.05,
        )

        # Convergence should receive ideas from divergence
        conv_round = DebateRound(
            round_num=1,
            phase=DebatePhase.CONVERGENCE,
            topic="Evaluate ideas: idea-1, idea-2, idea-3",
        )
        conv_result = PhaseResult(
            phase=DebatePhase.CONVERGENCE,
            rounds=[conv_round],
            output={"selected": ["idea-1"], "rejected": ["idea-2", "idea-3"]},
            duration_seconds=45.0,
            total_tokens=1500,
            total_cost=0.04,
        )

        # Verify phase values
        assert div_result.phase == DebatePhase.DIVERGENCE
        assert conv_result.phase == DebatePhase.CONVERGENCE
        assert len(conv_result.output["selected"]) == 1

    def test_message_referencing(self):
        """Test messages referencing other messages."""
        # Initial idea
        idea_msg = DebateMessage(
            id="msg-001",
            phase=DebatePhase.DIVERGENCE,
            round=1,
            agent_id="agent-001",
            agent_name="Innovator",
            message_type=MessageType.INITIAL_IDEA,
            content="Build a yield optimizer",
        )

        # Support message referencing the idea
        support_msg = DebateMessage(
            id="msg-002",
            phase=DebatePhase.CONVERGENCE,
            round=1,
            agent_id="agent-002",
            agent_name="Analyst",
            message_type=MessageType.SUPPORT,
            content="I support the yield optimizer idea.",
            references=["msg-001"],
        )

        # Challenge message also referencing
        challenge_msg = DebateMessage(
            id="msg-003",
            phase=DebatePhase.CONVERGENCE,
            round=1,
            agent_id="agent-003",
            agent_name="Devil's Advocate",
            message_type=MessageType.CHALLENGE,
            content="The market is saturated.",
            references=["msg-001"],
        )

        assert support_msg.references == ["msg-001"]
        assert challenge_msg.references == ["msg-001"]
