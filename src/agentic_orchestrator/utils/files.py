"""
File utilities for the Agentic Orchestrator.

Provides helpers for file operations, especially Markdown file handling.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .logging import get_logger

logger = get_logger(__name__)


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        The path (for chaining).
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: Path) -> Path:
    """
    Ensure the parent directory of a file exists.

    Args:
        path: File path.

    Returns:
        The path (for chaining).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_markdown(
    path: Path,
    content: str,
    title: Optional[str] = None,
    metadata: Optional[dict] = None,
    append: bool = False,
) -> Path:
    """
    Write a Markdown file with optional YAML frontmatter.

    Args:
        path: File path.
        content: Markdown content.
        title: Optional title for the document.
        metadata: Optional YAML frontmatter metadata.
        append: Append to existing file instead of overwriting.

    Returns:
        The file path.
    """
    path = Path(path)
    ensure_parent(path)

    # Build frontmatter
    frontmatter = ""
    if metadata or title:
        frontmatter = "---\n"
        if title:
            frontmatter += f"title: {title}\n"
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    value = value.isoformat()
                frontmatter += f"{key}: {value}\n"
        frontmatter += "---\n\n"

    # Build full content
    full_content = frontmatter + content

    # Write file
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        if append and f.tell() > 0:
            f.write("\n\n")
        f.write(full_content)

    logger.debug(f"Wrote Markdown file: {path}")
    return path


def read_markdown(path: Path) -> tuple[str, dict]:
    """
    Read a Markdown file and parse YAML frontmatter.

    Args:
        path: File path.

    Returns:
        Tuple of (content, metadata).
    """
    path = Path(path)

    if not path.exists():
        return "", {}

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Parse frontmatter
    metadata = {}
    content = text

    frontmatter_match = re.match(r"^---\n(.*?)\n---\n\n?(.*)", text, re.DOTALL)
    if frontmatter_match:
        import yaml

        frontmatter_text = frontmatter_match.group(1)
        content = frontmatter_match.group(2)

        try:
            metadata = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            logger.warning(f"Failed to parse frontmatter in {path}")

    return content, metadata


def generate_project_id() -> str:
    """
    Generate a unique project ID.

    Returns:
        Project ID in format: YYYYMMDD-HHMMSS-XXX
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_suffix = os.urandom(2).hex()[:3].upper()
    return f"{timestamp}-{random_suffix}"


def get_project_dir(project_id: str, base_path: Optional[Path] = None) -> Path:
    """
    Get the directory for a project.

    Args:
        project_id: Project identifier.
        base_path: Base path. Defaults to current directory.

    Returns:
        Path to project directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    return base_path / "projects" / project_id


def get_stage_dir(project_id: str, stage: str, base_path: Optional[Path] = None) -> Path:
    """
    Get the directory for a specific stage output.

    Args:
        project_id: Project identifier.
        stage: Stage name (e.g., "ideation", "planning").
        base_path: Base path. Defaults to current directory.

    Returns:
        Path to stage directory.
    """
    project_dir = get_project_dir(project_id, base_path)

    # Map stage names to directory names
    stage_dirs = {
        "IDEATION": "01_ideation",
        "PLANNING_DRAFT": "02_planning",
        "PLANNING_REVIEW": "02_planning",
        "DEV": "03_implementation",
        "QA": "04_quality",
        "DONE": "04_quality",
    }

    dir_name = stage_dirs.get(stage.upper(), stage.lower())
    stage_dir = project_dir / dir_name
    ensure_dir(stage_dir)

    return stage_dir


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: Original name.

    Returns:
        Sanitized filename.
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
    sanitized = re.sub(r"\s+", "_", sanitized)
    sanitized = sanitized.strip("._")

    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    return sanitized or "unnamed"


def create_alert_file(
    alert_type: str,
    provider: str,
    model: str,
    stage: str,
    error: str,
    resolution: str,
    base_path: Optional[Path] = None,
    project_id: Optional[str] = None,
) -> Path:
    """
    Create an alert file for quota/error issues.

    Args:
        alert_type: Type of alert (e.g., "quota", "error").
        provider: Provider name (e.g., "openai", "gemini").
        model: Model name.
        stage: Current stage.
        error: Error message.
        resolution: Suggested resolution steps.
        base_path: Base path. Defaults to current directory.
        project_id: Optional project ID for project-specific alerts.

    Returns:
        Path to the alert file.
    """
    if base_path is None:
        base_path = Path.cwd()

    # Determine alert location
    if project_id:
        alert_dir = get_stage_dir(project_id, "QA", base_path)
        filename = f"{alert_type}_alert.md"
    else:
        alert_dir = base_path / "alerts"
        filename = f"{alert_type}.md"

    ensure_dir(alert_dir)
    alert_path = alert_dir / filename

    # Build alert content
    content = f"""# {alert_type.upper()} Alert

## Summary

An issue occurred that requires attention before the orchestrator can continue.

## Details

| Field | Value |
|-------|-------|
| Provider | {provider} |
| Model | {model} |
| Stage | {stage} |
| Timestamp | {datetime.now().isoformat()} |

## Error

```
{error}
```

## Required Actions

{resolution}

## Recovery

After resolving the issue:

1. Review the error and ensure it's resolved
2. If needed, update `.env` with correct API keys
3. Restart the orchestrator: `ao step`

---

*This alert was automatically generated by the Agentic Orchestrator.*
"""

    write_markdown(alert_path, content)
    logger.warning(f"Created alert file: {alert_path}")

    return alert_path
