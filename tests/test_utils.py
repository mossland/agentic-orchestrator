"""Tests for utility modules."""

import tempfile
from pathlib import Path

import pytest

from agentic_orchestrator.utils.files import (
    ensure_dir,
    ensure_parent,
    write_markdown,
    read_markdown,
    generate_project_id,
    get_project_dir,
    get_stage_dir,
    sanitize_filename,
)
from agentic_orchestrator.utils.git import GitHelper
from agentic_orchestrator.utils.config import (
    get_env,
    get_env_bool,
    get_env_int,
    validate_backlog_environment,
    validate_environment_for_command,
    EnvironmentValidationError,
)


class TestFileUtils:
    """Tests for file utility functions."""

    def test_ensure_dir(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            result = ensure_dir(new_dir)

            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_parent(self):
        """Test parent directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "new" / "nested" / "file.txt"
            result = ensure_parent(file_path)

            assert result == file_path
            assert file_path.parent.exists()

    def test_write_markdown(self):
        """Test writing markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"

            write_markdown(
                file_path,
                "# Hello\n\nWorld",
                title="Test Document",
                metadata={"author": "test"},
            )

            assert file_path.exists()
            content = file_path.read_text()

            assert "title: Test Document" in content
            assert "author: test" in content
            assert "# Hello" in content
            assert "World" in content

    def test_read_markdown(self):
        """Test reading markdown files with frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("""---
title: Test
author: me
---

# Content

Body text here.
""")

            content, metadata = read_markdown(file_path)

            assert metadata["title"] == "Test"
            assert metadata["author"] == "me"
            assert "# Content" in content
            assert "Body text here" in content

    def test_read_markdown_no_frontmatter(self):
        """Test reading markdown without frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("# Just Content\n\nNo frontmatter here.")

            content, metadata = read_markdown(file_path)

            assert metadata == {}
            assert "# Just Content" in content

    def test_read_markdown_nonexistent(self):
        """Test reading nonexistent file."""
        content, metadata = read_markdown(Path("/nonexistent/file.md"))
        assert content == ""
        assert metadata == {}

    def test_generate_project_id(self):
        """Test project ID generation."""
        id1 = generate_project_id()
        id2 = generate_project_id()

        # IDs should have expected format
        assert "-" in id1
        assert len(id1) > 10

        # IDs should be unique
        assert id1 != id2

    def test_get_project_dir(self):
        """Test project directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_dir = get_project_dir("test-123", base)

            assert project_dir == base / "projects" / "test-123"

    def test_get_stage_dir(self):
        """Test stage directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            ideation = get_stage_dir("test", "IDEATION", base)
            assert "01_ideation" in str(ideation)

            planning = get_stage_dir("test", "PLANNING_DRAFT", base)
            assert "02_planning" in str(planning)

            dev = get_stage_dir("test", "DEV", base)
            assert "03_implementation" in str(dev)

            qa = get_stage_dir("test", "QA", base)
            assert "04_quality" in str(qa)

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("hello world") == "hello_world"
        assert sanitize_filename("file:name") == "filename"
        assert sanitize_filename("a/b\\c") == "abc"
        assert sanitize_filename("...hidden") == "hidden"
        assert sanitize_filename("") == "unnamed"


class TestConfigUtils:
    """Tests for configuration utilities."""

    def test_get_env_default(self):
        """Test getting env with default."""
        result = get_env("NONEXISTENT_VAR_12345", default="fallback")
        assert result == "fallback"

    def test_get_env_bool(self):
        """Test boolean env parsing."""
        import os

        # Test true values
        os.environ["TEST_BOOL"] = "true"
        assert get_env_bool("TEST_BOOL") is True

        os.environ["TEST_BOOL"] = "1"
        assert get_env_bool("TEST_BOOL") is True

        os.environ["TEST_BOOL"] = "yes"
        assert get_env_bool("TEST_BOOL") is True

        # Test false values
        os.environ["TEST_BOOL"] = "false"
        assert get_env_bool("TEST_BOOL") is False

        os.environ["TEST_BOOL"] = "0"
        assert get_env_bool("TEST_BOOL") is False

        # Test default
        del os.environ["TEST_BOOL"]
        assert get_env_bool("TEST_BOOL", default=True) is True

    def test_get_env_int(self):
        """Test integer env parsing."""
        import os

        os.environ["TEST_INT"] = "42"
        assert get_env_int("TEST_INT") == 42

        os.environ["TEST_INT"] = "invalid"
        assert get_env_int("TEST_INT", default=10) == 10

        del os.environ["TEST_INT"]
        assert get_env_int("TEST_INT", default=5) == 5


class TestGitHelper:
    """Tests for Git helper utilities."""

    def test_mask_sensitive_data(self):
        """Test masking sensitive data."""
        # API keys
        text = "api_key=sk-1234567890abcdefghijklmnop"
        masked = GitHelper.mask_sensitive_data(text)
        assert "sk-1234567890" not in masked
        assert "MASKED" in masked

        # GitHub tokens
        text = "token: ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
        masked = GitHelper.mask_sensitive_data(text)
        assert "ghp_1234567890" not in masked
        assert "MASKED" in masked

        # Google API keys
        text = "key=AIzaSyA1234567890123456789012345678901234"
        masked = GitHelper.mask_sensitive_data(text)
        assert "AIzaSyA1234567890" not in masked
        assert "MASKED" in masked

    def test_mask_preserves_normal_text(self):
        """Test that normal text is preserved."""
        text = "This is normal text without secrets"
        masked = GitHelper.mask_sensitive_data(text)
        assert masked == text


# =============================================================================
# v0.2.1 Tests: Environment Validation
# =============================================================================


class TestEnvironmentValidation:
    """Tests for environment variable validation."""

    def test_validate_backlog_environment_success(self):
        """Test successful validation with all required variables."""
        import os
        from unittest.mock import patch

        env_vars = {
            "GITHUB_TOKEN": "ghp_test123",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo",
            "ANTHROPIC_API_KEY": "sk-ant-test123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_backlog_environment()

            assert result["valid"] is True
            assert result["github"]["valid"] is True
            assert result["llm"]["valid"] is True
            assert "Claude" in result["llm"]["available"]

    def test_validate_backlog_environment_missing_github(self):
        """Test validation fails when GitHub credentials are missing."""
        import os
        from unittest.mock import patch

        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_backlog_environment()

            assert "GITHUB_TOKEN" in exc_info.value.missing
            assert "GITHUB_OWNER" in exc_info.value.missing
            assert "GITHUB_REPO" in exc_info.value.missing

    def test_validate_backlog_environment_missing_llm(self):
        """Test validation fails when no LLM API key is present."""
        import os
        from unittest.mock import patch

        env_vars = {
            "GITHUB_TOKEN": "ghp_test123",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_backlog_environment()

            # Should mention LLM keys
            assert any("API_KEY" in m for m in exc_info.value.missing)

    def test_validate_backlog_environment_any_llm_is_enough(self):
        """Test that any single LLM API key is sufficient."""
        import os
        from unittest.mock import patch

        # Test with OpenAI only
        env_vars = {
            "GITHUB_TOKEN": "ghp_test123",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo",
            "OPENAI_API_KEY": "sk-test123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_backlog_environment()
            assert result["valid"] is True
            assert "OpenAI" in result["llm"]["available"]

        # Test with Gemini only
        env_vars = {
            "GITHUB_TOKEN": "ghp_test123",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo",
            "GEMINI_API_KEY": "AIzaTest123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_backlog_environment()
            assert result["valid"] is True
            assert "Gemini" in result["llm"]["available"]

    def test_validate_environment_for_command_backlog(self):
        """Test validation for backlog commands."""
        import os
        from unittest.mock import patch

        env_vars = {
            "GITHUB_TOKEN": "ghp_test123",
            "GITHUB_OWNER": "test-owner",
            "GITHUB_REPO": "test-repo",
            "ANTHROPIC_API_KEY": "sk-ant-test123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Should call validate_backlog_environment for these commands
            result = validate_environment_for_command("backlog")
            assert result["valid"] is True

            result = validate_environment_for_command("backlog run")
            assert result["valid"] is True

            result = validate_environment_for_command("backlog generate")
            assert result["valid"] is True

            result = validate_environment_for_command("backlog process")
            assert result["valid"] is True

    def test_validate_environment_for_other_commands(self):
        """Test that other commands don't require specific validation."""
        import os
        from unittest.mock import patch

        # Even with no env vars, other commands should pass
        with patch.dict(os.environ, {}, clear=True):
            result = validate_environment_for_command("init")
            assert result["valid"] is True

            result = validate_environment_for_command("status")
            assert result["valid"] is True

    def test_environment_validation_error_message(self):
        """Test that error message is descriptive."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_backlog_environment()

            # Error message should mention GitHub and LLM
            assert "GitHub" in exc_info.value.message or "GITHUB" in exc_info.value.message
            assert "LLM" in exc_info.value.message or "API_KEY" in str(exc_info.value.missing)

    def test_environment_validation_error_attributes(self):
        """Test EnvironmentValidationError has correct attributes."""
        error = EnvironmentValidationError(
            missing=["GITHUB_TOKEN", "ANTHROPIC_API_KEY"],
            message="Test error message"
        )

        assert error.missing == ["GITHUB_TOKEN", "ANTHROPIC_API_KEY"]
        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_environment_validation_error_default_message(self):
        """Test EnvironmentValidationError default message."""
        error = EnvironmentValidationError(missing=["VAR1", "VAR2"])

        assert "VAR1" in error.message
        assert "VAR2" in error.message
