"""Planner for creating and replanning plans."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from agent_course.planning.plan import Plan, PlanStep, PlanStatus


class ReplanningTrigger(str, Enum):
    """Triggers for replanning."""
    
    STEP_FAILURE = "step_failure"  # A step failed
    UNEXPECTED_RESULT = "unexpected_result"  # Result doesn't match expectations
    NEW_INFORMATION = "new_information"  # New info invalidates plan
    PROGRESS_STALL = "progress_stall"  # No progress after N steps
    MANUAL = "manual"  # Manual trigger


@dataclass
class Planner:
    """Creates and manages plans for task execution."""
    
    def create_plan(
        self,
        plan_id: str,
        goal: str,
        steps_spec: list[dict[str, Any]],
    ) -> Plan:
        """Create a plan from a step specification.
        
        Args:
            plan_id: Unique identifier for the plan.
            goal: The goal this plan achieves.
            steps_spec: List of step specifications, each containing:
                - id: Step ID
                - description: Step description
                - action: Action/tool to execute
                - arguments: Action arguments
                - requires_approval: Whether step needs approval
                - dependencies: List of step IDs this depends on
        
        Returns:
            A new Plan object.
        """
        plan = Plan(id=plan_id, goal=goal)
        
        for spec in steps_spec:
            step = PlanStep(
                id=spec["id"],
                description=spec["description"],
                action=spec["action"],
                arguments=spec.get("arguments", {}),
                requires_approval=spec.get("requires_approval", False),
                dependencies=spec.get("dependencies", []),
            )
            plan.add_step(step)
        
        return plan
    
    def replan(
        self,
        original_plan: Plan,
        trigger: ReplanningTrigger,
        reason: str,
        completed_steps: set[str],
    ) -> Plan:
        """Create a new plan based on the original plan and current state.
        
        This is a simple replanning strategy that:
        1. Keeps completed steps
        2. Removes failed steps
        3. Adjusts remaining steps based on the trigger
        
        Args:
            original_plan: The original plan.
            trigger: What triggered replanning.
            reason: Human-readable reason for replanning.
            completed_steps: Set of step IDs that are completed.
        
        Returns:
            A new Plan object.
        """
        # Create new plan with same goal
        new_plan = Plan(
            id=f"{original_plan.id}_replan",
            goal=original_plan.goal,
            metadata={
                "replanned_from": original_plan.id,
                "trigger": trigger.value,
                "reason": reason,
            },
        )
        
        # Copy completed steps
        for step in original_plan.steps:
            if step.id in completed_steps:
                new_step = PlanStep(
                    id=step.id,
                    description=step.description,
                    action=step.action,
                    arguments=step.arguments,
                    status=PlanStatus.COMPLETED,
                    result=step.result,
                    requires_approval=step.requires_approval,
                    dependencies=step.dependencies,
                )
                new_plan.add_step(new_step)
        
        # Add remaining pending steps (skip failed ones)
        for step in original_plan.steps:
            if step.id not in completed_steps and step.status != PlanStatus.FAILED:
                new_step = PlanStep(
                    id=step.id,
                    description=step.description,
                    action=step.action,
                    arguments=step.arguments,
                    requires_approval=step.requires_approval,
                    dependencies=[d for d in step.dependencies if d in completed_steps or d in [s.id for s in original_plan.steps if s.status != PlanStatus.FAILED]],
                )
                new_plan.add_step(new_step)
        
        return new_plan
    
    def should_replan(
        self,
        plan: Plan,
        step_results: dict[str, Any],
    ) -> tuple[bool, ReplanningTrigger | None, str | None]:
        """Determine if replanning is needed.
        
        Args:
            plan: Current plan.
            step_results: Results from executed steps.
        
        Returns:
            Tuple of (should_replan, trigger, reason).
        """
        # Check for failed steps
        for step in plan.steps:
            if step.status == PlanStatus.FAILED:
                return True, ReplanningTrigger.STEP_FAILURE, f"Step {step.id} failed: {step.error}"
        
        # Check for unexpected results (simple heuristic)
        for step_id, result in step_results.items():
            if isinstance(result, dict) and result.get("unexpected"):
                return True, ReplanningTrigger.UNEXPECTED_RESULT, f"Step {step_id} produced unexpected result"
        
        return False, None, None
