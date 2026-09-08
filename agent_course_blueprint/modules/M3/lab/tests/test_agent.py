import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent


def test_agent_simple_task():
    """Test agent with simple final answer."""
    model = FakeModel(responses=[
        ModelResponse(content="The answer is 42"),
    ])
    agent = Agent(model=model)
    task = TaskSpec(goal="Answer the question", max_steps=5)

    result = agent.run(task)

    assert result.success
    assert result.output == "The answer is 42"
    assert result.total_steps == 1


def test_agent_with_tool_calls():
    """Test agent that uses tools."""
    model = FakeModel(responses=[
        ModelResponse(
            content="",
            tool_calls=[{"name": "calculator", "arguments": {"expression": "10 * 5"}}],
        ),
        ModelResponse(content="The result is 50"),
    ])
    tools = create_builtin_tools()
    agent = Agent(model=model, tools=tools)
    task = TaskSpec(goal="Calculate 10 * 5", max_steps=5)

    result = agent.run(task)

    assert result.success
    assert result.total_steps == 2
    assert result.trace is not None
    assert len(result.trace.steps) == 2


def test_agent_max_steps_termination():
    """Test that agent terminates at max steps."""
    # Model always returns tool calls
    model = FakeModel()
    model._tool_responses = {}  # No pattern matching

    tools = create_builtin_tools()
    agent = Agent(model=model, tools=tools)
    task = TaskSpec(goal="Infinite task", max_steps=3)

    result = agent.run(task)

    assert result.total_steps <= 3


def test_agent_trace_contains_decisions():
    """Test that trace records all decisions."""
    model = FakeModel(responses=[
        ModelResponse(
            content="",
            tool_calls=[{"name": "search", "arguments": {"query": "Python"}}],
        ),
        ModelResponse(content="Python is a programming language"),
    ])
    tools = create_builtin_tools()
    agent = Agent(model=model, tools=tools)
    task = TaskSpec(goal="What is Python?", max_steps=5)

    result = agent.run(task)

    assert result.trace is not None
    decisions = [step.decision for step in result.trace.steps]
    assert decisions[0]["kind"] == "tool"
    assert decisions[0]["name"] == "search"
    assert decisions[1]["kind"] == "final"


def test_agent_multiple_tool_calls():
    """Test agent with multiple tool calls."""
    model = FakeModel(responses=[
        ModelResponse(
            content="",
            tool_calls=[{"name": "search", "arguments": {"query": "Python"}}],
        ),
        ModelResponse(
            content="",
            tool_calls=[{"name": "calculator", "arguments": {"expression": "2+2"}}],
        ),
        ModelResponse(content="Done"),
    ])
    tools = create_builtin_tools()
    agent = Agent(model=model, tools=tools)
    task = TaskSpec(goal="Search and calculate", max_steps=10)

    result = agent.run(task)

    assert result.success
    assert result.total_steps == 3
    tool_calls = [s for s in result.trace.steps if s.decision["kind"] == "tool"]
    assert len(tool_calls) == 2
