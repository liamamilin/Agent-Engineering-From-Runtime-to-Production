from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from agent_course.tools.schema import ToolSchema
from agent_course.tools.registry import ToolRegistry
from agent_course.tools.validator import ToolValidator, ValidationError


class PermissionDeniedError(Exception):
    """Raised when a tool requires permission that is not granted."""

    pass


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, output: Any, **metadata: Any) -> ToolResult:
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def fail(cls, error: str) -> ToolResult:
        return cls(success=False, error=error)


class ToolExecutor:
    """Executes tools with validation and permission checks."""

    def __init__(
        self,
        registry: ToolRegistry,
        validator: ToolValidator | None = None,
        permission_granted: bool = True,
    ) -> None:
        self._registry = registry
        self._validator = validator or ToolValidator()
        self._permission_granted = permission_granted
        self._execution_history: list[dict[str, Any]] = []

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """Execute a tool with the given arguments."""
        # Get tool schema
        try:
            schema = self._registry.get(tool_name)
        except Exception as e:
            result = ToolResult.fail(str(e))
            self._record_execution(tool_name, arguments, result)
            return result

        # Check permissions
        if schema.requires_permission and not self._permission_granted:
            result = ToolResult.fail(f"Permission denied for tool: {tool_name}")
            self._record_execution(tool_name, arguments, result)
            return result

        # Validate arguments
        try:
            validated_args = self._validator.validate(schema, arguments)
        except ValidationError as e:
            result = ToolResult.fail(f"Validation error: {e}")
            self._record_execution(tool_name, arguments, result)
            return result

        # Execute handler
        try:
            handler = self._registry.get_handler(tool_name)
            output = handler(**validated_args)
            result = ToolResult.ok(output)
        except Exception as e:
            result = ToolResult.fail(f"Execution error: {e}")

        self._record_execution(tool_name, validated_args, result)
        return result

    def _record_execution(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: ToolResult,
    ) -> None:
        """Record an execution in history."""
        self._execution_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "success": result.success,
            "error": result.error,
        })

    @property
    def execution_history(self) -> list[dict[str, Any]]:
        return self._execution_history.copy()

    def grant_permission(self) -> None:
        """Grant permission for side-effecting tools."""
        self._permission_granted = True

    def revoke_permission(self) -> None:
        """Revoke permission for side-effecting tools."""
        self._permission_granted = False
