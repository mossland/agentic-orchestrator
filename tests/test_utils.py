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
from agentic_orchestrator.utils.config import get_env, get_env_bool, get_env_int


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
