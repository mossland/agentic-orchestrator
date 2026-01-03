"""Tests for state management module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from agentic_orchestrator.state import State, Stage, Iteration, Limits, Quality


class TestStage:
    """Tests for Stage enum."""

    def test_stage_from_string(self):
        """Test creating Stage from string."""
        assert Stage.from_string("IDEATION") == Stage.IDEATION
        assert Stage.from_string("ideation") == Stage.IDEATION
        assert Stage.from_string("PLANNING_DRAFT") == Stage.PLANNING_DRAFT

    def test_stage_from_string_invalid(self):
        """Test invalid stage string raises error."""
        with pytest.raises(ValueError):
            Stage.from_string("INVALID_STAGE")

    def test_next_stage(self):
        """Test stage transitions."""
        assert Stage.IDEATION.next_stage() == Stage.PLANNING_DRAFT
        assert Stage.PLANNING_DRAFT.next_stage() == Stage.PLANNING_REVIEW
        assert Stage.PLANNING_REVIEW.next_stage() == Stage.DEV
        assert Stage.DEV.next_stage() == Stage.QA
        assert Stage.QA.next_stage() == Stage.DONE
        assert Stage.DONE.next_stage() is None
        assert Stage.PAUSED_QUOTA.next_stage() is None

    def test_can_iterate(self):
        """Test which stages support iteration."""
        assert Stage.PLANNING_REVIEW.can_iterate() is True
        assert Stage.QA.can_iterate() is True
        assert Stage.IDEATION.can_iterate() is False
        assert Stage.DEV.can_iterate() is False


class TestState:
    """Tests for State class."""

    def test_default_state(self):
        """Test default state values."""
        state = State()
        assert state.stage == Stage.IDEATION
        assert state.project_id is None
        assert state.iteration.planning == 0
        assert state.iteration.dev == 0

    def test_state_save_load(self):
        """Test saving and loading state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create and save state
            state = State()
            state.project_id = "test-project"
            state.stage = Stage.PLANNING_DRAFT
            state.iteration.planning = 2
            state.save(base_path)

            # Load state
            loaded = State.load(base_path)

            assert loaded.project_id == "test-project"
            assert loaded.stage == Stage.PLANNING_DRAFT
            assert loaded.iteration.planning == 2

    def test_state_transition(self):
        """Test stage transitions."""
        state = State()
        state.transition_to(Stage.PLANNING_DRAFT)

        assert state.stage == Stage.PLANNING_DRAFT
        assert state.timestamps.stage_started is not None

    def test_state_advance(self):
        """Test advancing to next stage."""
        state = State()
        assert state.stage == Stage.IDEATION

        result = state.advance()
        assert result is True
        assert state.stage == Stage.PLANNING_DRAFT

        # Advance to DONE
        state.stage = Stage.QA
        state.advance()
        assert state.stage == Stage.DONE

        # Cannot advance from DONE
        result = state.advance()
        assert result is False

    def test_increment_planning(self):
        """Test planning iteration increment."""
        state = State()
        state.limits.planning_max = 3

        assert state.increment_planning() is True
        assert state.iteration.planning == 1

        assert state.increment_planning() is True
        assert state.iteration.planning == 2

        assert state.increment_planning() is True
        assert state.iteration.planning == 3

        # Exceeds limit
        assert state.increment_planning() is False
        assert state.iteration.planning == 4

    def test_increment_dev(self):
        """Test dev iteration increment."""
        state = State()
        state.limits.dev_max = 2

        assert state.increment_dev() is True
        assert state.iteration.dev == 1

        assert state.increment_dev() is True
        assert state.iteration.dev == 2

        assert state.increment_dev() is False

    def test_reset_for_new_project(self):
        """Test resetting state for new project."""
        state = State()
        state.stage = Stage.QA
        state.iteration.planning = 3
        state.iteration.dev = 5
        state.quality.review_score = 8.5

        state.reset_for_new_project("new-project")

        assert state.project_id == "new-project"
        assert state.stage == Stage.IDEATION
        assert state.iteration.planning == 0
        assert state.iteration.dev == 0
        assert state.quality.review_score is None
        assert state.timestamps.created is not None

    def test_pause_for_quota(self):
        """Test pausing for quota issues."""
        state = State()
        state.pause_for_quota("OpenAI quota exceeded")

        assert state.stage == Stage.PAUSED_QUOTA
        assert state.errors.paused_reason == "OpenAI quota exceeded"
        assert state.is_paused() is True

    def test_error_tracking(self):
        """Test error tracking."""
        state = State()

        state.set_error("First error")
        assert state.errors.last_error == "First error"
        assert state.errors.error_count == 1

        state.set_error("Second error")
        assert state.errors.last_error == "Second error"
        assert state.errors.error_count == 2

        state.clear_error()
        assert state.errors.last_error is None
        assert state.errors.error_count == 2  # Count persists

    def test_is_paused(self):
        """Test pause state detection."""
        state = State()
        assert state.is_paused() is False

        state.stage = Stage.PAUSED_QUOTA
        assert state.is_paused() is True

        state.stage = Stage.ERROR
        assert state.is_paused() is True

    def test_is_complete(self):
        """Test completion detection."""
        state = State()
        assert state.is_complete() is False

        state.stage = Stage.DONE
        assert state.is_complete() is True

    def test_can_continue(self):
        """Test continue capability."""
        state = State()
        assert state.can_continue() is True

        state.stage = Stage.PAUSED_QUOTA
        assert state.can_continue() is False

        state.stage = Stage.DONE
        assert state.can_continue() is False

    def test_meets_quality_threshold(self):
        """Test quality threshold check."""
        state = State()
        state.quality.required_score = 7.0

        # No score yet
        assert state.meets_quality_threshold() is False

        # Below threshold
        state.quality.review_score = 6.5
        assert state.meets_quality_threshold() is False

        # At threshold
        state.quality.review_score = 7.0
        assert state.meets_quality_threshold() is True

        # Above threshold
        state.quality.review_score = 8.5
        assert state.meets_quality_threshold() is True

    def test_state_str(self):
        """Test string representation."""
        state = State()
        state.project_id = "test-123"
        state.stage = Stage.DEV
        state.iteration.planning = 2
        state.iteration.dev = 1

        str_repr = str(state)
        assert "DEV" in str_repr
        assert "test-123" in str_repr

    def test_state_to_dict(self):
        """Test state serialization."""
        state = State()
        state.project_id = "test-project"
        state.stage = Stage.PLANNING_DRAFT

        data = state._to_dict()

        assert data["stage"] == "PLANNING_DRAFT"
        assert data["project_id"] == "test-project"
        assert "iteration" in data
        assert "limits" in data
        assert "quality" in data
