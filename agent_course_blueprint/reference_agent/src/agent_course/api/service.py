"""Agent service for production deployment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.api.config import Config
from agent_course.api.session import SessionManager
from agent_course.core import TaskSpec
from agent_course.runtime import Agent, AgentRunResult


@dataclass
class ServiceConfig:
    """Configuration for agent service."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "debug": self.debug,
            "cors_origins": self.cors_origins,
        }


class AgentService:
    """Service for running agents in production."""
    
    def __init__(
        self,
        agent: Agent,
        config: Config | None = None,
        service_config: ServiceConfig | None = None,
    ) -> None:
        """Initialize agent service.
        
        Args:
            agent: The agent to serve.
            config: Agent configuration.
            service_config: Service configuration.
        """
        self._agent = agent
        self._config = config or Config()
        self._service_config = service_config or ServiceConfig()
        self._session_manager = SessionManager()
        self._request_count = 0
        self._error_count = 0
    
    def run_task(
        self,
        task: TaskSpec,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a task.
        
        Args:
            task: The task to run.
            session_id: Optional session ID.
            
        Returns:
            Result dictionary.
        """
        self._request_count += 1
        
        # Get or create session
        if session_id:
            session = self._session_manager.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}",
                }
        else:
            session = self._session_manager.create_session("agent")
            session_id = session.id
        
        try:
            # Run agent
            result = self._agent.run(task)
            
            # Update session
            session.update_state("last_task", task.goal)
            session.update_state("last_result", result.output)
            
            return {
                "success": result.success,
                "output": result.output,
                "termination_reason": result.termination_reason,
                "total_steps": result.total_steps,
                "session_id": session_id,
            }
        except Exception as e:
            self._error_count += 1
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
            }
    
    def get_status(self) -> dict[str, Any]:
        """Get service status.
        
        Returns:
            Status dictionary.
        """
        return {
            "status": "running",
            "request_count": self._request_count,
            "error_count": self._error_count,
            "active_sessions": len(self._session_manager.list_sessions(active_only=True)),
            "config": self._config.to_dict(),
        }
    
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session information.
        
        Args:
            session_id: The session ID.
            
        Returns:
            Session dictionary, or None if not found.
        """
        session = self._session_manager.get_session(session_id)
        if session:
            return session.to_dict()
        return None
    
    def list_sessions(self, active_only: bool = True) -> list[dict[str, Any]]:
        """List sessions.
        
        Args:
            active_only: Whether to only return active sessions.
            
        Returns:
            List of session dictionaries.
        """
        sessions = self._session_manager.list_sessions(active_only=active_only)
        return [s.to_dict() for s in sessions]
    
    def close_session(self, session_id: str) -> bool:
        """Close a session.
        
        Args:
            session_id: The session ID.
            
        Returns:
            True if closed, False if not found.
        """
        return self._session_manager.close_session(session_id)
    
    def start(self) -> None:
        """Start the service (placeholder for actual server start)."""
        # In a real implementation, this would start a FastAPI/Flask server
        pass
    
    def stop(self) -> None:
        """Stop the service."""
        # Clean up sessions
        self._session_manager.cleanup_expired(max_age_seconds=0)
