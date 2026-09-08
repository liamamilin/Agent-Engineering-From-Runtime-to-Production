from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.core.task import TaskSpec
from agent_course.core.state import AgentState
from agent_course.core.observation import Observation
from agent_course.core.decision import Decision
from agent_course.core.transition import Transition
from agent_course.core.termination import TerminationPolicy, TerminationReason
from agent_course.llm.base import ModelAdapter
from agent_course.runtime.context_builder import ContextBuilder
from agent_course.runtime.policy import ModelPolicy
from agent_course.tools.registry import ToolRegistry
from agent_course.tools.executor import ToolExecutor, ToolResult
from agent_course.tracing.schema import Trace, StepRecord


@dataclass
class AgentRunResult:
    """Result of an agent run."""

    success: bool
    output: Any = None
    termination_reason: str | None = None
    total_steps: int = 0
    trace: Trace | None = None
    error: str | None = None


class Agent:
    """The main agent runtime controller."""

    def __init__(
        self,
        model: ModelAdapter,
        tools: ToolRegistry | None = None,
        termination: TerminationPolicy | None = None,
        system_prompt: str = "You are a helpful assistant.",
    ) -> None:
        self._model = model
        self._tools = tools
        self._termination = termination or TerminationPolicy()
        self._executor = ToolExecutor(tools) if tools else None

        context_builder = ContextBuilder(system_prompt=system_prompt)
        self._policy = ModelPolicy(model, context_builder)

    def run(self, task: TaskSpec, initial_observation: Observation | None = None) -> AgentRunResult:
        """Run the agent on a task."""
        state = AgentState(task=task)
        trace = Trace(task={"goal": task.goal, "success_criteria": task.success_criteria})

        observation = initial_observation

        while True:
            # Record step start
            step_record = StepRecord(step_number=state.step_count + 1)

            # 1. Observe (already have observation from previous iteration or initial)
            step_record.observation = {
                "kind": observation.kind if observation else "initial",
                "payload": str(observation.payload) if observation else None,
            }

            # 2. Decide
            decision = self._policy.decide(task, state, observation, self._tools)
            step_record.decision = {
                "kind": decision.kind,
                "name": decision.name,
                "arguments": decision.arguments,
                "content": str(decision.content)[:100] if decision.content else None,
            }

            # 3. Execute action if tool call
            action_result = None
            if decision.kind == "tool" and self._executor:
                tool_result = self._executor.execute(decision.name, decision.arguments)
                action_result = tool_result.output if tool_result.success else None
                step_record.action_result = {
                    "success": tool_result.success,
                    "output": str(tool_result.output)[:200] if tool_result.output else None,
                    "error": tool_result.error,
                }

                # Create observation from tool result
                if tool_result.success:
                    observation = Observation.from_tool(decision.name, tool_result.output)
                else:
                    observation = Observation.from_error(tool_result.error or "Tool execution failed")
            else:
                observation = None

            # 4. Transition
            state = Transition.apply(state, step_record.observation.get("kind") and Observation(
                kind=step_record.observation["kind"],
                payload=step_record.observation["payload"],
            ) or Observation(kind="initial", payload=None), decision, action_result)

            step_record.state_snapshot = {
                "step_count": state.step_count,
                "status": state.status,
                "tool_results_count": len(state.tool_results),
            }

            # 5. Check termination
            should_stop, reason = self._termination.should_stop(task, state)

            # Add step to trace
            trace.add_step(step_record)

            if should_stop:
                trace.finish(
                    output=state.final_output,
                    reason=reason.value if reason else None,
                )
                return AgentRunResult(
                    success=reason == TerminationReason.SUCCESS if reason else False,
                    output=state.final_output,
                    termination_reason=reason.value if reason else None,
                    total_steps=state.step_count,
                    trace=trace,
                    error=state.error,
                )

            # If decision was final but termination didn't catch it
            if decision.kind == "final":
                trace.finish(output=decision.content, reason="final_decision")
                return AgentRunResult(
                    success=True,
                    output=decision.content,
                    termination_reason="final_decision",
                    total_steps=state.step_count,
                    trace=trace,
                )

            # If decision was fail
            if decision.kind == "fail":
                trace.finish(output=None, reason="failed")
                return AgentRunResult(
                    success=False,
                    output=None,
                    termination_reason="failed",
                    total_steps=state.step_count,
                    trace=trace,
                    error=decision.reason,
                )
