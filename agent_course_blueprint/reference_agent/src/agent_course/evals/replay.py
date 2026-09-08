from __future__ import annotations

from typing import Any

from agent_course.core import TaskSpec, Observation
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent
from agent_course.tracing import Trace, StepRecord


class ReplayHarness:
    """Replays agent runs from traces for debugging and regression testing."""

    def __init__(self) -> None:
        self._replay_results: list[dict[str, Any]] = []

    def replay_from_trace(
        self,
        trace: Trace,
        model_responses: list[ModelResponse] | None = None,
    ) -> dict[str, Any]:
        """Replay a trace with the same or different model responses.

        This allows testing if the agent behaves deterministically given
        the same model outputs.
        """
        # Create a fake model with the trace's decisions
        if model_responses is None:
            model_responses = self._extract_model_responses(trace)

        model = FakeModel(responses=model_responses)
        tools = create_builtin_tools()
        agent = Agent(model=model, tools=tools)

        # Extract task from trace
        task_data = trace.task
        task = TaskSpec(
            goal=task_data.get("goal", "Replay task"),
            success_criteria=task_data.get("success_criteria", []),
            max_steps=trace.total_steps + 5,  # Allow some margin
        )

        # Run agent
        result = agent.run(task)

        # Compare results
        comparison = self._compare_traces(trace, result.trace)

        replay_result = {
            "original_trace": trace,
            "replay_trace": result.trace,
            "comparison": comparison,
            "success": result.success,
            "deterministic": comparison["identical"],
        }

        self._replay_results.append(replay_result)
        return replay_result

    def _extract_model_responses(self, trace: Trace) -> list[ModelResponse]:
        """Extract model responses from a trace."""
        responses = []
        for step in trace.steps:
            decision = step.decision
            if decision.get("kind") == "tool":
                responses.append(ModelResponse(
                    content="",
                    tool_calls=[{
                        "name": decision.get("name", ""),
                        "arguments": decision.get("arguments", {}),
                    }],
                ))
            elif decision.get("kind") == "final":
                responses.append(ModelResponse(
                    content=str(decision.get("content", "")),
                ))
            else:
                responses.append(ModelResponse(content=""))
        return responses

    def _compare_traces(self, original: Trace, replay: Trace | None) -> dict[str, Any]:
        """Compare two traces for differences."""
        if replay is None:
            return {"identical": False, "reason": "No replay trace"}

        if original.total_steps != replay.total_steps:
            return {
                "identical": False,
                "reason": f"Step count mismatch: {original.total_steps} vs {replay.total_steps}",
            }

        # Compare each step
        differences = []
        for i, (orig_step, replay_step) in enumerate(zip(original.steps, replay.steps)):
            if orig_step.decision != replay_step.decision:
                differences.append({
                    "step": i,
                    "field": "decision",
                    "original": orig_step.decision,
                    "replay": replay_step.decision,
                })

        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "step_count_match": original.total_steps == replay.total_steps,
        }

    def check_regression(self, baseline_trace: Trace, new_trace: Trace) -> bool:
        """Check if new trace regresses from baseline."""
        comparison = self._compare_traces(baseline_trace, new_trace)
        return comparison["identical"]

    @property
    def replay_history(self) -> list[dict[str, Any]]:
        return self._replay_results.copy()
