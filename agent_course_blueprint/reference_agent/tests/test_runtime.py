import pytest

from agent_course.core import TaskSpec, Observation, AgentState, Decision
from agent_course.llm import FakeModel, ModelResponse, Message
from agent_course.tools import create_builtin_tools
from agent_course.runtime import ContextBuilder, ModelPolicy, Agent


class TestContextBuilder:
    def test_build_basic_context(self):
        builder = ContextBuilder(system_prompt="You are helpful")
        task = TaskSpec(goal="Answer question")
        state = AgentState(task=task)

        messages = builder.build(task, state)

        assert len(messages) >= 2
        assert messages[0].role.value == "system"
        assert "Answer question" in messages[1].content

    def test_build_with_observation(self):
        builder = ContextBuilder()
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_user("Hello")

        messages = builder.build(task, state, obs)

        assert any("Hello" in m.content for m in messages)


class TestModelPolicy:
    def test_decide_final_answer(self):
        model = FakeModel(responses=[ModelResponse(content="The answer is 42")])
        policy = ModelPolicy(model)
        task = TaskSpec(goal="Answer")
        state = AgentState(task=task)

        decision = policy.decide(task, state)

        assert decision.kind == "final"
        assert "42" in decision.content

    def test_decide_tool_call(self):
        response = ModelResponse(
            content="",
            tool_calls=[{"name": "search", "arguments": {"query": "test"}}],
        )
        model = FakeModel(responses=[response])
        policy = ModelPolicy(model)
        task = TaskSpec(goal="Search")
        state = AgentState(task=task)

        decision = policy.decide(task, state)

        assert decision.kind == "tool"
        assert decision.name == "search"


class TestAgent:
    def test_simple_run(self):
        """Test a simple agent run with final answer."""
        model = FakeModel(responses=[
            ModelResponse(content="The answer is 42"),
        ])
        agent = Agent(model=model)
        task = TaskSpec(goal="Answer the question", max_steps=5)

        result = agent.run(task)

        assert result.success
        assert result.output == "The answer is 42"
        assert result.total_steps == 1

    def test_run_with_tool_call(self):
        """Test agent run with tool call."""
        # First response: tool call, second: final answer
        model = FakeModel(responses=[
            ModelResponse(
                content="",
                tool_calls=[{"name": "calculator", "arguments": {"expression": "2+2"}}],
            ),
            ModelResponse(content="The result is 4"),
        ])
        tools = create_builtin_tools()
        agent = Agent(model=model, tools=tools)
        task = TaskSpec(goal="Calculate 2+2", max_steps=5)

        result = agent.run(task)

        assert result.success
        assert result.total_steps == 2
        assert result.trace is not None
        assert len(result.trace.steps) == 2

    def test_run_max_steps_termination(self):
        """Test that agent terminates at max steps."""
        # Model always returns tool calls, never final answer
        model = FakeModel(default_response="")
        # Override to always return tool call
        model._responses = []
        model._tool_responses = {}

        tools = create_builtin_tools()
        agent = Agent(model=model, tools=tools)
        task = TaskSpec(goal="Infinite task", max_steps=3)

        result = agent.run(task)

        assert result.total_steps <= 3
        assert result.termination_reason in ["max_steps", "failed"]

    def test_run_failure_termination(self):
        """Test agent failure termination."""
        model = FakeModel(responses=[
            ModelResponse(content=""),  # Empty response -> fail
        ])
        agent = Agent(model=model)
        task = TaskSpec(goal="Test", max_steps=5)

        result = agent.run(task)

        # Empty response should lead to fail decision
        assert result.termination_reason in ["failed", "final_decision"]

    def test_trace_recorded(self):
        """Test that trace is recorded."""
        model = FakeModel(responses=[
            ModelResponse(
                content="",
                tool_calls=[{"name": "search", "arguments": {"query": "test"}}],
            ),
            ModelResponse(content="Done"),
        ])
        tools = create_builtin_tools()
        agent = Agent(model=model, tools=tools)
        task = TaskSpec(goal="Test", max_steps=5)

        result = agent.run(task)

        assert result.trace is not None
        assert result.trace.total_steps == 2
        assert result.trace.steps[0].decision["kind"] == "tool"
        assert result.trace.steps[1].decision["kind"] == "final"
