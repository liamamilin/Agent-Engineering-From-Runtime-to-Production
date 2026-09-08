from __future__ import annotations

from typing import Any

from agent_course.core.task import TaskSpec
from agent_course.core.state import AgentState
from agent_course.core.observation import Observation
from agent_course.llm.base import Message
from agent_course.tools.registry import ToolRegistry


class ContextBuilder:
    """Builds context for model calls from task, state, and observation."""

    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        max_context_tokens: int | None = None,
    ) -> None:
        self._system_prompt = system_prompt
        self._max_context_tokens = max_context_tokens

    def build(
        self,
        task: TaskSpec,
        state: AgentState,
        observation: Observation | None = None,
        tools: ToolRegistry | None = None,
    ) -> list[Message]:
        """Build context messages for model call."""
        messages: list[Message] = []

        # System message
        messages.append(Message.system(self._system_prompt))

        # Task description
        task_msg = f"Task: {task.goal}"
        if task.success_criteria:
            task_msg += f"\nSuccess criteria: {', '.join(task.success_criteria)}"
        messages.append(Message.user(task_msg))

        # Previous observations (simplified - in production would be more selective)
        for obs in state.observations[-5:]:  # Last 5 observations
            if hasattr(obs, "kind") and hasattr(obs, "payload"):
                if obs.kind == "user":
                    messages.append(Message.user(str(obs.payload)))
                elif obs.kind == "tool":
                    tool_data = obs.payload
                    if isinstance(tool_data, dict):
                        messages.append(Message.tool(
                            tool_call_id=f"call_{tool_data.get('tool', 'unknown')}",
                            content=str(tool_data.get("result", "")),
                            name=tool_data.get("tool"),
                        ))

        # Current observation
        if observation:
            if observation.kind == "user":
                messages.append(Message.user(str(observation.payload)))
            elif observation.kind == "tool":
                tool_data = observation.payload
                if isinstance(tool_data, dict):
                    messages.append(Message.tool(
                        tool_call_id=f"call_{tool_data.get('tool', 'unknown')}",
                        content=str(tool_data.get("result", "")),
                        name=tool_data.get("tool"),
                    ))

        return messages
