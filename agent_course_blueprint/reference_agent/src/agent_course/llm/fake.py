from __future__ import annotations

import re
from typing import Any

from agent_course.llm.base import ModelAdapter, ModelResponse, Message


class FakeModel(ModelAdapter):
    """Deterministic fake model for offline tests.

    Supports pattern-based response selection and tool call simulation.
    """

    def __init__(
        self,
        responses: list[ModelResponse] | None = None,
        default_response: str = "I don't know.",
        tool_responses: dict[str, ModelResponse] | None = None,
    ) -> None:
        """Initialize fake model.

        Args:
            responses: Predefined responses in sequence
            default_response: Default response when no pattern matches
            tool_responses: Map of tool name patterns to responses
        """
        self._responses = list(responses) if responses else []
        self._default_response = default_response
        self._tool_responses = tool_responses or {}
        self._call_count = 0
        self._call_history: list[dict[str, Any]] = []

    def _call(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> ModelResponse:
        self._call_history.append({
            "messages": [m.to_dict() for m in messages],
            "tools": tools,
        })

        # Check for sequential responses first
        if self._call_count < len(self._responses):
            response = self._responses[self._call_count]
        else:
            # Check for tool-based patterns
            last_message = messages[-1].content if messages else ""
            response = self._match_pattern(last_message, tools)

        self._call_count += 1
        return response

    def _match_pattern(
        self,
        content: str,
        tools: list[dict[str, Any]] | None,
    ) -> ModelResponse:
        """Match content against tool response patterns."""
        for pattern, response in self._tool_responses.items():
            if re.search(pattern, content, re.IGNORECASE):
                return response

        # If tools are available and no pattern matched, return a tool call
        if tools and "search" in str(tools).lower():
            return ModelResponse(
                content="",
                tool_calls=[{
                    "id": "call_1",
                    "name": "search",
                    "arguments": {"query": content[:50]},
                }],
            )

        return ModelResponse(content=self._default_response)

    def reset(self) -> None:
        """Reset call count and history."""
        self._call_count = 0
        self._call_history = []

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def call_history(self) -> list[dict[str, Any]]:
        return self._call_history.copy()
