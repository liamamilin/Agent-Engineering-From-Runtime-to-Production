"""Tests for planning, workflows, and human control module."""

import pytest

from agent_course.planning import (
    Plan,
    PlanStep,
    PlanStatus,
    Planner,
    ReplanningTrigger,
    Workflow,
    WorkflowState,
    WorkflowTransition,
    ApprovalCheckpoint,
    ApprovalStatus,
    HumanApprovalPolicy,
)
from agent_course.planning.approval import ApprovalManager
from agent_course.planning.workflow import create_simple_workflow, create_approval_workflow


class TestPlanStep:
    """Tests for PlanStep."""
    
    def test_step_creation(self):
        """Test creating a plan step."""
        step = PlanStep(
            id="step1",
            description="First step",
            action="search",
            arguments={"query": "test"},
        )
        assert step.id == "step1"
        assert step.status == PlanStatus.PENDING
    
    def test_step_status_transitions(self):
        """Test step status transitions."""
        step = PlanStep(id="step1", description="Test", action="test")
        
        step.mark_in_progress()
        assert step.status == PlanStatus.IN_PROGRESS
        
        step.mark_completed(result="done")
        assert step.status == PlanStatus.COMPLETED
        assert step.result == "done"
    
    def test_step_dependencies(self):
        """Test step dependency checking."""
        step = PlanStep(
            id="step2",
            description="Dependent step",
            action="test",
            dependencies=["step1"],
        )
        
        # Not ready if dependency not completed
        assert not step.is_ready(set())
        assert not step.is_ready({"step0"})
        
        # Ready if dependency completed
        assert step.is_ready({"step1"})


class TestPlan:
    """Tests for Plan."""
    
    def test_plan_creation(self):
        """Test creating a plan."""
        plan = Plan(id="plan1", goal="Test goal")
        assert plan.id == "plan1"
        assert plan.goal == "Test goal"
        assert plan.status == PlanStatus.PENDING
    
    def test_add_steps(self):
        """Test adding steps to a plan."""
        plan = Plan(id="plan1", goal="Test")
        plan.add_step(PlanStep(id="step1", description="Step 1", action="test"))
        plan.add_step(PlanStep(id="step2", description="Step 2", action="test"))
        
        assert len(plan.steps) == 2
        assert plan.get_step("step1") is not None
    
    def test_get_next_step(self):
        """Test getting the next ready step."""
        plan = Plan(id="plan1", goal="Test")
        plan.add_step(PlanStep(id="step1", description="Step 1", action="test"))
        plan.add_step(PlanStep(id="step2", description="Step 2", action="test", dependencies=["step1"]))
        
        # First step should be ready
        next_step = plan.get_next_step(set())
        assert next_step is not None
        assert next_step.id == "step1"
        
        # Mark step1 as completed
        plan.steps[0].mark_completed()
        
        # After completing step1, step2 should be ready
        next_step = plan.get_next_step({"step1"})
        assert next_step is not None
        assert next_step.id == "step2"
    
    def test_plan_progress(self):
        """Test plan progress calculation."""
        plan = Plan(id="plan1", goal="Test")
        plan.add_step(PlanStep(id="step1", description="Step 1", action="test"))
        plan.add_step(PlanStep(id="step2", description="Step 2", action="test"))
        
        assert plan.progress() == 0.0
        
        plan.steps[0].mark_completed()
        assert plan.progress() == 0.5
        
        plan.steps[1].mark_completed()
        assert plan.progress() == 1.0


class TestPlanner:
    """Tests for Planner."""
    
    def test_create_plan(self):
        """Test creating a plan from specification."""
        planner = Planner()
        
        steps_spec = [
            {"id": "step1", "description": "Search", "action": "search", "arguments": {"query": "test"}},
            {"id": "step2", "description": "Process", "action": "process", "dependencies": ["step1"]},
        ]
        
        plan = planner.create_plan("plan1", "Test goal", steps_spec)
        
        assert plan.id == "plan1"
        assert len(plan.steps) == 2
        assert plan.steps[1].dependencies == ["step1"]
    
    def test_replan(self):
        """Test replanning after failure."""
        planner = Planner()
        
        # Create original plan
        steps_spec = [
            {"id": "step1", "description": "Step 1", "action": "test1"},
            {"id": "step2", "description": "Step 2", "action": "test2"},
            {"id": "step3", "description": "Step 3", "action": "test3"},
        ]
        original = planner.create_plan("plan1", "Test", steps_spec)
        
        # Simulate step1 completed, step2 failed
        original.steps[0].mark_completed(result="done")
        original.steps[1].mark_failed(error="Failed")
        
        # Replan
        new_plan = planner.replan(
            original,
            ReplanningTrigger.STEP_FAILURE,
            "Step 2 failed",
            {"step1"},
        )
        
        # New plan should have step1 completed, step3 pending
        assert len(new_plan.steps) == 2
        assert new_plan.steps[0].status == PlanStatus.COMPLETED
        assert new_plan.steps[1].id == "step3"


