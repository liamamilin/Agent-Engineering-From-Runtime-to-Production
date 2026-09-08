"""Lab tests for M11 Production Delivery & Operations."""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.api import (
    Config,
    ConfigManager,
    Session,
    SessionManager,
    AgentService,
    MetricsCollector,
    HealthChecker,
)
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.runtime import Agent


def test_config_management():
    """Test configuration management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        # Create and save config
        manager = ConfigManager(config_path)
        config = Config(
            model_name="gpt-4",
            max_steps=50,
            temperature=0.8,
        )
        manager.save(config)
        
        # Load config
        manager2 = ConfigManager(config_path)
        loaded = manager2.load()
        
        assert loaded.model_name == "gpt-4"
        assert loaded.max_steps == 50
        assert loaded.temperature == 0.8


def test_session_management():
    """Test session management."""
    manager = SessionManager()
    
    # Create session
    session = manager.create_session("agent_1", metadata={"user": "test_user"})
    assert session is not None
    assert session.agent_id == "agent_1"
    assert session.is_active
    
    # Update session state
    session.update_state("last_task", "Research AI")
    assert session.get_state("last_task") == "Research AI"
    
    # Get session
    retrieved = manager.get_session(session.id)
    assert retrieved is not None
    assert retrieved.id == session.id
    
    # List sessions
    sessions = manager.list_sessions()
    assert len(sessions) == 1
    
    # Close session
    manager.close_session(session.id)
    retrieved = manager.get_session(session.id)
    assert retrieved is not None
    assert not retrieved.is_active


def test_agent_service():
    """Test agent service."""
    model = FakeModel(responses=[
        ModelResponse(content="Research complete"),
    ])
    agent = Agent(model=model)
    service = AgentService(agent)
    
    # Run task
    task = TaskSpec(goal="Research AI trends", max_steps=5)
    result = service.run_task(task)
    
    assert result["success"]
    assert "output" in result
    assert "session_id" in result
    
    # Get status
    status = service.get_status()
    assert status["status"] == "running"
    assert status["request_count"] == 1
    
    # Get session
    session_id = result["session_id"]
    session = service.get_session(session_id)
    assert session is not None
    
    # List sessions
    sessions = service.list_sessions()
    assert len(sessions) == 1


def test_metrics_collection():
    """Test metrics collection."""
    collector = MetricsCollector()
    
    # Record requests
    collector.record_request(latency_ms=100.0, tokens=50, success=True)
    collector.record_request(latency_ms=200.0, tokens=100, success=True)
    collector.record_request(latency_ms=150.0, tokens=75, success=False)
    
    # Check metrics
    assert collector.request_count == 3
    assert collector.error_count == 1
    assert collector.total_tokens == 225
    
    # Check calculated metrics
    assert collector.get_average_latency() == 150.0
    assert abs(collector.get_error_rate() - 1/3) < 0.01
    
    # Get summary
    summary = collector.get_summary()
    assert "request_count" in summary
    assert "error_rate" in summary
    assert "average_latency_ms" in summary


def test_health_checking():
    """Test health checking."""
    checker = HealthChecker()
    
    # Add checks
    checker.add_check("agent_alive", lambda: True)
    checker.add_check("model_available", lambda: True)
    
    # Run checks
    results = checker.run_checks()
    assert results["agent_alive"] is True
    assert results["model_available"] is True
    
    # Check health
    assert checker.is_healthy()
    
    # Add failing check
    checker.add_check("database", lambda: False)
    checker.run_checks()
    assert not checker.is_healthy()
    
    # Get status
    status = checker.get_status()
    assert "healthy" in status
    assert "checks" in status


def test_full_production_workflow():
    """Test full production workflow."""
    # 1. Load configuration
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_manager = ConfigManager(config_path)
        config = Config(model_name="gpt-4", max_steps=50)
        config_manager.save(config)
        
        # 2. Create agent and service
        model = FakeModel(responses=[
            ModelResponse(content="Task completed"),
        ])
        agent = Agent(model=model)
        service = AgentService(agent, config)
        
        # 3. Run task (service creates its own session)
        task = TaskSpec(goal="Complete task", max_steps=10)
        result = service.run_task(task)
        
        assert result["success"]
        
        # 4. Collect metrics
        metrics = MetricsCollector()
        metrics.record_request(latency_ms=100.0, tokens=50, success=True)
        
        # 5. Check health
        health = HealthChecker()
        health.add_check("service_running", lambda: True)
        assert health.is_healthy()
        
        # 6. Verify everything works together
        status = service.get_status()
        assert status["request_count"] == 1
        
        summary = metrics.get_summary()
        assert summary["request_count"] == 1
        
        health_status = health.get_status()
        assert health_status["healthy"] is True
