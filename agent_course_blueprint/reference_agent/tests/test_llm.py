import pytest

from agent_course.llm import FakeModel, ModelResponse, Message


class TestFakeModel:
    def test_default_response(self):
        model = FakeModel()
        response = model.complete([Message.user("Hello")])
        assert response.content == "I don't know."

    def test_predefined_responses(self):
        responses = [
            ModelResponse(content="First"),
            ModelResponse(content="Second"),
        ]
        model = FakeModel(responses=responses)

        r1 = model.complete([Message.user("1")])
        r2 = model.complete([Message.user("2")])
        r3 = model.complete([Message.user("3")])

        assert r1.content == "First"
        assert r2.content == "Second"
        assert r3.content == "I don't know."

    def test_call_count(self):
        model = FakeModel()
        assert model.call_count == 0
        model.complete([Message.user("1")])
        assert model.call_count == 1
        model.complete([Message.user("2")])
        assert model.call_count == 2

    def test_reset(self):
        model = FakeModel()
        model.complete([Message.user("1")])
        model.reset()
        assert model.call_count == 0

    def test_tool_calls_in_response(self):
        response = ModelResponse(
            content="",
            tool_calls=[{"id": "call_1", "name": "search", "arguments": {"query": "test"}}],
        )
        model = FakeModel(responses=[response])
        result = model.complete([Message.user("Search")])
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "search"

    def test_call_history(self):
        model = FakeModel()
        model.complete([Message.user("Hello")])
        model.complete([Message.user("World")])

        assert len(model.call_history) == 2
        assert model.call_history[0]["messages"][0]["content"] == "Hello"
        assert model.call_history[1]["messages"][0]["content"] == "World"

    def test_tool_response_pattern(self):
        model = FakeModel(
            tool_responses={
                "search": ModelResponse(content="Search results here"),
            }
        )
        result = model.complete([Message.user("Please search for something")])
        assert result.content == "Search results here"

    def test_auto_tool_call_when_tools_available(self):
        model = FakeModel()
        tools = [{"name": "search", "description": "Search the web"}]
        result = model.complete([Message.user("Find info")], tools=tools)
        assert result.has_tool_calls
        assert result.tool_calls[0]["name"] == "search"


class TestMessage:
    def test_system_message(self):
        msg = Message.system("You are helpful")
        assert msg.role.value == "system"
        assert msg.content == "You are helpful"

    def test_user_message(self):
        msg = Message.user("Hello")
        assert msg.role.value == "user"

    def test_assistant_message(self):
        msg = Message.assistant("Hi there")
        assert msg.role.value == "assistant"

    def test_tool_message(self):
        msg = Message.tool("call_1", "Result here", name="search")
        assert msg.role.value == "tool"
        assert msg.tool_call_id == "call_1"
        assert msg.name == "search"

    def test_to_dict(self):
        msg = Message.user("Hello")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello"}


class TestModelResponse:
    def test_has_tool_calls(self):
        r1 = ModelResponse(content="text")
        assert not r1.has_tool_calls

        r2 = ModelResponse(content="", tool_calls=[{"name": "search"}])
        assert r2.has_tool_calls

    def test_token_usage(self):
        r = ModelResponse(
            content="text",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        assert r.prompt_tokens == 10
        assert r.completion_tokens == 20
        assert r.total_tokens == 30
