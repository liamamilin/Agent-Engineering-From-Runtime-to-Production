from __future__ import annotations

from typing import Any

from agent_course.evals.evaluator import EvalResult


class TaskSuccessMetric:
    """Calculates task success rate."""

    @staticmethod
    def calculate(results: list[EvalResult]) -> float:
        """Calculate task success rate."""
        if not results:
            return 0.0
        successful = sum(1 for r in results if r.task_success)
        return successful / len(results)


class ActionCorrectnessMetric:
    """Calculates action correctness score."""

    @staticmethod
    def calculate(results: list[EvalResult]) -> float:
        """Calculate average action correctness."""
        if not results:
            return 0.0
        return sum(r.action_correctness for r in results) / len(results)


class CostMetric:
    """Calculates cost metrics."""

    # Pricing per 1K tokens (example values)
    PRICE_PER_1K_INPUT_TOKENS = 0.001
    PRICE_PER_1K_OUTPUT_TOKENS = 0.002

    @staticmethod
    def calculate_total_tokens(results: list[EvalResult]) -> int:
        """Calculate total tokens used."""
        return sum(r.total_tokens for r in results)

    @staticmethod
    def estimate_cost(results: list[EvalResult]) -> float:
        """Estimate cost in USD."""
        total_tokens = CostMetric.calculate_total_tokens(results)
        # Rough estimate: assume 50/50 input/output split
        input_tokens = total_tokens // 2
        output_tokens = total_tokens // 2

        cost = (
            (input_tokens / 1000) * CostMetric.PRICE_PER_1K_INPUT_TOKENS
            + (output_tokens / 1000) * CostMetric.PRICE_PER_1K_OUTPUT_TOKENS
        )
        return cost


class LatencyMetric:
    """Calculates latency metrics."""

    @staticmethod
    def calculate_avg_latency(results: list[EvalResult]) -> float:
        """Calculate average latency in milliseconds."""
        if not results:
            return 0.0
        return sum(r.latency_ms for r in results) / len(results)

    @staticmethod
    def calculate_p50_latency(results: list[EvalResult]) -> float:
        """Calculate p50 (median) latency."""
        if not results:
            return 0.0
        latencies = sorted(r.latency_ms for r in results)
        mid = len(latencies) // 2
        return latencies[mid]

    @staticmethod
    def calculate_p95_latency(results: list[EvalResult]) -> float:
        """Calculate p95 latency."""
        if not results:
            return 0.0
        latencies = sorted(r.latency_ms for r in results)
        idx = int(len(latencies) * 0.95)
        return latencies[min(idx, len(latencies) - 1)]


class StepCountMetric:
    """Calculates step count metrics."""

    @staticmethod
    def calculate_avg_steps(results: list[EvalResult]) -> float:
        """Calculate average step count."""
        if not results:
            return 0.0
        return sum(r.step_count for r in results) / len(results)

    @staticmethod
    def calculate_max_steps(results: list[EvalResult]) -> int:
        """Calculate maximum step count."""
        if not results:
            return 0
        return max(r.step_count for r in results)
