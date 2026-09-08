from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StepRecord:
    """Record of a single step in an agent run."""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_number: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    observation: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    decision: dict[str, Any] = field(default_factory=dict)
    action_result: dict[str, Any] = field(default_factory=dict)
    state_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Complete trace of an agent run."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task: dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    steps: list[StepRecord] = field(default_factory=list)
    final_output: Any = None
    termination_reason: str | None = None
    total_steps: int = 0

    def add_step(self, step: StepRecord) -> None:
        self.steps.append(step)
        self.total_steps = len(self.steps)

    def finish(self, output: Any = None, reason: str | None = None) -> None:
        self.end_time = datetime.now()
        self.final_output = output
        self.termination_reason = reason


@dataclass
class RunSummary:
    """Summary of an agent run for evaluation."""

    run_id: str
    task_goal: str
    total_steps: int
    termination_reason: str | None
    success: bool
    duration_seconds: float | None = None
    tool_calls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_trace(cls, trace: Trace) -> RunSummary:
        duration = None
        if trace.end_time and trace.start_time:
            duration = (trace.end_time - trace.start_time).total_seconds()

        tool_calls = [
            s.decision.get("name", "")
            for s in trace.steps
            if s.decision.get("kind") == "tool"
        ]

        errors = [
            s.state_snapshot.get("error", "")
            for s in trace.steps
            if s.state_snapshot.get("error")
        ]

        return cls(
            run_id=trace.run_id,
            task_goal=trace.task.get("goal", ""),
            total_steps=trace.total_steps,
            termination_reason=trace.termination_reason,
            success=trace.termination_reason == "success",
            duration_seconds=duration,
            tool_calls=tool_calls,
            errors=errors,
        )
