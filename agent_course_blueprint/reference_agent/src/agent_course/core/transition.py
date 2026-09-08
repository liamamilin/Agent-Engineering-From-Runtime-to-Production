from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_course.core.observation import Observation
from agent_course.core.decision import Decision
from agent_course.core.state import AgentState


@dataclass
class Transition:
    """The deterministic or controlled update from the current state to the next state."""

    @staticmethod
    def apply(
        state: AgentState,
        observation: Observation,
        decision: Decision,
        action_result: Any = None,
    ) -> AgentState:
        """Apply a transition: update state based on observation, decision, and action result."""
        state.step_count += 1
        state.add_observation(observation)

        if decision.kind == "tool" and action_result is not None:
            state.add_tool_result(decision.name, action_result)
        elif decision.kind == "final":
            state.set_final_output(decision.content)
        elif decision.kind == "fail":
            state.set_error(decision.reason or "Unknown failure")

        return state
