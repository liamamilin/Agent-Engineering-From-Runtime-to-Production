from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.core import TaskSpec
from agent_course.runtime import Agent, AgentRunResult
from agent_course.evals.dataset import EvalCase, EvalDataset
from agent_course.tracing import Trace


@dataclass
class EvalResult:
    """Result of evaluating a single case."""

    case_id: str
    task_success: bool
    action_correctness: float  # 0.0 to 1.0
    output_correctness: float  # 0.0 to 1.0
    step_count: int
    total_tokens: int = 0
    latency_ms: float = 0.0
    tool_calls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    failure_layer: str | None = None
    trace: Trace | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task_success": self.task_success,
            "action_correctness": self.action_correctness,
            "output_correctness": self.output_correctness,
            "step_count": self.step_count,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "failure_layer": self.failure_layer,
            "details": self.details,
        }


class Evaluator:
    """Evaluates agent runs against evaluation cases."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    def evaluate_case(self, case: EvalCase) -> EvalResult:
        """Evaluate a single case."""
        # Create task from case
        task = TaskSpec(
            goal=case.task_goal,
            success_criteria=case.success_criteria,
            constraints=case.constraints,
            max_steps=case.max_steps,
        )

        # Run agent
        import time
        start_time = time.time()
        result = self._agent.run(task)
        latency_ms = (time.time() - start_time) * 1000

        # Extract metrics
        tool_calls = []
        total_tokens = 0
        errors = []

        if result.trace:
            for step in result.trace.steps:
                if step.decision.get("kind") == "tool":
                    tool_calls.append(step.decision.get("name", ""))
                if step.state_snapshot.get("error"):
                    errors.append(step.state_snapshot["error"])

        # Calculate metrics
        task_success = result.success
        action_correctness = self._calculate_action_correctness(case, tool_calls)
        output_correctness = self._calculate_output_correctness(case, result.output)

        return EvalResult(
            case_id=case.id,
            task_success=task_success,
            action_correctness=action_correctness,
            output_correctness=output_correctness,
            step_count=result.total_steps,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            errors=errors,
            trace=result.trace,
        )

    def evaluate_dataset(self, dataset: EvalDataset) -> list[EvalResult]:
        """Evaluate all cases in a dataset."""
        results = []
        for case in dataset:
            result = self.evaluate_case(case)
            results.append(result)
        return results

    def _calculate_action_correctness(self, case: EvalCase, actual_tools: list[str]) -> float:
        """Calculate action correctness score."""
        if not case.expected_tool_calls:
            # No expected tools, any behavior is acceptable
            return 1.0 if not actual_tools else 0.5

        expected = set(case.expected_tool_calls)
        actual = set(actual_tools)

        if not expected:
            return 1.0

        # Jaccard similarity
        intersection = len(expected & actual)
        union = len(expected | actual)

        return intersection / union if union > 0 else 0.0

    def _calculate_output_correctness(self, case: EvalCase, actual_output: Any) -> float:
        """Calculate output correctness score."""
        if case.expected_output is None:
            # No expected output, check success criteria
            return 1.0 if actual_output else 0.0

        if actual_output is None:
            return 0.0

        expected = case.expected_output.lower().strip()
        actual = str(actual_output).lower().strip()

        # Exact match
        if expected == actual:
            return 1.0

        # Contains match
        if expected in actual or actual in expected:
            return 0.8

        # Word overlap
        expected_words = set(expected.split())
        actual_words = set(actual.split())

        if expected_words and actual_words:
            overlap = len(expected_words & actual_words) / len(expected_words)
            return overlap

        return 0.0


class MetricCalculator:
    """Calculates aggregate metrics from evaluation results."""

    @staticmethod
    def calculate_summary(results: list[EvalResult]) -> dict[str, Any]:
        """Calculate summary metrics."""
        if not results:
            return {}

        total = len(results)
        successful = sum(1 for r in results if r.task_success)

        return {
            "total_cases": total,
            "successful_cases": successful,
            "task_success_rate": successful / total if total > 0 else 0.0,
            "avg_action_correctness": sum(r.action_correctness for r in results) / total,
            "avg_output_correctness": sum(r.output_correctness for r in results) / total,
            "avg_step_count": sum(r.step_count for r in results) / total,
            "avg_latency_ms": sum(r.latency_ms for r in results) / total,
            "total_tokens": sum(r.total_tokens for r in results),
            "failure_layers": MetricCalculator._count_failure_layers(results),
        }

    @staticmethod
    def _count_failure_layers(results: list[EvalResult]) -> dict[str, int]:
        """Count failures by layer."""
        layers: dict[str, int] = {}
        for result in results:
            if result.failure_layer:
                layers[result.failure_layer] = layers.get(result.failure_layer, 0) + 1
        return layers
