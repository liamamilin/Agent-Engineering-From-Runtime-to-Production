"""Session management for agent systems."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Session:
    """A session for an agent interaction."""
    
    id: str
    agent_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state,
            "metadata": self.metadata,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Create session from dictionary."""
        return cls(**data)
    
    def update_state(self, key: str, value: Any) -> None:
        """Update session state."""
        self.state[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get session state value."""
        return self.state.get(key, default)
    
    def close(self) -> None:
        """Close the session."""
        self.is_active = False
        self.updated_at = datetime.now().isoformat()


class SessionManager:
    """Manages sessions for agent interactions."""
    
    def __init__(self) -> None:
        """Initialize session manager."""
        self._sessions: dict[str, Session] = {}
    
    def create_session(self, agent_id: str, metadata: dict[str, Any] | None = None) -> Session:
        """Create a new session.
        
        Args:
            agent_id: The agent ID.
            metadata: Optional metadata.
            
        Returns:
            Created session.
        """
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.
        
        Args:
            session_id: The session ID.
            
        Returns:
            The session, or None if not found.
        """
        return self._sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close a session.
        
        Args:
            session_id: The session ID.
            
        Returns:
            True if closed, False if not found.
        """
        session = self._sessions.get(session_id)
        if session:
            session.close()
            return True
        return False
    
    def list_sessions(self, agent_id: str | None = None, active_only: bool = True) -> list[Session]:
        """List sessions.
        
        Args:
            agent_id: Optional agent ID filter.
            active_only: Whether to only return active sessions.
            
        Returns:
            List of sessions.
        """
        sessions = list(self._sessions.values())
        
        if agent_id:
            sessions = [s for s in sessions if s.agent_id == agent_id]
        
        if active_only:
            sessions = [s for s in sessions if s.is_active]
        
        return sessions
    
    def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """Clean up expired sessions.
        
        Args:
            max_age_seconds: Maximum age in seconds.
            
        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.now()
        expired = []
        
        for session_id, session in self._sessions.items():
            created = datetime.fromisoformat(session.created_at)
            age = (now - created).total_seconds()
            
            if age > max_age_seconds:
                expired.append(session_id)
        
        for session_id in expired:
            del self._sessions[session_id]
        
        return len(expired)
