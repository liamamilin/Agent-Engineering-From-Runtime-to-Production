from __future__ import annotations

from typing import Any

from agent_course.core.decision import Decision
from agent_course.core.observation import Observation
from agent_course.core.state import AgentState
from agent_course.core.task import TaskSpec
from agent_course.llm.base import ModelAdapter, Message
from agent_course.runtime.context_builder import ContextBuilder
from agent_course.tools.registry import ToolRegistry


class ModelPolicy:
    """Policy that uses a model to make decisions."""

    def __init__(
        self,
        model: ModelAdapter,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self._model = model
        self._context_builder = context_builder or ContextBuilder()

    def decide(
        self,
        task: TaskSpec,
        state: AgentState,
        observation: Observation | None = None,
        tools: ToolRegistry | None = None,
    ) -> Decision:
        """Make a decision based on current state."""
        # Build context
        messages = self._context_builder.build(task, state, observation, tools)

        # Get tool schemas if available
        tool_schemas = None
        if tools:
            tool_schemas = tools.to_openai_tools()

        # Call model
        response = self._model.complete(messages, tools=tool_schemas)

        # Parse response into decision
        return self._parse_response(response)

    def _parse_response(self, response: Any) -> Decision:
        """Parse model response into a decision."""
        # Check for tool calls
        if response.has_tool_calls:
            tool_call = response.tool_calls[0]
            return Decision.call_tool(
                name=tool_call.get("name", "unknown"),
                arguments=tool_call.get("arguments", {}),
            )

        # Check for final answer patterns
        content = response.content
        if content:
            # Simple heuristic: if content looks like a final answer
            if any(marker in content.lower() for marker in ["answer:", "final:", "result:"]):
                return Decision.final_answer(content)

            # Otherwise, treat as final answer by default
            return Decision.final_answer(content)

        # Default to fail if no content
        return Decision.fail("No response from model")
