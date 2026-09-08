"""Supervisor/Worker pattern for multi-agent coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.core import TaskSpec, AgentState
from agent_course.runtime import Agent


@dataclass
class TaskDelegation:
    """Represents a task delegation from supervisor to worker."""
    
    task_id: str
    task_description: str
    assigned_worker: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "assigned_worker": self.assigned_worker,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class Worker:
    """A specialized worker agent."""
    
    def __init__(
        self,
        worker_id: str,
        agent: Agent,
        capabilities: list[str],
    ) -> None:
        """Initialize worker.
        
        Args:
            worker_id: Unique identifier for this worker.
            agent: The underlying agent.
            capabilities: List of capabilities this worker has.
        """
        self.worker_id = worker_id
        self.agent = agent
        self.capabilities = capabilities
        self.tasks_completed = 0
        self.tasks_failed = 0
    
    def execute_task(self, task: TaskSpec) -> dict[str, Any]:
        """Execute a task.
        
        Args:
            task: The task to execute.
            
        Returns:
            Dictionary with result and metadata.
        """
        result = self.agent.run(task)
        
        if result.success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        return {
            "worker_id": self.worker_id,
            "result": result.output,
            "success": result.success,
            "termination_reason": result.termination_reason,
            "total_steps": result.total_steps,
        }
    
    def can_handle(self, task_description: str) -> bool:
        """Check if this worker can handle a task.
        
        Args:
            task_description: Description of the task.
            
        Returns:
            True if worker has relevant capabilities.
        """
        # Simple keyword matching with variant support
        task_lower = task_description.lower()
        
        # Map capabilities to their variants
        capability_variants = {
            "research": ["research", "find", "search", "investigate"],
            "analysis": ["analyze", "analysis", "evaluate", "assess"],
            "writing": ["write", "writing", "draft", "compose"],
        }
        
        for capability in self.capabilities:
            capability_lower = capability.lower()
            # Check direct match
            if capability_lower in task_lower:
                return True
            # Check variants
            if capability_lower in capability_variants:
                for variant in capability_variants[capability_lower]:
                    if variant in task_lower:
                        return True
        return False


class Supervisor:
    """Supervisor agent that coordinates workers."""
    
    def __init__(
        self,
        supervisor_agent: Agent,
        workers: list[Worker],
    ) -> None:
        """Initialize supervisor.
        
        Args:
            supervisor_agent: The supervisor agent.
            workers: List of worker agents.
        """
        self.supervisor_agent = supervisor_agent
        self.workers = {w.worker_id: w for w in workers}
        self.delegations: list[TaskDelegation] = []
    
    def decompose_task(self, task: TaskSpec) -> list[dict[str, Any]]:
        """Decompose a complex task into subtasks.
        
        Args:
            task: The complex task to decompose.
            
        Returns:
            List of subtask descriptions.
        """
        # Simple decomposition: create subtasks based on keywords
        subtasks = []
        
        # Check for research needs
        if any(keyword in task.goal.lower() for keyword in ["research", "find", "search"]):
            subtasks.append({
                "task_id": "research_1",
                "description": f"Research: {task.goal}",
                "required_capability": "research",
            })
        
        # Check for writing needs
        if any(keyword in task.goal.lower() for keyword in ["write", "draft", "compose"]):
            subtasks.append({
                "task_id": "write_1",
                "description": f"Write: {task.goal}",
                "required_capability": "writing",
            })
        
        # Check for analysis needs
        if any(keyword in task.goal.lower() for keyword in ["analyze", "evaluate", "assess"]):
            subtasks.append({
                "task_id": "analyze_1",
                "description": f"Analyze: {task.goal}",
                "required_capability": "analysis",
            })
        
        # If no specific subtasks, create a general task
        if not subtasks:
            subtasks.append({
                "task_id": "general_1",
                "description": task.goal,
                "required_capability": None,
            })
        
        return subtasks
    
    def assign_worker(self, subtask: dict[str, Any]) -> str | None:
        """Assign a worker to a subtask.
        
        Args:
            subtask: The subtask to assign.
            
        Returns:
            Worker ID if assigned, None otherwise.
        """
        required_capability = subtask.get("required_capability")
        
        # Find workers with matching capability
        for worker_id, worker in self.workers.items():
            if required_capability is None:
                # Any worker can handle general tasks
                return worker_id
            
            if required_capability in worker.capabilities:
                return worker_id
        
        # No suitable worker found
        return None
    
    def execute_with_workers(self, task: TaskSpec) -> dict[str, Any]:
        """Execute a task using worker delegation.
        
        Args:
            task: The task to execute.
            
        Returns:
            Dictionary with results from all workers.
        """
        # Decompose task
        subtasks = self.decompose_task(task)
        
        results = []
        
        for subtask in subtasks:
            # Assign worker
            worker_id = self.assign_worker(subtask)
            
            if worker_id is None:
                # No suitable worker
                delegation = TaskDelegation(
                    task_id=subtask["task_id"],
                    task_description=subtask["description"],
                    assigned_worker="none",
                    status="failed",
                    error="No suitable worker available",
                )
                self.delegations.append(delegation)
                results.append({
                    "task_id": subtask["task_id"],
                    "success": False,
                    "error": "No suitable worker available",
                })
                continue
            
            # Create delegation
            delegation = TaskDelegation(
                task_id=subtask["task_id"],
                task_description=subtask["description"],
                assigned_worker=worker_id,
                status="in_progress",
            )
            self.delegations.append(delegation)
            
            # Execute with worker
            worker = self.workers[worker_id]
            subtask_spec = TaskSpec(
                goal=subtask["description"],
                success_criteria=["Task completed"],
                max_steps=10,
            )
            
            worker_result = worker.execute_task(subtask_spec)
            
            # Update delegation
            delegation.status = "completed" if worker_result["success"] else "failed"
            delegation.result = worker_result["result"]
            
            results.append({
                "task_id": subtask["task_id"],
                "worker_id": worker_id,
                "success": worker_result["success"],
                "result": worker_result["result"],
            })
        
        # Aggregate results
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "subtask_results": results,
            "delegations": [d.to_dict() for d in self.delegations],
        }
    
    def get_worker_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all workers.
        
        Returns:
            Dictionary of worker ID to stats.
        """
        stats = {}
        for worker_id, worker in self.workers.items():
            stats[worker_id] = {
                "tasks_completed": worker.tasks_completed,
                "tasks_failed": worker.tasks_failed,
                "capabilities": worker.capabilities,
            }
        return stats
