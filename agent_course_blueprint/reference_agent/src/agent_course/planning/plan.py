"""Plan representation for explicit planning architectures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanStatus(str, Enum):
    """Status of a plan or plan step."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in a plan."""
    
    id: str
    description: str
    action: str  # Tool name or action type
    arguments: dict[str, Any] = field(default_factory=dict)
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    error: str | None = None
    requires_approval: bool = False
    dependencies: list[str] = field(default_factory=list)  # Step IDs this depends on
    
    def mark_in_progress(self) -> None:
        """Mark step as in progress."""
        self.status = PlanStatus.IN_PROGRESS
    
    def mark_completed(self, result: Any = None) -> None:
        """Mark step as completed."""
        self.status = PlanStatus.COMPLETED
        self.result = result
    
    def mark_failed(self, error: str) -> None:
        """Mark step as failed."""
        self.status = PlanStatus.FAILED
        self.error = error
    
    def mark_skipped(self) -> None:
        """Mark step as skipped."""
        self.status = PlanStatus.SKIPPED
    
    def is_ready(self, completed_steps: set[str]) -> bool:
        """Check if step is ready to execute (all dependencies completed)."""
        if self.status != PlanStatus.PENDING:
            return False
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class Plan:
    """A plan consisting of ordered steps."""
    
    id: str
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    created_at: str = field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> PlanStep | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_next_step(self, completed_steps: set[str]) -> PlanStep | None:
        """Get the next step that is ready to execute."""
        for step in self.steps:
            if step.is_ready(completed_steps):
                return step
        return None
    
    def get_completed_steps(self) -> set[str]:
        """Get IDs of all completed steps."""
        return {
            step.id for step in self.steps
            if step.status == PlanStatus.COMPLETED
        }
    
    def get_pending_steps(self) -> list[PlanStep]:
        """Get all pending steps."""
        return [step for step in self.steps if step.status == PlanStatus.PENDING]
    
    def is_completed(self) -> bool:
        """Check if all steps are completed or skipped."""
        return all(
            step.status in (PlanStatus.COMPLETED, PlanStatus.SKIPPED)
            for step in self.steps
        )
    
    def is_failed(self) -> bool:
        """Check if any step has failed."""
        return any(step.status == PlanStatus.FAILED for step in self.steps)
    
    def update_status(self) -> None:
        """Update overall plan status based on step statuses."""
        if self.is_completed():
            self.status = PlanStatus.COMPLETED
        elif self.is_failed():
            self.status = PlanStatus.FAILED
        elif any(step.status == PlanStatus.IN_PROGRESS for step in self.steps):
            self.status = PlanStatus.IN_PROGRESS
        else:
            self.status = PlanStatus.PENDING
    
    def progress(self) -> float:
        """Calculate progress as fraction of completed steps."""
        if not self.steps:
            return 0.0
        completed = len([s for s in self.steps if s.status == PlanStatus.COMPLETED])
        return completed / len(self.steps)
