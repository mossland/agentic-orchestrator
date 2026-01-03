"""
Backlog-based workflow handlers.

Implements the new workflow where:
- Ideas are generated and stored as GitHub Issues
- Humans promote ideas to plans via labels
- Humans promote plans to development via labels
- Orchestrator polls for promotions and processes them
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from .github_client import GitHubClient, GitHubIssue, Labels, GitHubRateLimitError
from .providers.claude import create_claude_provider, ClaudeProvider
from .providers.openai import create_openai_provider
from .providers.gemini import create_gemini_provider
from .providers.base import QuotaExhaustedError
from .utils.logging import get_logger
from .utils.config import load_config, get_env_int, get_env_bool
from .utils.files import (
    ensure_dir,
    write_markdown,
    get_project_dir,
    generate_project_id,
    create_alert_file,
)
from .utils.git import GitHelper

logger = get_logger(__name__)


class IdeaGenerator:
    """
    Generates new idea issues for the backlog.

    Creates GitHub Issues with structured idea content
    following Mossland ecosystem focus.
    """

    def __init__(
        self,
        github: GitHubClient,
        claude: Optional[ClaudeProvider] = None,
        dry_run: bool = False,
    ):
        self.github = github
        self._claude = claude
        self.dry_run = dry_run

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def generate_ideas(self, count: int = 1) -> List[GitHubIssue]:
        """
        Generate new idea issues.

        Args:
            count: Number of ideas to generate.

        Returns:
            List of created GitHubIssue objects.
        """
        created = []

        for i in range(count):
            try:
                logger.info(f"Generating idea {i + 1}/{count}")

                # Generate idea content
                idea = self._generate_idea_content()

                if self.dry_run:
                    logger.info(f"[DRY RUN] Would create idea: {idea['title']}")
                    continue

                # Create GitHub Issue
                issue = self.github.create_issue(
                    title=f"[IDEA] {idea['title']}",
                    body=idea["body"],
                    labels=[
                        Labels.TYPE_IDEA,
                        Labels.STATUS_BACKLOG,
                        Labels.GENERATED_BY_ORCHESTRATOR,
                    ],
                )

                created.append(issue)
                logger.info(f"Created idea issue #{issue.number}: {idea['title']}")

            except Exception as e:
                logger.error(f"Failed to generate idea {i + 1}: {e}")
                continue

        return created

    def _generate_idea_content(self) -> dict:
        """Generate structured idea content using Claude."""
        prompt = self._get_idea_prompt()

        response = self.claude.chat(
            user_message=prompt,
            system_message=self._get_system_message(),
        )

        # Parse response
        return self._parse_idea_response(response)

    def _get_system_message(self) -> str:
        return """You are a creative Web3 product strategist for the Mossland ecosystem.

Mossland is a blockchain-based metaverse project with:
- MOC Token (Mossland Coin) - the native cryptocurrency
- Real-world location integration with virtual spaces
- NFT-based digital assets
- AR/VR experiences

Generate SMALL, FOCUSED micro-service ideas that:
1. Can be built as an MVP in 1-2 weeks
2. Provide clear value to MOC holders or the ecosystem
3. Are technically feasible with Web3 technologies
4. Have measurable success criteria

Avoid:
- Large platform/mainnet development
- Overly complex infrastructure
- Ideas requiring massive user adoption to work

Good examples:
- Token utility tools
- Community engagement helpers
- Governance participation tools
- Content verification systems
- Badge/achievement systems
- Simple bridges or integrations
- Analytics dashboards
- Reward distribution tools"""

    def _get_idea_prompt(self) -> str:
        return """Generate ONE innovative micro Web3 service idea for the Mossland ecosystem.

Provide a structured response with these exact sections:

## Title
A short, descriptive name (3-6 words)

## Problem
What specific problem does this solve? (2-3 sentences)

## Target User
Who will use this? What's their main need? (2-3 sentences)

## Why Mossland
How does this benefit the Mossland ecosystem and MOC token? (2-3 sentences)

## MVP Scope
What's the minimum viable product? List 3-5 core features:
- Feature 1
- Feature 2
- Feature 3

## Technical Approach
Brief technical overview (2-3 sentences mentioning key technologies)

## Risks
Top 2-3 risks and challenges:
- Risk 1
- Risk 2

## Success Metrics
How do we measure success? List 2-3 metrics:
- Metric 1
- Metric 2

