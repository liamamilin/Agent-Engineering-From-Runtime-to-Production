from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.core.task import TaskSpec


@dataclass
class AgentState:
    """The explicit information carried from one step to the next."""

    task: TaskSpec
    step_count: int = 0
    status: str = "running"
    observations: list[Any] = field(default_factory=list)
    tool_results: list[Any] = field(default_factory=list)
    working: dict[str, Any] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    final_output: Any | None = None
    error: str | None = None

    def add_observation(self, observation: Any) -> None:
        self.observations.append(observation)

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        self.tool_results.append({"tool": tool_name, "result": result})

    def set_final_output(self, output: Any) -> None:
        self.final_output = output
        self.status = "completed"

    def set_error(self, error: str) -> None:
        self.error = error
        self.status = "failed"
