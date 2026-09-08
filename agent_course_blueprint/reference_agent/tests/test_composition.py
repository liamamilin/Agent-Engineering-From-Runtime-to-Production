"""Tests for composition module (M9)."""

import pytest

from agent_course.composition import (
    AgentAsTool,
    Handoff,
    HandoffDecision,
    Supervisor,
    Worker,
    TaskDelegation,
    AgentMessage,
    MessageBus,
)
from agent_course.composition.message import MessageType
from agent_course.composition.handoff import HandoffPolicy, HandoffManager
from agent_course.core import TaskSpec, AgentState
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent


class TestAgentMessage:
    """Tests for AgentMessage."""
    
    def test_create_message(self):
        """Test creating a message."""
        msg = AgentMessage(
            id="msg_1",
            sender="agent_a",
            receiver="agent_b",
            message_type=MessageType.TASK,
            payload={"task": "Do something"},
        )
        assert msg.id == "msg_1"
        assert msg.sender == "agent_a"
        assert msg.receiver == "agent_b"
        assert msg.message_type == MessageType.TASK
    
    def test_create_task_message(self):
        """Test creating a task message."""
        msg = AgentMessage.create_task(
            task_id="task_1",
            sender="supervisor",
            receiver="worker",
            task_description="Research topic",
            context={"topic": "AI"},
        )
        assert msg.message_type == MessageType.TASK
        assert msg.payload["task_id"] == "task_1"
        assert msg.payload["description"] == "Research topic"
    
    def test_create_result_message(self):
        """Test creating a result message."""
        msg = AgentMessage.create_result(
            task_id="task_1",
            sender="worker",
            receiver="supervisor",
            result="Found 5 papers",
            success=True,
        )
        assert msg.message_type == MessageType.RESULT
        assert msg.payload["result"] == "Found 5 papers"
        assert msg.payload["success"] is True
        assert msg.reply_to == "msg_task_1"
    
    def test_message_serialization(self):
        """Test message to_dict and from_dict."""
        msg = AgentMessage(
            id="msg_1",
            sender="a",
            receiver="b",
            message_type=MessageType.QUERY,
            payload={"query": "test"},
        )
        data = msg.to_dict()
        restored = AgentMessage.from_dict(data)
        assert restored.id == msg.id
        assert restored.message_type == msg.message_type


class TestMessageBus:
    """Tests for MessageBus."""
    
    def test_send_and_receive(self):
        """Test sending and receiving messages."""
        bus = MessageBus()
        msg = AgentMessage(
            id="msg_1",
            sender="a",
            receiver="b",
            message_type=MessageType.TASK,
            payload={},
        )
        bus.send(msg)
        
        assert bus.has_messages("b")
        received = bus.receive("b")
        assert received is not None
        assert received.id == "msg_1"
        
        # Queue should be empty now
        assert not bus.has_messages("b")
    
    def test_peek_message(self):
        """Test peeking at messages."""
        bus = MessageBus()
        msg = AgentMessage(
            id="msg_1",
            sender="a",
            receiver="b",
            message_type=MessageType.TASK,
            payload={},
        )
        bus.send(msg)
        
        peeked = bus.peek("b")
        assert peeked is not None
        assert peeked.id == "msg_1"
        
        # Message should still be in queue
        assert bus.has_messages("b")
    
    def test_message_history(self):
        """Test message history."""
        bus = MessageBus()
        msg1 = AgentMessage(
            id="msg_1",
            sender="a",
            receiver="b",
            message_type=MessageType.TASK,
            payload={},
        )
        msg2 = AgentMessage(
            id="msg_2",
            sender="b",
            receiver="a",
            message_type=MessageType.RESULT,
            payload={},
        )
        bus.send(msg1)
        bus.send(msg2)
        
        history = bus.get_history()
        assert len(history) == 2
        
        # Filter by agent
        a_history = bus.get_history("a")
        assert len(a_history) == 2  # Both messages involve agent a


class TestHandoff:
    """Tests for Handoff."""
    
    def test_create_handoff(self):
        """Test creating a handoff."""
        handoff = Handoff(
            from_agent="agent_a",
            to_agent="agent_b",
            reason="Task requires specialized knowledge",
            context={"task": "Complex analysis"},
        )
        assert handoff.from_agent == "agent_a"
        assert handoff.to_agent == "agent_b"
        assert handoff.reason == "Task requires specialized knowledge"
    
    def test_handoff_serialization(self):
        """Test handoff serialization."""
        handoff = Handoff(
            from_agent="a",
            to_agent="b",
            reason="test",
        )
        data = handoff.to_dict()
        restored = Handoff.from_dict(data)
        assert restored.from_agent == handoff.from_agent
        assert restored.to_agent == handoff.to_agent


class TestHandoffPolicy:
    """Tests for HandoffPolicy."""
    
    def test_should_continue(self):
        """Test policy decides to continue."""
        policy = HandoffPolicy(max_steps_per_agent=10)
        task = TaskSpec(goal="Test", max_steps=20)
        state = AgentState(task=task)
        state.step_count = 5
        
        decision = policy.should_handoff("agent_a", state, ["agent_a", "agent_b"])
        assert decision == HandoffDecision.CONTINUE
    
    def test_should_handoff_on_max_steps(self):
        """Test policy decides to handoff when max steps reached."""
        policy = HandoffPolicy(max_steps_per_agent=5)
        task = TaskSpec(goal="Test", max_steps=20)
        state = AgentState(task=task)
        state.step_count = 5
        
        decision = policy.should_handoff("agent_a", state, ["agent_a", "agent_b"])
        assert decision == HandoffDecision.HANDOFF
    
    def test_should_complete(self):
        """Test policy decides to complete."""
        policy = HandoffPolicy()
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        state.status = "completed"
        
        decision = policy.should_handoff("agent_a", state, ["agent_a"])
        assert decision == HandoffDecision.COMPLETE


