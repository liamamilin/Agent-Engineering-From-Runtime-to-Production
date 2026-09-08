"""Composition module for multi-agent patterns."""

from agent_course.composition.agent_tool import AgentAsTool
from agent_course.composition.handoff import Handoff, HandoffDecision
from agent_course.composition.supervisor import Supervisor, Worker, TaskDelegation
from agent_course.composition.message import AgentMessage, MessageBus

__all__ = [
    "AgentAsTool",
    "Handoff",
    "HandoffDecision",
    "Supervisor",
    "Worker",
    "TaskDelegation",
    "AgentMessage",
    "MessageBus",
]
