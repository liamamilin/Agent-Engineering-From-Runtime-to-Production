from __future__ import annotations

from enum import Enum
from typing import Any

from agent_course.evals.evaluator import EvalResult


class FailureLayer(str, Enum):
    """Failure layers from docs/FAILURE_MODEL.md."""

    TASK = "task"  # Specification failure
    OBSERVATION = "observation"  # Perception/input failure
    CONTEXT = "context"  # Context construction failure
    POLICY = "policy"  # Decision failure
    ACTION = "action"  # Tool/action failure
    TRANSITION = "transition"  # State update failure
    CONTROL = "control"  # Orchestration failure
    KNOWLEDGE = "knowledge"  # Grounding failure
    MEMORY = "memory"  # Persistence failure
    COMPOSITION = "composition"  # Delegation failure
    SAFETY = "safety"  # Boundary failure
    RELIABILITY = "reliability"  # Infrastructure failure
    RESOURCE = "resource"  # Budget failure
    EVALUATION = "evaluation"  # Measurement failure


class FailureClassifier:
    """Classifies failures into layers based on symptoms."""

    @staticmethod
    def classify(result: EvalResult) -> FailureLayer | None:
        """Classify the failure layer for a failed result."""
        if result.task_success:
            return None

        # Check for specific symptoms
        errors = result.errors
        tool_calls = result.tool_calls

        # Action failure: tool errors
        if any("tool" in e.lower() or "permission" in e.lower() for e in errors):
            return FailureLayer.ACTION

        # Resource failure: max steps reached
        if result.step_count >= 10 and not result.task_success:
            # Check if it's stuck in a loop
            if len(set(tool_calls)) < len(tool_calls) / 2:
                return FailureLayer.CONTROL  # Loop detected
            return FailureLayer.RESOURCE

        # Policy failure: wrong tools called
        if result.action_correctness < 0.5:
            return FailureLayer.POLICY

        # Output failure: correct actions but wrong output
        if result.action_correctness >= 0.8 and result.output_correctness < 0.5:
            return FailureLayer.CONTEXT

        # Default to policy failure
        return FailureLayer.POLICY

    @staticmethod
    def classify_batch(results: list[EvalResult]) -> dict[FailureLayer, list[EvalResult]]:
        """Classify failures for a batch of results."""
        classified: dict[FailureLayer, list[EvalResult]] = {layer: [] for layer in FailureLayer}

        for result in results:
            layer = FailureClassifier.classify(result)
            if layer:
                classified[layer].append(result)
                result.failure_layer = layer.value

        return classified

    @staticmethod
    def summary(classified: dict[FailureLayer, list[EvalResult]]) -> dict[str, int]:
        """Generate a summary of failure counts by layer."""
        return {layer.value: len(results) for layer, results in classified.items() if results}