class TestWorkflow:
    """Tests for Workflow."""
    
    def test_simple_workflow(self):
        """Test simple linear workflow."""
        workflow = create_simple_workflow("wf1", "Simple Workflow")
        
        assert workflow.current_state == WorkflowState.INITIAL.value
        
        # initial -> running
        result = workflow.execute_transition(0)
        assert result["new_state"] == WorkflowState.RUNNING.value
        
        # running -> completed
        result = workflow.execute_transition(0)
        assert result["new_state"] == WorkflowState.COMPLETED.value
        assert workflow.is_completed()
    
    def test_approval_workflow(self):
        """Test workflow with approval checkpoint."""
        workflow = create_approval_workflow("wf2", "Approval Workflow")
        
        # initial -> running
        workflow.execute_transition(0)
        assert workflow.current_state == WorkflowState.RUNNING.value
        
        # running -> waiting_approval
        workflow.execute_transition(0)
        assert workflow.is_waiting_approval()
        
        # Cannot proceed without approval
        available = workflow.get_available_transitions()
        assert len(available) == 0  # No transitions available without approval
        
        # Set approval in context
        workflow.update_context("approved", True)
        available = workflow.get_available_transitions()
        assert len(available) == 1
        
        # waiting_approval -> completed
        workflow.execute_transition(0)
        assert workflow.is_completed()
    
    def test_workflow_history(self):
        """Test workflow execution history."""
        workflow = create_simple_workflow("wf1", "Test")
        
        workflow.execute_transition(0)
        workflow.execute_transition(0)
        
        trace = workflow.get_execution_trace()
        assert len(trace) == 2
        assert trace[0]["from_state"] == WorkflowState.INITIAL.value
        assert trace[1]["to_state"] == WorkflowState.COMPLETED.value


class TestApprovalCheckpoint:
    """Tests for ApprovalCheckpoint."""
    
    def test_checkpoint_creation(self):
        """Test creating an approval checkpoint."""
        checkpoint = ApprovalCheckpoint(
            id="cp1",
            action="delete_file",
            arguments={"path": "/tmp/test.txt"},
            reason="Destructive action",
        )
        assert checkpoint.status == ApprovalStatus.PENDING
        assert checkpoint.is_pending()
    
    def test_checkpoint_approval(self):
        """Test approving a checkpoint."""
        checkpoint = ApprovalCheckpoint(
            id="cp1",
            action="test",
            arguments={},
            reason="Test",
        )
        
        checkpoint.approve(approved_by="user", notes="Looks good")
        
        assert checkpoint.is_approved()
        assert checkpoint.resolved_by == "user"
        assert checkpoint.notes == "Looks good"
    
    def test_checkpoint_rejection(self):
        """Test rejecting a checkpoint."""
        checkpoint = ApprovalCheckpoint(
            id="cp1",
            action="test",
            arguments={},
            reason="Test",
        )
        
        checkpoint.reject(rejected_by="user", notes="Too risky")
        
        assert checkpoint.is_rejected()
        assert checkpoint.notes == "Too risky"


class TestHumanApprovalPolicy:
    """Tests for HumanApprovalPolicy."""
    
    def test_requires_approval(self):
        """Test approval requirement logic."""
        policy = HumanApprovalPolicy(
            require_approval_for=["delete_file", "send_email"],
            auto_approve_safe=True,
        )
        
        # Explicitly required
        assert policy.requires_approval("delete_file", {})
        assert policy.requires_approval("send_email", {})
        
        # Safe actions auto-approved
        assert not policy.requires_approval("read_file", {})
        assert not policy.requires_approval("search", {})
        
        # Unknown actions require approval
        assert policy.requires_approval("unknown_action", {})
    
    def test_create_checkpoint(self):
        """Test creating checkpoint from policy."""
        policy = HumanApprovalPolicy()
        
        checkpoint = policy.create_checkpoint(
            "cp1",
            "delete_file",
            {"path": "/tmp/test.txt"},
            "Destructive action",
        )
        
        assert checkpoint.id == "cp1"
        assert checkpoint.action == "delete_file"
        assert checkpoint.is_pending()


class TestApprovalManager:
    """Tests for ApprovalManager."""
    
    def test_request_and_approve(self):
        """Test requesting and approving a checkpoint."""
        manager = ApprovalManager()
        
        checkpoint = manager.request_approval(
            "cp1",
            "delete_file",
            {"path": "/tmp/test.txt"},
            "Destructive",
        )
        
        assert checkpoint.is_pending()
        
        # Approve
        result = manager.approve("cp1", approved_by="admin")
        assert result is True
        assert checkpoint.is_approved()
    
    def test_request_and_reject(self):
        """Test requesting and rejecting a checkpoint."""
        manager = ApprovalManager()
        
        checkpoint = manager.request_approval(
            "cp1",
            "send_email",
            {"to": "test@example.com"},
            "External communication",
        )
        
        # Reject
        result = manager.reject("cp1", rejected_by="admin", notes="Not appropriate")
        assert result is True
        assert checkpoint.is_rejected()
    
    def test_get_pending_checkpoints(self):
        """Test getting pending checkpoints."""
        manager = ApprovalManager()
        
        manager.request_approval("cp1", "action1", {}, "Reason 1")
        manager.request_approval("cp2", "action2", {}, "Reason 2")
        
        pending = manager.get_pending_checkpoints()
        assert len(pending) == 2
        
        # Approve one
        manager.approve("cp1")
        
        pending = manager.get_pending_checkpoints()
        assert len(pending) == 1
        assert pending[0].id == "cp2"
