"""Lab tests for M8 Planning, Workflows & Human Control."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.planning import (
    Plan,
    PlanStep,
    PlanStatus,
    Planner,
    ReplanningTrigger,
    Workflow,
    WorkflowState,
    ApprovalCheckpoint,
    ApprovalStatus,
    HumanApprovalPolicy,
)
from agent_course.planning.approval import ApprovalManager
from agent_course.planning.workflow import create_simple_workflow, create_approval_workflow


def test_plan_creation_and_execution():
    """Test creating and executing a plan."""
    planner = Planner()
    
    # Create a plan
    steps_spec = [
        {"id": "step1", "description": "Search", "action": "search", "arguments": {"query": "test"}},
        {"id": "step2", "description": "Process", "action": "process", "dependencies": ["step1"]},
        {"id": "step3", "description": "Write", "action": "write", "dependencies": ["step2"]},
    ]
    
    plan = planner.create_plan("plan1", "Research task", steps_spec)
    
    # Verify plan structure
    assert plan.id == "plan1"
    assert len(plan.steps) == 3
    assert plan.steps[1].dependencies == ["step1"]
    
    # Execute steps in order
    completed = set()
    
    # Step 1 should be ready
    next_step = plan.get_next_step(completed)
    assert next_step is not None
    assert next_step.id == "step1"
    
    # Complete step 1
    next_step.mark_completed(result="search results")
    completed.add("step1")
    
    # Step 2 should be ready now
    next_step = plan.get_next_step(completed)
    assert next_step is not None
    assert next_step.id == "step2"


def test_reactive_vs_planning_comparison():
    """Test that same task can run under both architectures."""
    # Reactive loop: dynamic decisions
    reactive_trace = []
    for i in range(3):
        reactive_trace.append({"step": i, "decision": "dynamic"})
    
    # Explicit planning: predefined steps
    planner = Planner()
    plan = planner.create_plan(
        "plan1",
        "Test task",
        [
            {"id": "s1", "description": "Step 1", "action": "action1"},
            {"id": "s2", "description": "Step 2", "action": "action2"},
            {"id": "s3", "description": "Step 3", "action": "action3"},
        ],
    )
    
    planning_trace = []
    completed = set()
    while not plan.is_completed():
        next_step = plan.get_next_step(completed)
        if next_step is None:
            break
        planning_trace.append({"step": next_step.id, "decision": "predefined"})
        next_step.mark_completed()
        completed.add(next_step.id)
    
    # Both should have 3 steps
    assert len(reactive_trace) == 3
    assert len(planning_trace) == 3
    
    # Planning trace should have predefined steps
    assert all(t["decision"] == "predefined" for t in planning_trace)


def test_workflow_with_approval():
    """Test workflow with approval checkpoint."""
    workflow = create_approval_workflow("wf1", "Approval Workflow")
    
    # initial -> running
    result = workflow.execute_transition(0)
    assert result["new_state"] == WorkflowState.RUNNING.value
    
    # running -> waiting_approval
    result = workflow.execute_transition(0)
    assert workflow.is_waiting_approval()
    
    # Cannot proceed without approval
    available = workflow.get_available_transitions()
    assert len(available) == 0
    
    # Simulate approval
    workflow.update_context("approved", True)
    available = workflow.get_available_transitions()
    assert len(available) == 1
    
    # waiting_approval -> completed
    result = workflow.execute_transition(0)
    assert workflow.is_completed()


def test_approval_manager_pause_resume():
    """Test that approval can pause and resume execution."""
    manager = ApprovalManager()
    
    # Request approval for a destructive action
    checkpoint = manager.request_approval(
        "cp1",
        "delete_file",
        {"path": "/important/data.txt"},
        "Destructive action requires approval",
    )
    
    assert checkpoint.is_pending()
    
    # Execution should pause here
    pending = manager.get_pending_checkpoints()
    assert len(pending) == 1
    
    # Simulate human approval
    manager.approve("cp1", approved_by="admin", notes="Approved after review")
    
    assert checkpoint.is_approved()
    assert checkpoint.resolved_by == "admin"
    assert checkpoint.notes == "Approved after review"
    
    # No more pending checkpoints
    pending = manager.get_pending_checkpoints()
    assert len(pending) == 0


def test_replanning_after_failure():
    """Test replanning when a step fails."""
    planner = Planner()
    
    # Create original plan
    steps_spec = [
        {"id": "step1", "description": "Step 1", "action": "action1"},
        {"id": "step2", "description": "Step 2", "action": "action2"},
        {"id": "step3", "description": "Step 3", "action": "action3"},
    ]
    original_plan = planner.create_plan("plan1", "Test", steps_spec)
    
    # Simulate execution: step1 completed, step2 failed
    original_plan.steps[0].mark_completed(result="done")
    original_plan.steps[1].mark_failed(error="Action failed")
    
    # Check if replanning is needed
    should_replan, trigger, reason = planner.should_replan(
        original_plan,
        {"step1": "done", "step2": {"error": "Action failed"}},
    )
    
    assert should_replan is True
    assert trigger == ReplanningTrigger.STEP_FAILURE
    
    # Replan
    new_plan = planner.replan(
        original_plan,
        trigger,
        reason,
        original_plan.get_completed_steps(),
    )
    
    # New plan should have step1 completed and step3 pending
    assert len(new_plan.steps) == 2
    assert new_plan.steps[0].status == PlanStatus.COMPLETED
    assert new_plan.steps[1].id == "step3"
    assert new_plan.steps[1].status == PlanStatus.PENDING


def test_workflow_execution_trace():
    """Test that workflow execution creates a trace."""
    workflow = create_simple_workflow("wf1", "Simple Workflow")
    
    # Execute workflow
    workflow.execute_transition(0)  # initial -> running
    workflow.execute_transition(0)  # running -> completed
    
    # Check trace
    trace = workflow.get_execution_trace()
    assert len(trace) == 2
    assert trace[0]["from_state"] == WorkflowState.INITIAL.value
    assert trace[0]["to_state"] == WorkflowState.RUNNING.value
    assert trace[1]["from_state"] == WorkflowState.RUNNING.value
    assert trace[1]["to_state"] == WorkflowState.COMPLETED.value


def test_approval_rejection():
    """Test that approval rejection is handled correctly."""
    manager = ApprovalManager()
    
    checkpoint = manager.request_approval(
        "cp1",
        "send_email",
        {"to": "test@example.com"},
        "External communication",
    )
    
    assert checkpoint.is_pending()
    
    # Reject approval
    manager.reject("cp1", rejected_by="admin", notes="Not appropriate")
    
    assert checkpoint.is_rejected()
    assert checkpoint.notes == "Not appropriate"
