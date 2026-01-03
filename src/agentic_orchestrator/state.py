"""
State management for the Agentic Orchestrator.

Handles loading, saving, and transitioning between pipeline stages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import yaml


class Stage(Enum):
    """Pipeline stages for the orchestrator."""

    IDEATION = "IDEATION"
    PLANNING_DRAFT = "PLANNING_DRAFT"
    PLANNING_REVIEW = "PLANNING_REVIEW"
    DEV = "DEV"
    QA = "QA"
    DONE = "DONE"
    PAUSED_QUOTA = "PAUSED_QUOTA"
    ERROR = "ERROR"

    @classmethod
    def from_string(cls, value: str) -> "Stage":
        """Create Stage from string value."""
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid stage: {value}. Valid stages: {[s.value for s in cls]}")

    def next_stage(self) -> Optional["Stage"]:
        """Get the next stage in the normal flow."""
        transitions = {
            Stage.IDEATION: Stage.PLANNING_DRAFT,
            Stage.PLANNING_DRAFT: Stage.PLANNING_REVIEW,
            Stage.PLANNING_REVIEW: Stage.DEV,
            Stage.DEV: Stage.QA,
            Stage.QA: Stage.DONE,
            Stage.DONE: None,
            Stage.PAUSED_QUOTA: None,
            Stage.ERROR: None,
        }
        return transitions.get(self)

    def can_iterate(self) -> bool:
        """Check if this stage supports iteration loops."""
        return self in (Stage.PLANNING_REVIEW, Stage.QA)


@dataclass
class Iteration:
    """Iteration counters for planning and development cycles."""

    planning: int = 0
    dev: int = 0


@dataclass
class Limits:
    """Maximum iteration limits."""

    planning_max: int = 3
    dev_max: int = 5


@dataclass
class Quality:
    """Quality metrics and thresholds."""

    review_score: Optional[float] = None
    tests_passed: Optional[bool] = None
    required_score: float = 7.0
    review_approvals: int = 0


@dataclass
class Timestamps:
    """Timestamp tracking for the state."""

    created: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    stage_started: Optional[datetime] = None


@dataclass
class ErrorInfo:
    """Error tracking information."""

    last_error: Optional[str] = None
    error_count: int = 0
    paused_reason: Optional[str] = None


@dataclass
class State:
    """
    Complete state of the orchestrator.

    This is persisted to .agent/state.yaml and drives the state machine.
    """

    stage: Stage = Stage.IDEATION
    project_id: Optional[str] = None
    iteration: Iteration = field(default_factory=Iteration)
    limits: Limits = field(default_factory=Limits)
    quality: Quality = field(default_factory=Quality)
    timestamps: Timestamps = field(default_factory=Timestamps)
    errors: ErrorInfo = field(default_factory=ErrorInfo)

    # Class-level path configuration
    _state_dir: Path = Path(".agent")
    _state_file: str = "state.yaml"

    @classmethod
    def get_state_path(cls) -> Path:
        """Get the path to the state file."""
        return cls._state_dir / cls._state_file

    @classmethod
    def load(cls, base_path: Optional[Path] = None) -> "State":
        """
        Load state from YAML file.

        Args:
            base_path: Base directory containing .agent folder.
                      Defaults to current directory.

        Returns:
            State instance loaded from file, or new state if file doesn't exist.
        """
        if base_path is None:
            base_path = Path.cwd()

        state_path = base_path / cls._state_dir / cls._state_file

        if not state_path.exists():
            # Return new state with creation timestamp
            state = cls()
            state.timestamps.created = datetime.now()
            return state

        with open(state_path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    def save(self, base_path: Optional[Path] = None) -> Path:
        """
        Save state to YAML file.

        Args:
            base_path: Base directory containing .agent folder.
                      Defaults to current directory.

        Returns:
            Path to the saved state file.
        """
        if base_path is None:
            base_path = Path.cwd()

        state_dir = base_path / self._state_dir
        state_dir.mkdir(parents=True, exist_ok=True)

        state_path = state_dir / self._state_file

        # Update timestamp
        self.timestamps.last_updated = datetime.now()

        with open(state_path, "w") as f:
            yaml.dump(self._to_dict(), f, default_flow_style=False, sort_keys=False)

        return state_path

    @classmethod
    def _from_dict(cls, data: dict) -> "State":
        """Create State from dictionary."""
        state = cls()

        # Stage
        if "stage" in data:
            state.stage = Stage.from_string(data["stage"])

        # Project ID
        state.project_id = data.get("project_id")

        # Iteration
        if "iteration" in data:
            iter_data = data["iteration"]
            state.iteration = Iteration(
                planning=iter_data.get("planning", 0),
                dev=iter_data.get("dev", 0),
            )

        # Limits
        if "limits" in data:
            limits_data = data["limits"]
            state.limits = Limits(
                planning_max=limits_data.get("planning_max", 3),
                dev_max=limits_data.get("dev_max", 5),
            )

        # Quality
        if "quality" in data:
            qual_data = data["quality"]
            state.quality = Quality(
                review_score=qual_data.get("review_score"),
                tests_passed=qual_data.get("tests_passed"),
                required_score=qual_data.get("required_score", 7.0),
                review_approvals=qual_data.get("review_approvals", 0),
            )

        # Timestamps
        if "timestamps" in data:
            ts_data = data["timestamps"]
            state.timestamps = Timestamps(
                created=cls._parse_datetime(ts_data.get("created")),
                last_updated=cls._parse_datetime(ts_data.get("last_updated")),
                stage_started=cls._parse_datetime(ts_data.get("stage_started")),
            )

        # Errors
        if "errors" in data:
            err_data = data["errors"]
            state.errors = ErrorInfo(
                last_error=err_data.get("last_error"),
                error_count=err_data.get("error_count", 0),
                paused_reason=err_data.get("paused_reason"),
            )

        return state

    def _to_dict(self) -> dict:
        """Convert State to dictionary for YAML serialization."""
        return {
            "stage": self.stage.value,
            "project_id": self.project_id,
            "iteration": {
                "planning": self.iteration.planning,
                "dev": self.iteration.dev,
            },
            "limits": {
                "planning_max": self.limits.planning_max,
                "dev_max": self.limits.dev_max,
            },
            "quality": {
                "review_score": self.quality.review_score,
                "tests_passed": self.quality.tests_passed,
                "required_score": self.quality.required_score,
                "review_approvals": self.quality.review_approvals,
            },
            "timestamps": {
                "created": self._format_datetime(self.timestamps.created),
                "last_updated": self._format_datetime(self.timestamps.last_updated),
                "stage_started": self._format_datetime(self.timestamps.stage_started),
            },
            "errors": {
                "last_error": self.errors.last_error,
                "error_count": self.errors.error_count,
                "paused_reason": self.errors.paused_reason,
            },
        }

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Format datetime to ISO string."""
        if dt is None:
            return None
        return dt.isoformat()

    def transition_to(self, new_stage: Stage) -> None:
        """
        Transition to a new stage.

        Args:
            new_stage: The stage to transition to.
        """
        self.stage = new_stage
        self.timestamps.stage_started = datetime.now()

    def advance(self) -> bool:
        """
        Advance to the next stage in the pipeline.

        Returns:
            True if advanced successfully, False if no next stage.
        """
        next_stage = self.stage.next_stage()
        if next_stage is None:
            return False
        self.transition_to(next_stage)
        return True

    def increment_planning(self) -> bool:
        """
        Increment planning iteration counter.

        Returns:
            True if within limits, False if exceeded.
        """
        self.iteration.planning += 1
        return self.iteration.planning <= self.limits.planning_max

    def increment_dev(self) -> bool:
        """
        Increment development iteration counter.

        Returns:
            True if within limits, False if exceeded.
        """
        self.iteration.dev += 1
        return self.iteration.dev <= self.limits.dev_max

    def reset_for_new_project(self, project_id: str) -> None:
        """Reset state for a new project."""
        self.project_id = project_id
        self.stage = Stage.IDEATION
        self.iteration = Iteration()
        self.quality = Quality()
        self.timestamps = Timestamps(created=datetime.now())
        self.errors = ErrorInfo()

    def pause_for_quota(self, reason: str) -> None:
        """Pause the orchestrator due to quota issues."""
        self.stage = Stage.PAUSED_QUOTA
        self.errors.paused_reason = reason
        self.timestamps.last_updated = datetime.now()

    def set_error(self, error: str) -> None:
        """Record an error."""
        self.errors.last_error = error
        self.errors.error_count += 1

    def clear_error(self) -> None:
        """Clear the current error state."""
        self.errors.last_error = None

    def is_paused(self) -> bool:
        """Check if the orchestrator is in a paused state."""
        return self.stage in (Stage.PAUSED_QUOTA, Stage.ERROR)

    def is_complete(self) -> bool:
        """Check if the current project is complete."""
        return self.stage == Stage.DONE

    def can_continue(self) -> bool:
        """Check if the orchestrator can continue processing."""
        return not self.is_paused() and not self.is_complete()

    def meets_quality_threshold(self) -> bool:
        """Check if quality metrics meet the required thresholds."""
        if self.quality.review_score is None:
            return False
        return self.quality.review_score >= self.quality.required_score

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"State(stage={self.stage.value}, project={self.project_id}, "
            f"planning_iter={self.iteration.planning}, dev_iter={self.iteration.dev})"
        )
