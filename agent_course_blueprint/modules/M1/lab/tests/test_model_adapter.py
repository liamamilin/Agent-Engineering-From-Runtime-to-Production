import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.llm import (
    FakeModel, ModelResponse, Message,
    StructuredOutput, SchemaValidator,
    RetryPolicy, RetryableError
)


def test_fake_model_with_tools():
    """Test that FakeModel can return tool calls."""
    response = ModelResponse(
        content="",
        tool_calls=[{
            "id": "call_1",
            "name": "search",
            "arguments": {"query": "Python"}
        }]
    )
    model = FakeModel(responses=[response])
    result = model.complete([Message.user("Search for Python")])
    assert result.has_tool_calls
    assert result.tool_calls[0]["name"] == "search"


def test_structured_output_parsing():
    """Test that structured output can be parsed."""
    content = '{"answer": "Paris", "confidence": 0.95}'
    result = StructuredOutput.parse_json(content)
    assert result["answer"] == "Paris"
    assert result["confidence"] == 0.95


def test_schema_validation():
    """Test that schema validation works."""
    validator = SchemaValidator.for_answer()
    is_valid, errors = validator.validate({
        "answer": "Paris",
        "confidence": 0.95
    })
    assert is_valid
    assert errors == []


def test_schema_validation_missing_field():
    """Test that missing fields are caught."""
    validator = SchemaValidator.for_answer()
    is_valid, errors = validator.validate({
        "answer": "Paris"
    })
    assert not is_valid
    assert len(errors) == 1


def test_retry_policy_succeeds_after_failure():
    """Test that retry policy handles transient failures."""
    call_count = 0

    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RetryableError("Transient error")
        return ModelResponse(content="Success")

    policy = RetryPolicy(max_retries=3, base_delay=0.01)
    result = policy.execute(failing_func)
    assert result.content == "Success"
    assert call_count == 3


def test_message_roles():
    """Test that messages have correct roles."""
    system = Message.system("You are helpful")
    user = Message.user("Hello")
    assistant = Message.assistant("Hi")
    tool = Message.tool("call_1", "Result", name="search")

    assert system.role.value == "system"
    assert user.role.value == "user"
    assert assistant.role.value == "assistant"
    assert tool.role.value == "tool"
