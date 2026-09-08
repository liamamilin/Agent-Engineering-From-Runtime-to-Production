"""Handoff pattern for control transfer between agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_course.core import AgentState, TaskSpec
from agent_course.runtime import Agent


class HandoffDecision(str, Enum):
    """Decision types for handoff."""
    
    CONTINUE = "continue"  # Current agent continues
    HANDOFF = "handoff"  # Transfer to another agent
    ESCALATE = "escalate"  # Escalate to supervisor
    COMPLETE = "complete"  # Task is complete


@dataclass
class Handoff:
    """Represents a handoff decision and context.
    
    Handoff is used when one agent determines that another agent
    is better suited to handle the current task or subtask.
    """
    
    from_agent: str
    to_agent: str
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    state_snapshot: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "reason": self.reason,
            "context": self.context,
            "state_snapshot": self.state_snapshot,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Handoff:
        """Create from dictionary."""
        return cls(**data)


class HandoffPolicy:
    """Policy for determining when to handoff control."""
    
    def __init__(
        self,
        max_steps_per_agent: int = 10,
        confidence_threshold: float = 0.7,
    ) -> None:
        """Initialize handoff policy.
        
        Args:
            max_steps_per_agent: Maximum steps before considering handoff.
            confidence_threshold: Confidence threshold for continuing.
        """
        self.max_steps_per_agent = max_steps_per_agent
        self.confidence_threshold = confidence_threshold
    
    def should_handoff(
        self,
        current_agent: str,
        state: AgentState,
        available_agents: list[str],
    ) -> HandoffDecision:
        """Determine if handoff should occur.
        
        Args:
            current_agent: ID of current agent.
            state: Current agent state.
            available_agents: List of available agents to handoff to.
            
        Returns:
            HandoffDecision indicating what to do.
        """
        # Check if task is complete
        if state.status == "completed":
            return HandoffDecision.COMPLETE
        
        # Check if max steps reached
        if state.step_count >= self.max_steps_per_agent:
            # Find another agent to handoff to
            other_agents = [a for a in available_agents if a != current_agent]
            if other_agents:
                return HandoffDecision.HANDOFF
            else:
                return HandoffDecision.ESCALATE
        
        # Default: continue
        return HandoffDecision.CONTINUE
    
    def select_target_agent(
        self,
        current_agent: str,
        available_agents: list[str],
        task: TaskSpec,
    ) -> str | None:
        """Select the best agent to handoff to.
        
        Args:
            current_agent: ID of current agent.
            available_agents: List of available agents.
            task: The task to be handled.
            
        Returns:
            ID of selected agent, or None if no suitable agent.
        """
        # Simple heuristic: select first available agent that's not current
        for agent in available_agents:
            if agent != current_agent:
                return agent
        return None


class HandoffManager:
    """Manages handoffs between agents."""
    
    def __init__(self, agents: dict[str, Agent], policy: HandoffPolicy | None = None) -> None:
        """Initialize handoff manager.
        
        Args:
            agents: Dictionary of agent ID to Agent instance.
            policy: Handoff policy. If None, uses default.
        """
        self.agents = agents
        self.policy = policy or HandoffPolicy()
        self.handoff_history: list[Handoff] = []
    
    def execute_with_handoff(
        self,
        initial_agent_id: str,
        task: TaskSpec,
    ) -> dict[str, Any]:
        """Execute task with potential handoffs.
        
        Args:
            initial_agent_id: ID of initial agent.
            task: The task to execute.
            
        Returns:
            Dictionary with result and handoff history.
        """
        current_agent_id = initial_agent_id
        state = AgentState(task=task)
        
        while True:
            agent = self.agents[current_agent_id]
            
            # Run agent for a few steps
            result = agent.run(task)
            
            # Check if should handoff
            decision = self.policy.should_handoff(
                current_agent_id,
                state,
                list(self.agents.keys()),
            )
            
            if decision == HandoffDecision.COMPLETE:
                return {
                    "result": result.output,
                    "success": result.success,
                    "final_agent": current_agent_id,
                    "handoffs": self.handoff_history,
                }
            
            if decision == HandoffDecision.HANDOFF:
                target_agent = self.policy.select_target_agent(
                    current_agent_id,
                    list(self.agents.keys()),
                    task,
                )
                
                if target_agent:
                    handoff = Handoff(
                        from_agent=current_agent_id,
                        to_agent=target_agent,
                        reason=f"Max steps reached ({state.step_count})",
                        context={"task": task.goal},
                    )
                    self.handoff_history.append(handoff)
                    current_agent_id = target_agent
                    continue
            
            if decision == HandoffDecision.ESCALATE:
                return {
                    "result": None,
                    "success": False,
                    "final_agent": current_agent_id,
                    "handoffs": self.handoff_history,
                    "escalated": True,
                }
            
            # Continue with current agent
            if result.success:
                return {
                    "result": result.output,
                    "success": True,
                    "final_agent": current_agent_id,
                    "handoffs": self.handoff_history,
                }
            
            # If failed and no handoff, return failure
            return {
                "result": result.output,
                "success": False,
                "final_agent": current_agent_id,
                "handoffs": self.handoff_history,
            }
