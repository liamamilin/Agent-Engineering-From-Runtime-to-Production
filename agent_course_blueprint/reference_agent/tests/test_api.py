"""Tests for API module (M11)."""

import pytest
import tempfile
from pathlib import Path

from agent_course.api import (
    Config,
    ConfigManager,
    Session,
    SessionManager,
    AgentService,
    ServiceConfig,
    CLI,
    CLICommand,
    MetricsCollector,
    HealthChecker,
)
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.runtime import Agent


class TestConfig:
    """Tests for Config."""
    
    def test_create_config(self):
        """Test creating a config."""
        config = Config()
        assert config.model_provider == "openai"
        assert config.max_steps == 20
    
    def test_config_to_dict(self):
        """Test config to_dict."""
        config = Config(model_name="gpt-4", max_steps=50)
        data = config.to_dict()
        assert data["model_name"] == "gpt-4"
        assert data["max_steps"] == 50
    
    def test_config_from_dict(self):
        """Test config from_dict."""
        data = {"model_name": "gpt-4", "max_steps": 50}
        config = Config.from_dict(data)
        assert config.model_name == "gpt-4"
        assert config.max_steps == 50
    
    def test_config_get_set(self):
        """Test config get and set."""
        config = Config()
        config.set("model_name", "gpt-4")
        assert config.get("model_name") == "gpt-4"
        
        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"


class TestConfigManager:
    """Tests for ConfigManager."""
    
    def test_load_default_config(self):
        """Test loading default config."""
        manager = ConfigManager()
        config = manager.load()
        assert config is not None
        assert config.model_provider == "openai"
    
    def test_save_and_load_config(self):
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)
            
            # Save config
            config = Config(model_name="gpt-4", max_steps=50)
            manager.save(config)
            
            # Load config
            manager2 = ConfigManager(config_path)
            loaded = manager2.load()
            assert loaded.model_name == "gpt-4"
            assert loaded.max_steps == 50


class TestSession:
    """Tests for Session."""
    
    def test_create_session(self):
        """Test creating a session."""
        session = Session(id="test", agent_id="agent_1")
        assert session.id == "test"
        assert session.agent_id == "agent_1"
        assert session.is_active
    
    def test_session_state(self):
        """Test session state management."""
        session = Session(id="test", agent_id="agent_1")
        session.update_state("key", "value")
        assert session.get_state("key") == "value"
        assert session.get_state("missing", "default") == "default"
    
    def test_session_close(self):
        """Test closing a session."""
        session = Session(id="test", agent_id="agent_1")
        assert session.is_active
        session.close()
        assert not session.is_active


class TestSessionManager:
    """Tests for SessionManager."""
    
    def test_create_session(self):
        """Test creating a session."""
        manager = SessionManager()
        session = manager.create_session("agent_1")
        assert session is not None
        assert session.agent_id == "agent_1"
    
    def test_get_session(self):
        """Test getting a session."""
        manager = SessionManager()
        session = manager.create_session("agent_1")
        retrieved = manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
    
    def test_close_session(self):
        """Test closing a session."""
        manager = SessionManager()
        session = manager.create_session("agent_1")
        assert manager.close_session(session.id)
        
        retrieved = manager.get_session(session.id)
        assert retrieved is not None
        assert not retrieved.is_active
    
    def test_list_sessions(self):
        """Test listing sessions."""
        manager = SessionManager()
        manager.create_session("agent_1")
        manager.create_session("agent_2")
        
        sessions = manager.list_sessions()
        assert len(sessions) == 2
        
        sessions = manager.list_sessions(agent_id="agent_1")
        assert len(sessions) == 1


class TestAgentService:
    """Tests for AgentService."""
    
    def test_create_service(self):
        """Test creating a service."""
        model = FakeModel()
        agent = Agent(model=model)
        service = AgentService(agent)
        assert service is not None
    
    def test_run_task(self):
        """Test running a task."""
        model = FakeModel(responses=[ModelResponse(content="Result")])
        agent = Agent(model=model)
        service = AgentService(agent)
        
        task = TaskSpec(goal="Test task")
        result = service.run_task(task)
        
        assert result["success"]
        assert "output" in result
        assert "session_id" in result
    
    def test_get_status(self):
        """Test getting service status."""
        model = FakeModel()
        agent = Agent(model=model)
        service = AgentService(agent)
        
        status = service.get_status()
        assert status["status"] == "running"
        assert "request_count" in status
        assert "error_count" in status
    
    def test_session_management(self):
        """Test session management in service."""
        model = FakeModel(responses=[ModelResponse(content="Result")])
        agent = Agent(model=model)
        service = AgentService(agent)
        
        # Run task creates session
        task = TaskSpec(goal="Test")
        result = service.run_task(task)
        session_id = result["session_id"]
        
        # Get session
        session = service.get_session(session_id)
        assert session is not None
        
        # List sessions
        sessions = service.list_sessions()
        assert len(sessions) == 1
        
        # Close session
        assert service.close_session(session_id)


class TestMetricsCollector:
    """Tests for MetricsCollector."""
    
    def test_record_request(self):
        """Test recording a request."""
        collector = MetricsCollector()
        collector.record_request(latency_ms=100.0, tokens=50, success=True)
        
        assert collector.request_count == 1
        assert collector.total_tokens == 50
        assert collector.total_latency_ms == 100.0
    
    def test_record_error(self):
        """Test recording an error."""
        collector = MetricsCollector()
        collector.record_request(latency_ms=100.0, tokens=50, success=False)
        
        assert collector.error_count == 1
        assert collector.get_error_rate() == 1.0
    
    def test_average_latency(self):
        """Test average latency calculation."""
        collector = MetricsCollector()
        collector.record_request(latency_ms=100.0, success=True)
        collector.record_request(latency_ms=200.0, success=True)
        
        assert collector.get_average_latency() == 150.0
    
    def test_custom_metrics(self):
        """Test custom metrics."""
        collector = MetricsCollector()
        collector.record_metric("custom", 10.0)
        collector.record_metric("custom", 20.0)
        
        assert collector.custom_metrics["custom"] == 30.0
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()
        collector.record_request(latency_ms=100.0, tokens=50, success=True)
        
        summary = collector.get_summary()
        assert "request_count" in summary
        assert "error_rate" in summary
        assert "average_latency_ms" in summary


class TestHealthChecker:
    """Tests for HealthChecker."""
    
    def test_add_check(self):
        """Test adding a health check."""
        checker = HealthChecker()
        checker.add_check("test", lambda: True)
        assert "test" in checker.checks
    
    def test_run_checks(self):
        """Test running health checks."""
        checker = HealthChecker()
        checker.add_check("healthy", lambda: True)
        checker.add_check("unhealthy", lambda: False)
        
        results = checker.run_checks()
        assert results["healthy"] is True
        assert results["unhealthy"] is False
    
    def test_is_healthy(self):
        """Test is_healthy."""
        checker = HealthChecker()
        checker.add_check("check1", lambda: True)
        checker.add_check("check2", lambda: True)
        
        assert checker.is_healthy()
        
        checker.add_check("check3", lambda: False)
        checker.run_checks()
        assert not checker.is_healthy()
    
    def test_get_status(self):
        """Test getting health status."""
        checker = HealthChecker()
        checker.add_check("check", lambda: True)
        
        status = checker.get_status()
        assert "healthy" in status
        assert "checks" in status
        assert "last_check_time" in status
