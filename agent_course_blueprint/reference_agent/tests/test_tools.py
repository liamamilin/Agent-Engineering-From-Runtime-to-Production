import pytest

from agent_course.tools import (
    ToolSchema, ToolParameter, ParameterType,
    ToolRegistry, ToolNotFoundError,
    ToolValidator, ValidationError,
    ToolExecutor, ToolResult, PermissionDeniedError,
    create_builtin_tools,
)


class TestToolSchema:
    def test_create_schema(self):
        schema = ToolSchema(
            name="search",
            description="Search for info",
            parameters=[
                ToolParameter(name="query", type=ParameterType.STRING, required=True),
            ],
        )
        assert schema.name == "search"
        assert len(schema.parameters) == 1

    def test_to_openai_schema(self):
        schema = ToolSchema(
            name="search",
            description="Search for info",
            parameters=[
                ToolParameter(name="query", type=ParameterType.STRING, required=True),
                ToolParameter(name="limit", type=ParameterType.INTEGER, required=False, default=5),
            ],
        )
        openai = schema.to_openai_schema()
        assert openai["type"] == "function"
        assert openai["function"]["name"] == "search"
        assert "query" in openai["function"]["parameters"]["required"]
        assert "limit" not in openai["function"]["parameters"]["required"]


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        schema = ToolSchema(name="test", description="Test tool")
        registry.register(schema, lambda: None)
        assert registry.get("test") == schema

    def test_get_nonexistent_raises(self):
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent")

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(ToolSchema(name="a", description="A"), lambda: None)
        registry.register(ToolSchema(name="b", description="B"), lambda: None)
        assert len(registry.list_tools()) == 2

    def test_contains(self):
        registry = ToolRegistry()
        registry.register(ToolSchema(name="test", description="Test"), lambda: None)
        assert "test" in registry
        assert "other" not in registry


class TestToolValidator:
    def test_valid_arguments(self):
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(name="query", type=ParameterType.STRING, required=True),
            ],
        )
        validator = ToolValidator()
        result = validator.validate(schema, {"query": "hello"})
        assert result == {"query": "hello"}

    def test_missing_required_raises(self):
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(name="query", type=ParameterType.STRING, required=True),
            ],
        )
        validator = ToolValidator()
        with pytest.raises(ValidationError, match="Missing required"):
            validator.validate(schema, {})

    def test_wrong_type_raises(self):
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(name="count", type=ParameterType.INTEGER, required=True),
            ],
        )
        validator = ToolValidator()
        with pytest.raises(ValidationError, match="should be integer"):
            validator.validate(schema, {"count": "not a number"})

    def test_default_applied(self):
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(name="limit", type=ParameterType.INTEGER, required=False, default=10),
            ],
        )
        validator = ToolValidator()
        result = validator.validate(schema, {})
        assert result == {"limit": 10}

    def test_unknown_parameter_raises(self):
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters=[
                ToolParameter(name="query", type=ParameterType.STRING, required=True),
            ],
        )
        validator = ToolValidator()
        with pytest.raises(ValidationError, match="Unknown parameter"):
            validator.validate(schema, {"query": "hello", "unknown": "value"})


class TestToolExecutor:
    def test_execute_success(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        result = executor.execute("search", {"query": "Python"})
        assert result.success
        assert "results" in result.output

    def test_execute_validation_error(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        result = executor.execute("search", {})  # missing required query
        assert not result.success
        assert "Validation error" in result.error

    def test_execute_tool_not_found(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        result = executor.execute("nonexistent", {})
        assert not result.success
        assert "not found" in result.error.lower()

    def test_permission_denied(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry, permission_granted=False)
        result = executor.execute("write_file", {"path": "/tmp/test", "content": "hello"})
        assert not result.success
        assert "Permission denied" in result.error

    def test_permission_granted(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry, permission_granted=True)
        result = executor.execute("write_file", {"path": "/tmp/test", "content": "hello"})
        assert result.success

    def test_execution_history(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        executor.execute("search", {"query": "Python"})
        executor.execute("calculator", {"expression": "2+2"})
        assert len(executor.execution_history) == 2


class TestBuiltinTools:
    def test_search_tool(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        result = executor.execute("search", {"query": "test"})
        assert result.success
        assert len(result.output["results"]) > 0

    def test_calculator_tool(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry)
        result = executor.execute("calculator", {"expression": "2 + 3 * 4"})
        assert result.success
        assert result.output["result"] == 14

    def test_write_file_tool(self):
        registry = create_builtin_tools()
        executor = ToolExecutor(registry, permission_granted=True)
        result = executor.execute("write_file", {"path": "/tmp/test.txt", "content": "hello"})
        assert result.success
        assert result.output["bytes_written"] == 5
