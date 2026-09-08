"""Lab tests for M9 Multi-Agent Composition."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.composition import (
    AgentAsTool,
    Supervisor,
    Worker,
    AgentMessage,
    MessageBus,
)
from agent_course.composition.message import MessageType
from agent_course.composition.handoff import HandoffPolicy, HandoffManager
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.runtime import Agent


def test_single_agent_baseline():
    """Test single agent baseline for complex task."""
    model = FakeModel(responses=[
        ModelResponse(content="Research complete: AI is growing rapidly"),
        ModelResponse(content="Report drafted based on research"),
    ])
    agent = Agent(model=model)
    
    task = TaskSpec(
        goal="Research AI trends and write a report",
        success_criteria=["Research done", "Report written"],
        max_steps=10,
    )
    
    result = agent.run(task)
    
    assert result.success
    assert result.total_steps <= 10


def test_agent_as_tool_pattern():
    """Test agent-as-tool composition pattern."""
    # Create specialized agents
    research_model = FakeModel(responses=[
        ModelResponse(content="AI trends: LLMs, agents, multi-modal"),
    ])
    research_agent = Agent(model=research_model)
    
    writer_model = FakeModel(responses=[
        ModelResponse(content="Report: AI is transforming industries..."),
    ])
    writer_agent = Agent(model=writer_model)
    
    # Wrap as tools
    research_tool = AgentAsTool(
        agent=research_agent,
        name="research_agent",
        description="Research agent",
        input_schema={"query": {"type": "string", "description": "Research query"}},
    )
    
    writer_tool = AgentAsTool(
        agent=writer_agent,
        name="writer_agent",
        description="Writer agent",
        input_schema={"task": {"type": "string", "description": "Writing task"}},
    )
    
    # Execute tools
    research_result = research_tool.execute(query="AI trends")
    assert research_result["success"]
    assert "result" in research_result
    
    writer_result = writer_tool.execute(task="Write report about AI")
    assert writer_result["success"]
    assert "result" in writer_result


def test_supervisor_worker_pattern():
    """Test supervisor/worker composition pattern."""
    # Create workers
    researcher_model = FakeModel(responses=[
        ModelResponse(content="Research findings: ..."),
    ])
    researcher_agent = Agent(model=researcher_model)
    researcher = Worker("researcher", researcher_agent, ["research", "search"])
    
    writer_model = FakeModel(responses=[
        ModelResponse(content="Written report: ..."),
    ])
    writer_agent = Agent(model=writer_model)
    writer = Worker("writer", writer_agent, ["writing", "draft"])
    
    # Create supervisor
    supervisor_model = FakeModel()
    supervisor_agent = Agent(model=supervisor_model)
    supervisor = Supervisor(supervisor_agent, [researcher, writer])
    
    # Execute complex task
    task = TaskSpec(
        goal="Research AI and write report",
        success_criteria=["Complete"],
        max_steps=10,
    )
    
    result = supervisor.execute_with_workers(task)
    
    assert "subtask_results" in result
    assert len(result["subtask_results"]) > 0


def test_handoff_pattern():
    """Test handoff composition pattern."""
    # Create agents
    agent_a_model = FakeModel(responses=[
        ModelResponse(content="Agent A processing..."),
    ])
    agent_a = Agent(model=agent_a_model)
    
    agent_b_model = FakeModel(responses=[
        ModelResponse(content="Agent B completed task"),
    ])
    agent_b = Agent(model=agent_b_model)
    
    # Create handoff manager
    agents = {"agent_a": agent_a, "agent_b": agent_b}
    policy = HandoffPolicy(max_steps_per_agent=2)
    manager = HandoffManager(agents, policy)
    
    # Execute with potential handoff
    task = TaskSpec(goal="Complex task", max_steps=10)
    result = manager.execute_with_handoff("agent_a", task)
    
    assert "final_agent" in result
    assert "handoffs" in result


def test_message_bus_communication():
    """Test message bus for agent communication."""
    bus = MessageBus()
    
    # Create task message
    task_msg = AgentMessage.create_task(
        task_id="task_1",
        sender="supervisor",
        receiver="worker",
        task_description="Research AI",
        context={"topic": "AI"},
    )
    
    bus.send(task_msg)
    
    # Worker receives message
    received = bus.receive("worker")
    assert received is not None
    assert received.message_type == MessageType.TASK
    assert received.payload["task_id"] == "task_1"
    
    # Worker sends result
    result_msg = AgentMessage.create_result(
        task_id="task_1",
        sender="worker",
        receiver="supervisor",
        result="Research complete",
        success=True,
    )
    
    bus.send(result_msg)
    
    # Supervisor receives result
    received = bus.receive("supervisor")
    assert received is not None
    assert received.message_type == MessageType.RESULT
    assert received.payload["success"] is True


def test_context_isolation():
    """Test that agent internal state is isolated."""
    # Create worker with internal state
    worker_model = FakeModel(responses=[
        ModelResponse(content="Worker result"),
    ])
    worker_agent = Agent(model=worker_model)
    worker = Worker("worker_1", worker_agent, ["research"])
    
    # Execute task
    task = TaskSpec(goal="Research task", max_steps=5)
    result = worker.execute_task(task)
    
    # Result should not contain internal agent state
    assert "result" in result
    assert "worker_id" in result
    
    # Internal state (like model call history) should not be exposed
    assert "model" not in result
    assert "agent" not in result


def test_multi_agent_vs_single_agent():
    """Compare multi-agent vs single-agent performance."""
    # Single agent
    single_model = FakeModel(responses=[
        ModelResponse(content="Single agent result"),
    ])
    single_agent = Agent(model=single_model)
    
    task = TaskSpec(goal="Complex task", max_steps=10)
    single_result = single_agent.run(task)
    
    # Multi-agent (supervisor/worker)
    worker_model = FakeModel(responses=[
        ModelResponse(content="Worker result"),
    ])
    worker_agent = Agent(model=worker_model)
    worker = Worker("worker_1", worker_agent, ["general"])
    
    supervisor_model = FakeModel()
    supervisor_agent = Agent(model=supervisor_model)
    supervisor = Supervisor(supervisor_agent, [worker])
    
    multi_result = supervisor.execute_with_workers(task)
    
    # Both should complete
    assert single_result.success
    assert multi_result["success"]
    
    # Multi-agent may have more overhead but better specialization
    # (In this simple test, we just verify both work)


def test_worker_capability_matching():
    """Test that workers are matched to tasks by capability."""
    # Create specialized workers
    researcher_model = FakeModel()
    researcher_agent = Agent(model=researcher_model)
    researcher = Worker("researcher", researcher_agent, ["research", "search"])
    
    writer_model = FakeModel()
    writer_agent = Agent(model=writer_model)
    writer = Worker("writer", writer_agent, ["writing", "draft"])
    
    # Test capability matching
    assert researcher.can_handle("Research AI trends")
    assert researcher.can_handle("Search for papers")
    assert not researcher.can_handle("Write a report")
    
    assert writer.can_handle("Write a report")
    assert writer.can_handle("Draft document")
    assert not writer.can_handle("Research topics")
