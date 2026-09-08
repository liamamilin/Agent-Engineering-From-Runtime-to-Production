"""Message passing for inter-agent communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Types of messages between agents."""
    
    TASK = "task"  # Task delegation
    RESULT = "result"  # Task result
    QUERY = "query"  # Information query
    RESPONSE = "response"  # Query response
    HANDOFF = "handoff"  # Control handoff
    BROADCAST = "broadcast"  # Broadcast to all


@dataclass
class AgentMessage:
    """Structured message for agent communication."""
    
    id: str
    sender: str
    receiver: str
    message_type: MessageType
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reply_to: str | None = None  # ID of message this is replying to
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        """Create from dictionary."""
        data = data.copy()
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)
    
    @classmethod
    def create_task(cls, task_id: str, sender: str, receiver: str, 
                    task_description: str, context: dict[str, Any]) -> AgentMessage:
        """Create a task delegation message."""
        return cls(
            id=f"msg_{task_id}",
            sender=sender,
            receiver=receiver,
            message_type=MessageType.TASK,
            payload={
                "task_id": task_id,
                "description": task_description,
                "context": context,
            },
        )
    
    @classmethod
    def create_result(cls, task_id: str, sender: str, receiver: str,
                      result: Any, success: bool = True) -> AgentMessage:
        """Create a task result message."""
        return cls(
            id=f"result_{task_id}",
            sender=sender,
            receiver=receiver,
            message_type=MessageType.RESULT,
            payload={
                "task_id": task_id,
                "result": result,
                "success": success,
            },
            reply_to=f"msg_{task_id}",
        )


class MessageBus:
    """Message bus for routing messages between agents."""
    
    def __init__(self) -> None:
        """Initialize message bus."""
        self._queues: dict[str, list[AgentMessage]] = {}
        self._history: list[AgentMessage] = []
    
    def send(self, message: AgentMessage) -> None:
        """Send a message to an agent.
        
        Args:
            message: The message to send.
        """
        if message.receiver not in self._queues:
            self._queues[message.receiver] = []
        
        self._queues[message.receiver].append(message)
        self._history.append(message)
    
    def receive(self, agent_id: str) -> AgentMessage | None:
        """Receive next message for an agent.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            The next message, or None if queue is empty.
        """
        if agent_id not in self._queues:
            return None
        
        if not self._queues[agent_id]:
            return None
        
        return self._queues[agent_id].pop(0)
    
    def peek(self, agent_id: str) -> AgentMessage | None:
        """Peek at next message without removing it.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            The next message, or None if queue is empty.
        """
        if agent_id not in self._queues:
            return None
        
        if not self._queues[agent_id]:
            return None
        
        return self._queues[agent_id][0]
    
    def has_messages(self, agent_id: str) -> bool:
        """Check if agent has pending messages.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            True if has messages, False otherwise.
        """
        return (agent_id in self._queues and 
                len(self._queues[agent_id]) > 0)
    
    def get_history(self, agent_id: str | None = None) -> list[AgentMessage]:
        """Get message history.
        
        Args:
            agent_id: Optional agent ID to filter by sender or receiver.
            
        Returns:
            List of messages.
        """
        if agent_id is None:
            return self._history.copy()
        
        return [
            msg for msg in self._history
            if msg.sender == agent_id or msg.receiver == agent_id
        ]
    
    def clear(self, agent_id: str | None = None) -> None:
        """Clear message queues.
        
        Args:
            agent_id: Optional agent ID to clear specific queue.
        """
        if agent_id is None:
            self._queues.clear()
        elif agent_id in self._queues:
            self._queues[agent_id].clear()
