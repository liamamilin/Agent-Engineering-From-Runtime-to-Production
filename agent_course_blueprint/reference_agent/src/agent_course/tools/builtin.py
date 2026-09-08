from __future__ import annotations

import json
from typing import Any

from agent_course.tools.schema import ToolSchema, ToolParameter, ParameterType
from agent_course.tools.registry import ToolRegistry


def search_tool_handler(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search for information (fake implementation)."""
    # Fake search results
    results = [
        {"title": f"Result {i} for '{query}'", "snippet": f"This is result {i}."}
        for i in range(1, min(max_results, 3) + 1)
    ]
    return {"query": query, "results": results}


def calculator_tool_handler(expression: str) -> dict[str, Any]:
    """Evaluate a mathematical expression."""
    try:
        # Safe evaluation of simple math expressions
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression"}
        result = eval(expression)  # noqa: S307
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


def write_file_tool_handler(path: str, content: str) -> dict[str, Any]:
    """Write content to a file (fake implementation)."""
    # Fake file write
    return {
        "path": path,
        "bytes_written": len(content),
        "status": "success",
    }


def create_builtin_tools() -> ToolRegistry:
    """Create a registry with built-in tools."""
    registry = ToolRegistry()

    # Search tool (read-only)
    search_schema = ToolSchema(
        name="search",
        description="Search for information on a topic",
        parameters=[
            ToolParameter(
                name="query",
                type=ParameterType.STRING,
                description="The search query",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type=ParameterType.INTEGER,
                description="Maximum number of results to return",
                required=False,
                default=5,
            ),
        ],
        requires_permission=False,
        idempotent=True,
    )
    registry.register(search_schema, search_tool_handler)

    # Calculator tool (read-only)
    calc_schema = ToolSchema(
        name="calculator",
        description="Evaluate a mathematical expression",
        parameters=[
            ToolParameter(
                name="expression",
                type=ParameterType.STRING,
                description="The mathematical expression to evaluate",
                required=True,
            ),
        ],
        requires_permission=False,
        idempotent=True,
    )
    registry.register(calc_schema, calculator_tool_handler)

    # Write file tool (side-effecting)
    write_schema = ToolSchema(
        name="write_file",
        description="Write content to a file",
        parameters=[
            ToolParameter(
                name="path",
                type=ParameterType.STRING,
                description="The file path to write to",
                required=True,
            ),
            ToolParameter(
                name="content",
                type=ParameterType.STRING,
                description="The content to write",
                required=True,
            ),
        ],
        requires_permission=True,
        idempotent=False,
    )
    registry.register(write_schema, write_file_tool_handler)

    return registry
