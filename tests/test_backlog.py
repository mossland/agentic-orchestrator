"""Tests for the backlog workflow module."""
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from agentic_orchestrator.github_client import GitHubClient, GitHubIssue, Labels, GitHubAPIError


class TestLabels:
    """Test Labels constants."""

    def test_type_labels(self):
        """Test type label constants."""
        assert Labels.TYPE_IDEA == "type:idea"
        assert Labels.TYPE_PLAN == "type:plan"

    def test_status_labels(self):
        """Test status label constants."""
        assert Labels.STATUS_BACKLOG == "status:backlog"
        assert Labels.STATUS_PLANNED == "status:planned"
        assert Labels.STATUS_IN_DEV == "status:in-dev"
        assert Labels.STATUS_DONE == "status:done"

    def test_promotion_labels(self):
        """Test promotion label constants."""
        assert Labels.PROMOTE_TO_PLAN == "promote:to-plan"
        assert Labels.PROMOTE_TO_DEV == "promote:to-dev"

    def test_processed_labels(self):
        """Test processed label constants."""
        assert Labels.PROCESSED_TO_PLAN == "processed:to-plan"
        assert Labels.PROCESSED_TO_DEV == "processed:to-dev"

    def test_all_labels_dict(self):
        """Test all labels dictionary."""
        all_labels = Labels.ALL_LABELS
        assert Labels.TYPE_IDEA in all_labels
        assert Labels.PROMOTE_TO_PLAN in all_labels
        assert Labels.GENERATED_BY_ORCHESTRATOR in all_labels
        # Check structure
        assert "color" in all_labels[Labels.TYPE_IDEA]
        assert "description" in all_labels[Labels.TYPE_IDEA]


