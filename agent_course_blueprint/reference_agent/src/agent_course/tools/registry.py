from __future__ import annotations

from typing import Any

from agent_course.tools.schema import ToolSchema


class ToolNotFoundError(Exception):
    """Raised when a tool is not found in the registry."""

    pass


class ToolRegistry:
    """Registry for available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSchema] = {}
        self._handlers: dict[str, Any] = {}

    def register(self, schema: ToolSchema, handler: Any) -> None:
        """Register a tool with its schema and handler."""
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

    def get(self, name: str) -> ToolSchema:
        """Get a tool schema by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def get_handler(self, name: str) -> Any:
        """Get a tool handler by name."""
        if name not in self._handlers:
            raise ToolNotFoundError(f"Tool handler not found: {name}")
        return self._handlers[name]

    def list_tools(self) -> list[ToolSchema]:
        """List all registered tools."""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert all tools to OpenAI format."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
