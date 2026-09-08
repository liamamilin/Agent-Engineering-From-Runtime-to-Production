from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from agent_course.core.task import TaskSpec
from agent_course.core.state import AgentState


class TerminationReason(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    MAX_STEPS = "max_steps"
    BUDGET_EXCEEDED = "budget_exceeded"
    FINAL_DECISION = "final_decision"
    HUMAN_STOP = "human_stop"


@dataclass
class TerminationPolicy:
    """The policy that decides when the run must stop."""

    max_steps: int | None = None
    max_cost_usd: float | None = None

    def should_stop(self, task: TaskSpec, state: AgentState) -> tuple[bool, TerminationReason | None]:
        """Check if the run should stop."""
        if state.status == "completed":
            return True, TerminationReason.SUCCESS
        if state.status == "failed":
            return True, TerminationReason.FAILED

        if self.max_steps is not None and state.step_count >= self.max_steps:
            return True, TerminationReason.MAX_STEPS

        if task.max_steps and state.step_count >= task.max_steps:
            return True, TerminationReason.MAX_STEPS

        return False, None