class TestGitHubIssue:
    """Test GitHubIssue dataclass."""

    def test_issue_creation(self):
        """Test creating a GitHubIssue."""
        issue = GitHubIssue(
            number=1,
            title="Test Issue",
            body="Test body",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="https://github.com/test/repo/issues/1",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.number == 1
        assert issue.title == "Test Issue"
        assert "type:idea" in issue.labels

    def test_has_label(self):
        """Test has_label method."""
        issue = GitHubIssue(
            number=1,
            title="Test",
            body="",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.has_label("type:idea") is True
        assert issue.has_label("type:plan") is False

    def test_has_any_label(self):
        """Test has_any_label method."""
        issue = GitHubIssue(
            number=1,
            title="Test",
            body="",
            labels=["type:idea", "status:backlog"],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert issue.has_any_label(["type:idea", "type:plan"]) is True
        assert issue.has_any_label(["type:plan", "status:done"]) is False

    def test_from_api_response(self):
        """Test creating issue from API response."""
        api_response = {
            "number": 42,
            "title": "API Issue",
            "body": "Body text",
            "labels": [{"name": "type:idea"}, {"name": "status:backlog"}],
            "state": "open",
            "html_url": "https://github.com/test/repo/issues/42",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "user": {"login": "testuser"},
            "assignees": []
        }
        issue = GitHubIssue.from_api_response(api_response)
        assert issue.number == 42
        assert issue.title == "API Issue"
        assert issue.labels == ["type:idea", "status:backlog"]
        assert issue.user == "testuser"


class TestGitHubClient:
    """Test GitHubClient class."""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "test-token",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo"
        }):
            client = GitHubClient()
            assert client.token == "test-token"
            assert client.owner == "test-owner"
            assert client.repo == "test-repo"
            client.close()

    def test_init_with_params(self):
        """Test initialization with parameters."""
        client = GitHubClient(
            token="param-token",
            owner="param-owner",
            repo="param-repo"
        )
        assert client.token == "param-token"
        assert client.owner == "param-owner"
        assert client.repo == "param-repo"
        client.close()

    def test_init_missing_token(self):
        """Test initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("GITHUB_OWNER", None)
            os.environ.pop("GITHUB_REPO", None)
            with pytest.raises(GitHubAPIError, match="GITHUB_TOKEN"):
                GitHubClient(owner="test", repo="test")

    def test_repo_path(self):
        """Test repo_path property."""
        client = GitHubClient(
            token="test",
            owner="testowner",
            repo="testrepo"
        )
        assert client.repo_path == "testowner/testrepo"
        client.close()

    def test_context_manager(self):
        """Test context manager support."""
        with GitHubClient(token="test", owner="test", repo="test") as client:
            assert client is not None


class TestBacklogOrchestrator:
    """Test BacklogOrchestrator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test BacklogOrchestrator initialization."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        orchestrator = BacklogOrchestrator()
        assert orchestrator.github is not None
        assert orchestrator.dry_run is True

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_get_status(self):
        """Test getting backlog status."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        orchestrator = BacklogOrchestrator()

        with patch.object(orchestrator.github, "find_backlog_ideas", return_value=[]):
            with patch.object(orchestrator.github, "find_backlog_plans", return_value=[]):
                with patch.object(orchestrator.github, "find_ideas_to_promote", return_value=[]):
                    with patch.object(orchestrator.github, "find_plans_to_promote", return_value=[]):
                        status = orchestrator.get_status()

                        assert "backlog" in status
                        assert "pending_promotion" in status
                        assert "issues" in status
                        assert status["backlog"]["ideas"] == 0
                        assert status["pending_promotion"]["ideas_to_plan"] == 0


class TestIdeaGenerator:
    """Test IdeaGenerator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test IdeaGenerator initialization."""
        from agentic_orchestrator.backlog import IdeaGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = IdeaGenerator(github=github, dry_run=True)
        assert generator.github is not None
        assert generator.dry_run is True
        github.close()


class TestPlanGenerator:
    """Test PlanGenerator class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test PlanGenerator initialization."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = PlanGenerator(github=github, dry_run=True)
        assert generator.github is not None
        assert generator.dry_run is True
        github.close()


class TestDevScaffolder:
    """Test DevScaffolder class."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_init(self):
        """Test DevScaffolder initialization."""
        from agentic_orchestrator.backlog import DevScaffolder

        github = GitHubClient(token="test", owner="test", repo="test")
        scaffolder = DevScaffolder(github=github, dry_run=True)
        assert scaffolder.github is not None
        assert scaffolder.dry_run is True
        github.close()


# =============================================================================
# v0.2.1 Tests: Idempotency, Lock Timeout, Rollback
# =============================================================================


class TestPlanGeneratorIdempotency:
    """Test PlanGenerator idempotency protection."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_already_processed_idea(self):
        """Test that already processed ideas are skipped."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = PlanGenerator(github=github, dry_run=False)

        # Create idea with processed label
        idea = GitHubIssue(
            number=1,
            title="[IDEA] Test Idea",
            body="Test body",
            labels=[Labels.TYPE_IDEA, Labels.PROCESSED_TO_PLAN],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        result = generator.generate_plan_from_idea(idea)
        assert result is None
        github.close()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_already_planned_idea(self):
        """Test that already planned ideas are skipped."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = PlanGenerator(github=github, dry_run=False)

        # Create idea with planned status
        idea = GitHubIssue(
            number=1,
            title="[IDEA] Test Idea",
            body="Test body",
            labels=[Labels.TYPE_IDEA, Labels.STATUS_PLANNED],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        result = generator.generate_plan_from_idea(idea)
        assert result is None
        github.close()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_idea_with_existing_plan(self):
        """Test that ideas with existing plans are skipped."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = GitHubClient(token="test", owner="test", repo="test")
        generator = PlanGenerator(github=github, dry_run=False)

        # Create idea without processed labels
        idea = GitHubIssue(
            number=1,
            title="[IDEA] Test Idea",
            body="Test body",
            labels=[Labels.TYPE_IDEA, Labels.PROMOTE_TO_PLAN],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        # Mock existing plan search
        existing_plan = GitHubIssue(
            number=2,
            title="[PLAN] Test Idea",
            body="**Source Idea:** #1",
            labels=[Labels.TYPE_PLAN],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        with patch.object(generator, "_find_existing_plan_for_idea", return_value=[existing_plan]):
            result = generator.generate_plan_from_idea(idea)
            assert result is None

        github.close()


class TestDevScaffolderIdempotency:
    """Test DevScaffolder idempotency protection."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_already_processed_plan(self):
        """Test that already processed plans are skipped."""
        from agentic_orchestrator.backlog import DevScaffolder

        github = GitHubClient(token="test", owner="test", repo="test")
        scaffolder = DevScaffolder(github=github, dry_run=False)

        # Create plan with processed label
        plan = GitHubIssue(
            number=1,
            title="[PLAN] Test Plan",
            body="Test body",
            labels=[Labels.TYPE_PLAN, Labels.PROCESSED_TO_DEV],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        result = scaffolder.scaffold_from_plan(plan)
        assert result is None
        github.close()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_plan_already_in_dev(self):
        """Test that plans already in dev are skipped."""
        from agentic_orchestrator.backlog import DevScaffolder

        github = GitHubClient(token="test", owner="test", repo="test")
        scaffolder = DevScaffolder(github=github, dry_run=False)

        # Create plan with in-dev status
        plan = GitHubIssue(
            number=1,
            title="[PLAN] Test Plan",
            body="Test body",
            labels=[Labels.TYPE_PLAN, Labels.STATUS_IN_DEV],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        result = scaffolder.scaffold_from_plan(plan)
        assert result is None
        github.close()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_skip_plan_with_existing_project(self):
        """Test that plans with existing projects are skipped."""
        from agentic_orchestrator.backlog import DevScaffolder

        github = GitHubClient(token="test", owner="test", repo="test")

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            scaffolder = DevScaffolder(github=github, base_path=base_path, dry_run=False)

            # Create plan without processed labels
            plan = GitHubIssue(
                number=1,
                title="[PLAN] Test Plan",
                body="Test body",
                labels=[Labels.TYPE_PLAN, Labels.PROMOTE_TO_DEV],
                state="open",
                html_url="",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            )

            # Mock existing project found
            with patch.object(scaffolder, "_find_existing_project_for_plan", return_value="existing-project-123"):
                result = scaffolder.scaffold_from_plan(plan)
                assert result is None

        github.close()


class TestBacklogOrchestratorLockTimeout:
    """Test BacklogOrchestrator lock timeout mechanism."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_cleanup_stale_lock_by_timeout(self):
        """Test that stale locks are cleaned up after timeout."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Create agent directory
            lock_path = base_path / ".agent" / "orchestrator.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Write a stale lock (old timestamp)
            old_time = datetime.now() - timedelta(seconds=600)  # 10 minutes ago
            lock_path.write_text(f"12345\n{old_time.isoformat()}")

            # Mock config to return short timeout (300 seconds)
            def mock_get(*args, **kwargs):
                if args == ("orchestrator", "lock_timeout_seconds"):
                    return kwargs.get("default", 300)
                return kwargs.get("default")

            with patch.object(orchestrator.config, "get", side_effect=mock_get):
                orchestrator._cleanup_stale_lock()

            # Lock should be removed
            assert not lock_path.exists()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_cleanup_dead_process_lock(self):
        """Test that locks from dead processes are cleaned up."""
        from agentic_orchestrator.backlog import BacklogOrchestrator
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Create agent directory
            lock_path = base_path / ".agent" / "orchestrator.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Write a lock with recent timestamp but dead PID
            lock_path.write_text(f"999999\n{datetime.now().isoformat()}")

            # Mock _is_process_alive to return False
            with patch.object(orchestrator, "_is_process_alive", return_value=False):
                orchestrator._cleanup_stale_lock()

            # Lock should be removed
            assert not lock_path.exists()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_keep_valid_lock(self):
        """Test that valid locks are not removed."""
        from agentic_orchestrator.backlog import BacklogOrchestrator
        from datetime import datetime
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Create agent directory
            lock_path = base_path / ".agent" / "orchestrator.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Write a valid lock (recent timestamp, alive process)
            lock_path.write_text(f"{os.getpid()}\n{datetime.now().isoformat()}")

            orchestrator._cleanup_stale_lock()

            # Lock should still exist
            assert lock_path.exists()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_cleanup_malformed_lock(self):
        """Test that malformed lock files are cleaned up."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Create agent directory
            lock_path = base_path / ".agent" / "orchestrator.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Write malformed lock (missing timestamp)
            lock_path.write_text("12345")

            orchestrator._cleanup_stale_lock()

            # Lock should be removed
            assert not lock_path.exists()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_is_process_alive_current_process(self):
        """Test _is_process_alive returns True for current process."""
        from agentic_orchestrator.backlog import BacklogOrchestrator
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Current process should be alive
            assert orchestrator._is_process_alive(os.getpid()) is True

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DRY_RUN": "true"
    })
    def test_is_process_alive_dead_process(self):
        """Test _is_process_alive returns False for non-existent PID."""
        from agentic_orchestrator.backlog import BacklogOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            orchestrator = BacklogOrchestrator(base_path=base_path)

            # Very high PID that doesn't exist
            assert orchestrator._is_process_alive(9999999) is False


class TestPlanGeneratorRollback:
    """Test PlanGenerator rollback on failure."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test-token",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
    })
    def test_rollback_on_label_update_failure(self):
        """Test that created plan is closed when label update fails."""
        from agentic_orchestrator.backlog import PlanGenerator

        github = MagicMock(spec=GitHubClient)

        # Setup mock responses
        created_plan = GitHubIssue(
            number=2,
            title="[PLAN] Test",
            body="Plan body",
            labels=[Labels.TYPE_PLAN],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        github.create_issue.return_value = created_plan
        github.mark_idea_as_planned.side_effect = Exception("Label update failed")
        github.search_issues.return_value = []

        generator = PlanGenerator(github=github, dry_run=False)

        # Create idea
        idea = GitHubIssue(
            number=1,
            title="[IDEA] Test Idea",
            body="Test body",
            labels=[Labels.TYPE_IDEA, Labels.PROMOTE_TO_PLAN],
            state="open",
            html_url="",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

        # Mock claude
        mock_claude = MagicMock()
        mock_claude.chat.return_value = "## Plan content\nTest plan"
        generator._claude = mock_claude

        # Should raise the exception
        with pytest.raises(Exception, match="Label update failed"):
            generator.generate_plan_from_idea(idea)

        # Verify rollback was attempted - plan should be closed
        github.update_issue.assert_called_once()
        call_args = github.update_issue.call_args
        assert call_args[0][0] == 2  # plan number
        assert call_args[1]["state"] == "closed"
        assert "rollback:failed" in call_args[1]["labels"]
