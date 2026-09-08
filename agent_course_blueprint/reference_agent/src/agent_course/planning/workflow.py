"""Workflow/state machine for deterministic control architectures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class WorkflowState(str, Enum):
    """Predefined workflow states."""
    
    INITIAL = "initial"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowTransition:
    """A transition in a workflow."""
    
    from_state: str
    to_state: str
    action: str  # Action to execute during transition
    condition: Callable[[dict[str, Any]], bool] | None = None  # Condition for transition
    arguments: dict[str, Any] = field(default_factory=dict)
    
    def can_transition(self, context: dict[str, Any]) -> bool:
        """Check if transition can occur given context."""
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class Workflow:
    """A deterministic workflow/state machine."""
    
    id: str
    name: str
    initial_state: str = WorkflowState.INITIAL.value
    current_state: str = WorkflowState.INITIAL.value
    transitions: list[WorkflowTransition] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    
    def add_transition(self, transition: WorkflowTransition) -> None:
        """Add a transition to the workflow."""
        self.transitions.append(transition)
    
    def get_available_transitions(self) -> list[WorkflowTransition]:
        """Get all transitions available from current state."""
        return [
            t for t in self.transitions
            if t.from_state == self.current_state and t.can_transition(self.context)
        ]
    
    def execute_transition(self, transition_id: int) -> dict[str, Any]:
        """Execute a transition by index.
        
        Args:
            transition_id: Index of the transition in available transitions.
        
        Returns:
            Result of the transition.
        
        Raises:
            ValueError: If transition_id is invalid.
        """
        available = self.get_available_transitions()
        if transition_id >= len(available):
            raise ValueError(f"Invalid transition_id: {transition_id}")
        
        transition = available[transition_id]
        
        # Record history
        self.history.append({
            "from_state": self.current_state,
            "to_state": transition.to_state,
            "action": transition.action,
            "arguments": transition.arguments,
        })
        
        # Update state
        self.current_state = transition.to_state
        
        # Return transition info
        return {
            "action": transition.action,
            "arguments": transition.arguments,
            "new_state": self.current_state,
        }
    
    def is_completed(self) -> bool:
        """Check if workflow is in completed state."""
        return self.current_state == WorkflowState.COMPLETED.value
    
    def is_failed(self) -> bool:
        """Check if workflow is in failed state."""
        return self.current_state == WorkflowState.FAILED.value
    
    def is_waiting_approval(self) -> bool:
        """Check if workflow is waiting for approval."""
        return self.current_state == WorkflowState.WAITING_APPROVAL.value
    
    def update_context(self, key: str, value: Any) -> None:
        """Update workflow context."""
        self.context[key] = value
    
    def get_execution_trace(self) -> list[dict[str, Any]]:
        """Get the execution trace."""
        return self.history.copy()


def create_simple_workflow(workflow_id: str, name: str) -> Workflow:
    """Create a simple linear workflow for testing.
    
    Workflow: initial -> running -> completed
    
    Args:
        workflow_id: Unique identifier.
        name: Workflow name.
    
    Returns:
        A simple Workflow object.
    """
    workflow = Workflow(id=workflow_id, name=name)
    
    # initial -> running
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.INITIAL.value,
        to_state=WorkflowState.RUNNING.value,
        action="start_task",
    ))
    
    # running -> completed
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.RUNNING.value,
        to_state=WorkflowState.COMPLETED.value,
        action="finish_task",
    ))
    
    return workflow


def create_approval_workflow(workflow_id: str, name: str) -> Workflow:
    """Create a workflow with approval checkpoint.
    
    Workflow: initial -> running -> waiting_approval -> completed
    
    Args:
        workflow_id: Unique identifier.
        name: Workflow name.
    
    Returns:
        A Workflow object with approval step.
    """
    workflow = Workflow(id=workflow_id, name=name)
    
    # initial -> running
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.INITIAL.value,
        to_state=WorkflowState.RUNNING.value,
        action="start_task",
    ))
    
    # running -> waiting_approval
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.RUNNING.value,
        to_state=WorkflowState.WAITING_APPROVAL.value,
        action="request_approval",
    ))
    
    # waiting_approval -> completed (after approval)
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.WAITING_APPROVAL.value,
        to_state=WorkflowState.COMPLETED.value,
        action="execute_approved_action",
        condition=lambda ctx: ctx.get("approved", False),
    ))
    
    # waiting_approval -> failed (if rejected)
    workflow.add_transition(WorkflowTransition(
        from_state=WorkflowState.WAITING_APPROVAL.value,
        to_state=WorkflowState.FAILED.value,
        action="handle_rejection",
        condition=lambda ctx: ctx.get("rejected", False),
    ))
    
    return workflow
