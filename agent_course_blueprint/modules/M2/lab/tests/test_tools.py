import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.tools import (
    create_builtin_tools, ToolExecutor, ToolResult
)


def test_builtin_tools_registry():
    """Test that builtin tools are registered."""
    registry = create_builtin_tools()
    assert "search" in registry
    assert "calculator" in registry
    assert "write_file" in registry
    assert len(registry.list_tools()) == 3


def test_search_tool_execution():
    """Test search tool execution."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("search", {"query": "Python"})
    assert result.success
    assert "results" in result.output


def test_calculator_tool_execution():
    """Test calculator tool execution."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("calculator", {"expression": "10 + 5 * 2"})
    assert result.success
    assert result.output["result"] == 20


def test_write_file_permission_denied():
    """Test write_file requires permission."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry, permission_granted=False)
    result = executor.execute("write_file", {"path": "/tmp/test.txt", "content": "hello"})
    assert not result.success
    assert "Permission denied" in result.error


def test_write_file_permission_granted():
    """Test write_file with permission."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry, permission_granted=True)
    result = executor.execute("write_file", {"path": "/tmp/test.txt", "content": "hello"})
    assert result.success
    assert result.output["bytes_written"] == 5


def test_invalid_arguments():
    """Test that invalid arguments are caught."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("search", {})  # missing required query
    assert not result.success
    assert "Validation error" in result.error


def test_wrong_argument_type():
    """Test that wrong argument types are caught."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("search", {"query": "test", "max_results": "five"})
    assert not result.success
    assert "Validation error" in result.error


def test_tool_not_found():
    """Test that nonexistent tools are handled."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("nonexistent_tool", {})
    assert not result.success
    assert "not found" in result.error.lower()


def test_execution_history():
    """Test that execution history is recorded."""
    registry = create_builtin_tools()
    executor = ToolExecutor(registry)
    executor.execute("search", {"query": "Python"})
    executor.execute("calculator", {"expression": "2+2"})
    assert len(executor.execution_history) == 2
    assert executor.execution_history[0]["tool"] == "search"
    assert executor.execution_history[1]["tool"] == "calculator"