class TestAgentAsTool:
    """Tests for AgentAsTool."""
    
    def test_create_agent_as_tool(self):
        """Test creating an agent-as-tool."""
        model = FakeModel(responses=[ModelResponse(content="Result")])
        agent = Agent(model=model)
        
        agent_tool = AgentAsTool(
            agent=agent,
            name="test_agent",
            description="Test agent",
            input_schema={
                "query": {
                    "type": "string",
                    "description": "Query",
                    "required": True,
                }
            },
        )
        
        assert agent_tool.name == "test_agent"
        assert agent_tool.description == "Test agent"
    
    def test_get_tool_schema(self):
        """Test getting tool schema from agent-as-tool."""
        model = FakeModel()
        agent = Agent(model=model)
        
        agent_tool = AgentAsTool(
            agent=agent,
            name="research_agent",
            description="Research agent",
            input_schema={
                "query": {
                    "type": "string",
                    "description": "Search query",
                    "required": True,
                }
            },
        )
        
        schema = agent_tool.get_tool_schema()
        assert schema.name == "research_agent"
        assert len(schema.parameters) == 1
        assert schema.parameters[0].name == "query"
    
    def test_execute_agent_as_tool(self):
        """Test executing an agent-as-tool."""
        model = FakeModel(responses=[
            ModelResponse(content="Research complete"),
        ])
        agent = Agent(model=model)
        
        agent_tool = AgentAsTool(
            agent=agent,
            name="research_agent",
            description="Research agent",
        )
        
        result = agent_tool.execute(query="AI trends")
        assert "result" in result
        assert "success" in result


class TestWorker:
    """Tests for Worker."""
    
    def test_create_worker(self):
        """Test creating a worker."""
        model = FakeModel()
        agent = Agent(model=model)
        
        worker = Worker(
            worker_id="worker_1",
            agent=agent,
            capabilities=["research", "analysis"],
        )
        
        assert worker.worker_id == "worker_1"
        assert "research" in worker.capabilities
    
    def test_worker_can_handle(self):
        """Test worker capability matching."""
        model = FakeModel()
        agent = Agent(model=model)
        
        worker = Worker(
            worker_id="worker_1",
            agent=agent,
            capabilities=["research", "analysis"],
        )
        
        assert worker.can_handle("Research AI trends")
        assert worker.can_handle("Analyze data")
        assert not worker.can_handle("Write code")
    
    def test_worker_execute_task(self):
        """Test worker executing a task."""
        model = FakeModel(responses=[
            ModelResponse(content="Task complete"),
        ])
        agent = Agent(model=model)
        
        worker = Worker(
            worker_id="worker_1",
            agent=agent,
            capabilities=["general"],
        )
        
        task = TaskSpec(goal="Do something", max_steps=5)
        result = worker.execute_task(task)
        
        assert "worker_id" in result
        assert result["worker_id"] == "worker_1"
        assert worker.tasks_completed == 1


class TestSupervisor:
    """Tests for Supervisor."""
    
    def test_create_supervisor(self):
        """Test creating a supervisor."""
        supervisor_model = FakeModel()
        supervisor_agent = Agent(model=supervisor_model)
        
        worker_model = FakeModel()
        worker_agent = Agent(model=worker_model)
        worker = Worker("worker_1", worker_agent, ["research"])
        
        supervisor = Supervisor(supervisor_agent, [worker])
        
        assert len(supervisor.workers) == 1
    
    def test_decompose_task(self):
        """Test task decomposition."""
        supervisor_model = FakeModel()
        supervisor_agent = Agent(model=supervisor_model)
        
        supervisor = Supervisor(supervisor_agent, [])
        
        task = TaskSpec(goal="Research and write about AI")
        subtasks = supervisor.decompose_task(task)
        
        assert len(subtasks) >= 1
        assert any("research" in st["description"].lower() for st in subtasks)
    
    def test_assign_worker(self):
        """Test worker assignment."""
        supervisor_model = FakeModel()
        supervisor_agent = Agent(model=supervisor_model)
        
        worker_model = FakeModel()
        worker_agent = Agent(model=worker_model)
        worker = Worker("worker_1", worker_agent, ["research"])
        
        supervisor = Supervisor(supervisor_agent, [worker])
        
        subtask = {
            "task_id": "research_1",
            "description": "Research AI",
            "required_capability": "research",
        }
        
        assigned = supervisor.assign_worker(subtask)
        assert assigned == "worker_1"
    
    def test_get_worker_stats(self):
        """Test getting worker statistics."""
        supervisor_model = FakeModel()
        supervisor_agent = Agent(model=supervisor_model)
        
        worker_model = FakeModel()
        worker_agent = Agent(model=worker_model)
        worker = Worker("worker_1", worker_agent, ["research"])
        worker.tasks_completed = 5
        worker.tasks_failed = 2
        
        supervisor = Supervisor(supervisor_agent, [worker])
        
        stats = supervisor.get_worker_stats()
        assert stats["worker_1"]["tasks_completed"] == 5
        assert stats["worker_1"]["tasks_failed"] == 2
