"""Tests for the main orchestrator."""

import tempfile
from pathlib import Path

import pytest

from agentic_orchestrator.orchestrator import Orchestrator
from agentic_orchestrator.state import State, Stage


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_init_project(self):
        """Test project initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create a git repo for testing
            import subprocess
            subprocess.run(["git", "init"], cwd=base, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=base,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=base,
                capture_output=True
            )

            orchestrator = Orchestrator(base_path=base, dry_run=True)

            project_id = orchestrator.init_project()

            assert project_id is not None
            assert orchestrator.state.project_id == project_id
            assert orchestrator.state.stage == Stage.IDEATION

    def test_init_project_custom_id(self):
        """Test project initialization with custom ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)

            project_id = orchestrator.init_project("my-custom-project")

            assert project_id == "my-custom-project"
            assert orchestrator.state.project_id == "my-custom-project"

    def test_status(self):
        """Test status retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project("test-project")

            status = orchestrator.status()

            assert status["project_id"] == "test-project"
            assert status["stage"] == "IDEATION"
            assert "iteration" in status
            assert "quality" in status
            assert "flags" in status
            assert status["dry_run"] is True

    def test_status_flags(self):
        """Test status flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project()

            # Initial state
            status = orchestrator.status()
            assert status["flags"]["can_continue"] is True
            assert status["flags"]["is_paused"] is False
            assert status["flags"]["is_complete"] is False

            # Paused state
            orchestrator.state.stage = Stage.PAUSED_QUOTA
            status = orchestrator.status()
            assert status["flags"]["is_paused"] is True
            assert status["flags"]["can_continue"] is False

            # Complete state
            orchestrator.state.stage = Stage.DONE
            status = orchestrator.status()
            assert status["flags"]["is_complete"] is True
            assert status["flags"]["can_continue"] is False

    def test_reset_keep_project(self):
        """Test reset while keeping project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project("my-project")
            orchestrator.state.stage = Stage.DEV
            orchestrator.state.iteration.planning = 3

            orchestrator.reset(keep_project=True)

            assert orchestrator.state.project_id == "my-project"
            assert orchestrator.state.stage == Stage.IDEATION
            assert orchestrator.state.iteration.planning == 0

    def test_reset_new_project(self):
        """Test full reset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project("my-project")

            orchestrator.reset(keep_project=False)

            assert orchestrator.state.project_id is None

    def test_step_paused_state(self):
        """Test step when paused."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project()
            orchestrator.state.pause_for_quota("Test pause")

            result = orchestrator.step()

            assert result.success is False
            assert "paused" in result.error.lower()

    def test_step_complete_state(self):
        """Test step when complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project()
            orchestrator.state.stage = Stage.DONE

            result = orchestrator.step()

            assert result.success is True
            assert "complete" in result.message.lower()

    def test_save_state(self):
        """Test state persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create and save
            orchestrator = Orchestrator(base_path=base, dry_run=True)
            orchestrator.init_project("persist-test")
            orchestrator.state.stage = Stage.DEV
            orchestrator.save_state()

            # Load in new orchestrator
            orchestrator2 = Orchestrator(base_path=base, dry_run=True)

            assert orchestrator2.state.project_id == "persist-test"
            assert orchestrator2.state.stage == Stage.DEV


class TestOrchestratorDryRun:
    """Tests for dry run mode."""

    def test_dry_run_flag(self):
        """Test dry run flag propagation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            orchestrator = Orchestrator(base_path=base, dry_run=True)

            assert orchestrator.dry_run is True

    def test_dry_run_from_env(self):
        """Test dry run from environment."""
        import os

        os.environ["DRY_RUN"] = "true"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                base = Path(tmpdir)
                orchestrator = Orchestrator(base_path=base)
                # Should pick up from env/config
                assert orchestrator.config.dry_run is True
        finally:
            del os.environ["DRY_RUN"]