Be specific and practical. Focus on something that can actually be built quickly."""

    def _parse_idea_response(self, response: str) -> dict:
        """Parse Claude's response into structured idea."""
        # Extract title
        title_match = re.search(r"##\s*Title\s*\n+(.+?)(?=\n\n|\n##)", response, re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled Idea"

        # Clean title
        title = title.replace("#", "").strip()
        if len(title) > 80:
            title = title[:77] + "..."

        # Build body with all sections
        body = f"""## Overview

{self._extract_section(response, "Problem", "Target User")}

## Target User

{self._extract_section(response, "Target User", "Why Mossland")}

## Why Mossland

{self._extract_section(response, "Why Mossland", "MVP Scope")}

## MVP Scope

{self._extract_section(response, "MVP Scope", "Technical Approach")}

## Technical Approach

{self._extract_section(response, "Technical Approach", "Risks")}

## Risks

{self._extract_section(response, "Risks", "Success Metrics")}

## Success Metrics

{self._extract_section(response, "Success Metrics", None)}

---

*Generated by Agentic Orchestrator on {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC*

**To promote this idea to planning:** Add the `promote:to-plan` label.
"""

        return {"title": title, "body": body}

    def _extract_section(
        self,
        text: str,
        section: str,
        next_section: Optional[str],
    ) -> str:
        """Extract content between two section headers."""
        if next_section:
            pattern = rf"##\s*{section}\s*\n+(.*?)(?=##\s*{next_section})"
        else:
            pattern = rf"##\s*{section}\s*\n+(.*?)$"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "(Not provided)"


class PlanGenerator:
    """
    Generates planning documents from promoted ideas.

    Creates detailed PRD, Architecture, Tasks, and Acceptance Criteria
    and stores them in a new GitHub Issue.
    """

    def __init__(
        self,
        github: GitHubClient,
        claude: Optional[ClaudeProvider] = None,
        dry_run: bool = False,
    ):
        self.github = github
        self._claude = claude
        self.dry_run = dry_run

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def generate_plan_from_idea(self, idea_issue: GitHubIssue) -> Optional[GitHubIssue]:
        """
        Generate a plan issue from an idea issue.

        Args:
            idea_issue: The idea issue to plan.

        Returns:
            Created plan issue, or None if failed/skipped.
        """
        logger.info(f"Generating plan for idea #{idea_issue.number}: {idea_issue.title}")

        # Idempotency check: skip if already processed
        if idea_issue.has_label(Labels.PROCESSED_TO_PLAN):
            logger.info(f"Idea #{idea_issue.number} already has processed label, skipping")
            return None

        if idea_issue.has_label(Labels.STATUS_PLANNED):
            logger.info(f"Idea #{idea_issue.number} already planned, skipping")
            return None

        # Check for existing plan that references this idea
        existing_plans = self._find_existing_plan_for_idea(idea_issue.number)
        if existing_plans:
            logger.info(
                f"Plan already exists for idea #{idea_issue.number}: "
                f"#{existing_plans[0].number}, skipping"
            )
            return None

        # Track created artifacts for rollback
        created_plan: Optional[GitHubIssue] = None

        try:
            # Generate plan content
            plan_content = self._generate_plan_content(idea_issue)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would create plan for idea #{idea_issue.number}")
                return None

            # Step 1: Create plan issue
            plan_title = idea_issue.title.replace("[IDEA]", "[PLAN]")
            created_plan = self.github.create_issue(
                title=plan_title,
                body=plan_content,
                labels=[
                    Labels.TYPE_PLAN,
                    Labels.STATUS_BACKLOG,
                    Labels.GENERATED_BY_ORCHESTRATOR,
                ],
            )
            logger.debug(f"Created plan issue #{created_plan.number}")

            # Step 2: Update idea issue status
            self.github.mark_idea_as_planned(idea_issue.number)
            logger.debug(f"Marked idea #{idea_issue.number} as planned")

            # Step 3: Add cross-reference comments (non-critical, don't rollback for these)
            try:
                self.github.add_comment(
                    idea_issue.number,
                    f"Planning document created: #{created_plan.number}\n\n"
                    f"This idea has been promoted to the planning phase.",
                )

                self.github.add_comment(
                    created_plan.number,
                    f"This plan was generated from idea #{idea_issue.number}.\n\n"
                    f"**To promote this plan to development:** Add the `promote:to-dev` label.",
                )
            except Exception as comment_err:
                # Comments are non-critical, just log warning
                logger.warning(f"Failed to add cross-reference comments: {comment_err}")

            logger.info(f"Created plan issue #{created_plan.number}")
            return created_plan

        except Exception as e:
            logger.error(f"Failed to generate plan for #{idea_issue.number}: {e}")

            # Rollback: Close the created plan issue if it exists
            if created_plan is not None:
                try:
                    logger.warning(
                        f"Rolling back: closing plan issue #{created_plan.number} "
                        f"due to error: {e}"
                    )
                    self.github.update_issue(
                        created_plan.number,
                        state="closed",
                        labels=[Labels.TYPE_PLAN, "rollback:failed"],
                    )
                    self.github.add_comment(
                        created_plan.number,
                        f"This plan was automatically closed due to an error during creation.\n\n"
                        f"Error: {e}\n\n"
                        f"The original idea #{idea_issue.number} may need to be re-promoted.",
                    )
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback plan issue: {rollback_err}")

            # Add error comment to idea (only if plan wasn't created or rollback succeeded)
            if not self.dry_run:
                try:
                    self.github.add_comment(
                        idea_issue.number,
                        f"Failed to generate plan: {e}\n\n"
                        f"Please try again or create plan manually.",
                    )
                except Exception:
                    pass  # Best effort

            raise

    def _generate_plan_content(self, idea_issue: GitHubIssue) -> str:
        """Generate detailed planning content."""
        prompt = f"""Based on the following idea, create a detailed planning document.

# Idea: {idea_issue.title}

{idea_issue.body}

---

Create a comprehensive planning document with these sections:

## 1. Product Requirements Document (PRD)

### 1.1 Executive Summary
Brief overview (2-3 sentences)

### 1.2 Problem Statement
Detailed problem description

### 1.3 Goals and Success Metrics
- Primary goal
- Key metrics

### 1.4 User Stories
Write 3-5 user stories in format: "As a [user], I want [action] so that [benefit]"

### 1.5 Functional Requirements
List core features with priorities (Must Have / Should Have / Nice to Have)

### 1.6 Non-Functional Requirements
Performance, security, scalability considerations

## 2. Architecture

### 2.1 System Overview
High-level architecture description

### 2.2 Technology Stack
| Layer | Technology | Justification |
|-------|------------|---------------|

### 2.3 Component Design
Key components and their responsibilities

### 2.4 Data Model
Core entities and relationships

### 2.5 API Design
Key endpoints (if applicable)

## 3. Task Breakdown

### Phase 1: Setup
- [ ] Task 1 (Effort: S/M/L)
- [ ] Task 2

### Phase 2: Core Development
- [ ] Task 3
- [ ] Task 4

### Phase 3: Integration & Testing
- [ ] Task 5
- [ ] Task 6

## 4. Acceptance Criteria

### Feature 1
- [ ] Criterion 1
- [ ] Criterion 2

### Feature 2
- [ ] Criterion 1

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|

## 6. Timeline Estimate

- Phase 1: X days
- Phase 2: X days
- Phase 3: X days
- **Total: X days**

Be specific and practical. Focus on MVP scope that can be built in 1-2 weeks."""

        response = self.claude.chat(
            user_message=prompt,
            system_message="You are an expert product manager and software architect. Create detailed, actionable planning documents.",
        )

        # Add metadata
        body = f"""# Planning Document

**Source Idea:** #{idea_issue.number}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC

---

{response}

---

**To promote this plan to development:** Add the `promote:to-dev` label.
"""

        return body

    def _find_existing_plan_for_idea(self, idea_number: int) -> List[GitHubIssue]:
        """
        Find existing plan issues that reference a specific idea.

        Args:
            idea_number: The idea issue number to search for.

        Returns:
            List of plan issues that reference this idea.
        """
        try:
            # Search for plan issues that mention this idea number
            plans = self.github.search_issues(
                labels=[Labels.TYPE_PLAN],
                state="all",  # Include closed plans too
            )

            # Filter plans that reference this idea in their body
            matching_plans = []
            source_patterns = [
                f"Source Idea: #{idea_number}",
                f"Source Idea:** #{idea_number}",
                f"idea #{idea_number}",
            ]
            for plan in plans:
                if any(pattern in plan.body for pattern in source_patterns):
                    matching_plans.append(plan)

            return matching_plans
        except Exception as e:
            logger.warning(f"Failed to search for existing plans: {e}")
            return []


class DevScaffolder:
    """
    Sets up development environment from promoted plans.

    Creates project structure, initial files, and prepares
    for development work.
    """

    def __init__(
        self,
        github: GitHubClient,
        base_path: Optional[Path] = None,
        dry_run: bool = False,
    ):
        self.github = github
        self.base_path = base_path or Path.cwd()
        self.dry_run = dry_run
        self._git: Optional[GitHelper] = None

    @property
    def git(self) -> GitHelper:
        if self._git is None:
            self._git = GitHelper(self.base_path)
        return self._git

    def scaffold_from_plan(self, plan_issue: GitHubIssue) -> Optional[str]:
        """
        Create development scaffold from a plan issue.

        Args:
            plan_issue: The plan issue to scaffold.

        Returns:
            Project ID if successful, None if failed/skipped.
        """
        logger.info(f"Scaffolding development for plan #{plan_issue.number}")

        # Idempotency check: skip if already processed
        if plan_issue.has_label(Labels.PROCESSED_TO_DEV):
            logger.info(f"Plan #{plan_issue.number} already has processed label, skipping")
            return None

        if plan_issue.has_label(Labels.STATUS_IN_DEV):
            logger.info(f"Plan #{plan_issue.number} already in development, skipping")
            return None

        # Check for existing project directory for this plan
        existing_project = self._find_existing_project_for_plan(plan_issue.number)
        if existing_project:
            logger.info(
                f"Project already exists for plan #{plan_issue.number}: "
                f"{existing_project}, skipping"
            )
            return None

        try:
            # Generate project ID
            project_id = generate_project_id()

            if self.dry_run:
                logger.info(f"[DRY RUN] Would scaffold project {project_id}")
                return project_id

            # Create project structure
            project_dir = get_project_dir(project_id, self.base_path)
            self._create_project_structure(project_dir, plan_issue, project_id)

            # Commit changes
            self.git.add(all=True)
            self.git.commit(
                f"[dev] Scaffold project {project_id} from plan #{plan_issue.number}",
                stage="DEV",
                project_id=project_id,
            )

            # Update plan issue
            self.github.mark_plan_as_in_dev(plan_issue.number)

            # Add comment with project info
            self.github.add_comment(
                plan_issue.number,
                f"Development started!\n\n"
                f"- **Project ID:** `{project_id}`\n"
                f"- **Directory:** `projects/{project_id}/`\n\n"
                f"Initial scaffold has been committed to the repository.",
            )

            logger.info(f"Created project scaffold: {project_id}")
            return project_id

        except Exception as e:
            logger.error(f"Failed to scaffold from plan #{plan_issue.number}: {e}")
            if not self.dry_run:
                self.github.add_comment(
                    plan_issue.number,
                    f"Failed to start development: {e}\n\nPlease check the logs and try again.",
                )
            raise

    def _create_project_structure(
        self,
        project_dir: Path,
        plan_issue: GitHubIssue,
        project_id: str,
    ) -> None:
        """Create the project directory structure."""
        # Create directories
        dirs = [
            project_dir / "01_ideation",
            project_dir / "02_planning",
            project_dir / "03_implementation" / "src",
            project_dir / "03_implementation" / "tests",
            project_dir / "04_quality",
        ]
        for d in dirs:
            ensure_dir(d)

        # Extract idea number from plan body
        idea_ref = re.search(r"Source Idea.*?#(\d+)", plan_issue.body)
        idea_number = idea_ref.group(1) if idea_ref else "unknown"

        # Save plan document
        write_markdown(
            project_dir / "02_planning" / "PLAN.md",
            plan_issue.body,
            title=plan_issue.title,
            metadata={
                "source_issue": plan_issue.number,
                "source_idea": idea_number,
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
            },
        )

        # Create project README
        readme_content = f"""# Project: {project_id}

## Source

- **Plan Issue:** [#{plan_issue.number}]({plan_issue.html_url})
- **Idea Issue:** #{idea_number}

## Status

- [x] Idea generated
- [x] Planning complete
- [ ] Development in progress
- [ ] Quality assurance
- [ ] Complete

## Structure

```
{project_id}/
├── 01_ideation/       # Original idea documents
├── 02_planning/       # PRD, Architecture, Tasks
├── 03_implementation/ # Source code
│   ├── src/
│   └── tests/
└── 04_quality/        # QA reports, reviews
```

## Development

Development was initiated on {datetime.now().strftime("%Y-%m-%d")}.

See `02_planning/PLAN.md` for detailed requirements and tasks.
"""

        write_markdown(
            project_dir / "README.md",
            readme_content,
            title=f"Project {project_id}",
        )

        # Create implementation placeholder
        write_markdown(
            project_dir / "03_implementation" / "README.md",
            "# Implementation\n\nSource code will be added here during development.",
        )

    def _find_existing_project_for_plan(self, plan_number: int) -> Optional[str]:
        """
        Find existing project directory that references a specific plan.

        Args:
            plan_number: The plan issue number to search for.

        Returns:
            Project ID if found, None otherwise.
        """
        try:
            projects_dir = self.base_path / "projects"
            if not projects_dir.exists():
                return None

            # Search through project directories
            for project_path in projects_dir.iterdir():
                if not project_path.is_dir():
                    continue

                # Check PLAN.md or README.md for plan reference
                plan_md = project_path / "02_planning" / "PLAN.md"
                readme_md = project_path / "README.md"

                for check_file in [plan_md, readme_md]:
                    if check_file.exists():
                        content = check_file.read_text()
                        if f"#{plan_number}" in content or f"source_issue: {plan_number}" in content:
                            return project_path.name

            return None
        except Exception as e:
            logger.warning(f"Failed to search for existing projects: {e}")
            return None


class BacklogOrchestrator:
    """
    Main orchestrator for the backlog-based workflow.

    Handles:
    - Periodic idea generation
    - Polling for promotion labels
    - Processing promoted items
    - Concurrency control
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        dry_run: bool = False,
    ):
        self.base_path = base_path or Path.cwd()
        self.dry_run = dry_run or get_env_bool("DRY_RUN")
        self.config = load_config()

        self._github: Optional[GitHubClient] = None
        self._idea_generator: Optional[IdeaGenerator] = None
        self._plan_generator: Optional[PlanGenerator] = None
        self._dev_scaffolder: Optional[DevScaffolder] = None

        # Concurrency control
        self._lock_file = self.base_path / ".agent" / "orchestrator.lock"

    @property
    def github(self) -> GitHubClient:
        if self._github is None:
            self._github = GitHubClient()
        return self._github

    @property
    def idea_generator(self) -> IdeaGenerator:
        if self._idea_generator is None:
            self._idea_generator = IdeaGenerator(
                github=self.github,
                dry_run=self.dry_run,
            )
        return self._idea_generator

    @property
    def plan_generator(self) -> PlanGenerator:
        if self._plan_generator is None:
            self._plan_generator = PlanGenerator(
                github=self.github,
                dry_run=self.dry_run,
            )
        return self._plan_generator

    @property
    def dev_scaffolder(self) -> DevScaffolder:
        if self._dev_scaffolder is None:
            self._dev_scaffolder = DevScaffolder(
                github=self.github,
                base_path=self.base_path,
                dry_run=self.dry_run,
            )
        return self._dev_scaffolder

    def acquire_lock(self) -> bool:
        """
        Acquire execution lock to prevent concurrent runs.

        Includes stale lock detection:
        - Checks if lock holder process is still alive
        - Checks if lock has exceeded timeout
        """
        import fcntl
        import os
        import signal

        ensure_dir(self._lock_file.parent)

        # Check for stale lock before attempting to acquire
        self._cleanup_stale_lock()

        try:
            self._lock_fd = open(self._lock_file, "w")
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_fd.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
            self._lock_fd.flush()
            return True
        except (IOError, OSError):
            logger.warning("Another orchestrator instance is running")
            return False

    def _cleanup_stale_lock(self) -> None:
        """Remove stale lock if process is dead or timeout exceeded."""
        import os
        import signal

        if not self._lock_file.exists():
            return

        try:
            content = self._lock_file.read_text().strip()
            lines = content.split('\n')
            if len(lines) < 2:
                # Malformed lock file, remove it
                logger.warning("Malformed lock file detected, removing")
                self._lock_file.unlink()
                return

            pid_str, timestamp_str = lines[0], lines[1]
            pid = int(pid_str)
            lock_time = datetime.fromisoformat(timestamp_str)

            # Get lock timeout from config (default 300 seconds)
            lock_timeout = self.config.get("orchestrator", "lock_timeout_seconds", default=300)

            # Check if lock has timed out
            elapsed = (datetime.now() - lock_time).total_seconds()
            if elapsed > lock_timeout:
                logger.warning(
                    f"Stale lock detected: lock held for {elapsed:.0f}s "
                    f"(timeout: {lock_timeout}s), removing"
                )
                self._lock_file.unlink()
                return

            # Check if process is still alive
            if not self._is_process_alive(pid):
                logger.warning(
                    f"Dead process lock detected: PID {pid} no longer exists, removing"
                )
                self._lock_file.unlink()
                return

        except (ValueError, OSError, IOError) as e:
            logger.warning(f"Error checking lock file: {e}, removing lock")
            try:
                self._lock_file.unlink()
            except OSError:
                pass

    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process with the given PID is still running."""
        import os
        import signal

        try:
            # Sending signal 0 checks if process exists without actually signaling
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            # Process does not exist
            return False
        except PermissionError:
            # Process exists but we don't have permission (still alive)
            return True

    def release_lock(self) -> None:
        """Release execution lock."""
        import fcntl

        if hasattr(self, "_lock_fd") and self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self._lock_file.unlink(missing_ok=True)
            except Exception:
                pass

    def run_cycle(
        self,
        generate_ideas: bool = True,
        idea_count: int = 1,
        max_promotions: int = 5,
    ) -> dict:
        """
        Run one orchestration cycle.

        Args:
            generate_ideas: Whether to generate new ideas.
            idea_count: Number of ideas to generate.
            max_promotions: Maximum promotions to process.

        Returns:
            Summary of actions taken.
        """
        if not self.acquire_lock():
            return {"error": "Could not acquire lock - another instance running"}

        try:
            results = {
                "ideas_generated": 0,
                "plans_generated": 0,
                "devs_started": 0,
                "errors": [],
            }

            # 1. Generate new ideas (if enabled)
            if generate_ideas:
                try:
                    ideas = self.idea_generator.generate_ideas(count=idea_count)
                    results["ideas_generated"] = len(ideas)
                except Exception as e:
                    logger.error(f"Idea generation failed: {e}")
                    results["errors"].append(f"Idea generation: {e}")

            # 2. Process idea promotions
            try:
                promoted_ideas = self.github.find_ideas_to_promote()
                for idea in promoted_ideas[:max_promotions]:
                    try:
                        plan = self.plan_generator.generate_plan_from_idea(idea)
                        if plan:
                            results["plans_generated"] += 1
                    except Exception as e:
                        logger.error(f"Plan generation failed for #{idea.number}: {e}")
                        results["errors"].append(f"Plan for #{idea.number}: {e}")
            except Exception as e:
                logger.error(f"Finding promoted ideas failed: {e}")
                results["errors"].append(f"Find promoted ideas: {e}")

            # 3. Process plan promotions
            try:
                promoted_plans = self.github.find_plans_to_promote()
                for plan in promoted_plans[:max_promotions]:
                    try:
                        project_id = self.dev_scaffolder.scaffold_from_plan(plan)
                        if project_id:
                            results["devs_started"] += 1
                    except Exception as e:
                        logger.error(f"Dev scaffold failed for #{plan.number}: {e}")
                        results["errors"].append(f"Dev for #{plan.number}: {e}")
            except Exception as e:
                logger.error(f"Finding promoted plans failed: {e}")
                results["errors"].append(f"Find promoted plans: {e}")

            return results

        except GitHubRateLimitError as e:
            logger.error(f"GitHub rate limit hit: {e}")
            return {"error": f"GitHub rate limit: retry after {e.reset_time}"}

        except QuotaExhaustedError as e:
            logger.error(f"API quota exhausted: {e}")
            create_alert_file(
                alert_type="quota",
                provider=e.provider,
                model=e.model,
                stage="backlog",
                error=str(e),
                resolution="Check API quota and billing. Restart with: ao backlog",
                base_path=self.base_path,
            )
            return {"error": f"Quota exhausted: {e}"}

        finally:
            self.release_lock()

    def setup_labels(self) -> None:
        """Ensure all required labels exist in the repository."""
        logger.info("Setting up labels...")
        self.github.ensure_labels_exist()
        logger.info("Labels setup complete")

    def get_status(self) -> dict:
        """Get current backlog status."""
        try:
            backlog_ideas = self.github.find_backlog_ideas()
            backlog_plans = self.github.find_backlog_plans()
            ideas_to_promote = self.github.find_ideas_to_promote()
            plans_to_promote = self.github.find_plans_to_promote()

            return {
                "backlog": {
                    "ideas": len(backlog_ideas),
                    "plans": len(backlog_plans),
                },
                "pending_promotion": {
                    "ideas_to_plan": len(ideas_to_promote),
                    "plans_to_dev": len(plans_to_promote),
                },
                "issues": {
                    "ideas": [
                        {"number": i.number, "title": i.title}
                        for i in backlog_ideas[:10]
                    ],
                    "plans": [
                        {"number": p.number, "title": p.title}
                        for p in backlog_plans[:10]
                    ],
                },
            }
        except Exception as e:
            return {"error": str(e)}
