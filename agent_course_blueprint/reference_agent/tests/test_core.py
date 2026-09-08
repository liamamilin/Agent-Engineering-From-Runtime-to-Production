import pytest

from agent_course.core import (
    TaskSpec,
    Observation,
    AgentState,
    Decision,
    Transition,
    TerminationPolicy,
    TerminationReason,
)


class TestTaskSpec:
    def test_create_task_spec(self):
        task = TaskSpec(
            goal="Answer the question",
            success_criteria=["Correct answer provided"],
            max_steps=10,
        )
        assert task.goal == "Answer the question"
        assert task.max_steps == 10
        assert task.success_criteria == ["Correct answer provided"]

    def test_task_spec_defaults(self):
        task = TaskSpec(goal="Test")
        assert task.constraints == []
        assert task.max_steps == 20
        assert task.max_cost_usd is None


class TestObservation:
    def test_from_user(self):
        obs = Observation.from_user("Hello")
        assert obs.kind == "user"
        assert obs.payload == "Hello"

    def test_from_tool(self):
        obs = Observation.from_tool("search", {"results": ["a", "b"]})
        assert obs.kind == "tool"
        assert obs.payload["tool"] == "search"

    def test_from_error(self):
        obs = Observation.from_error("Something failed")
        assert obs.kind == "error"
        assert obs.payload == "Something failed"


class TestAgentState:
    def test_create_state(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        assert state.step_count == 0
        assert state.status == "running"
        assert state.observations == []
        assert state.tool_results == []

    def test_add_observation(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_user("Hello")
        state.add_observation(obs)
        assert len(state.observations) == 1

    def test_set_final_output(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        state.set_final_output("Done")
        assert state.final_output == "Done"
        assert state.status == "completed"

    def test_set_error(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        state.set_error("Failed")
        assert state.error == "Failed"
        assert state.status == "failed"


class TestDecision:
    def test_call_tool(self):
        decision = Decision.call_tool("search", {"query": "test"})
        assert decision.kind == "tool"
        assert decision.name == "search"
        assert decision.arguments == {"query": "test"}

    def test_ask_user(self):
        decision = Decision.ask_user("What do you mean?")
        assert decision.kind == "ask_user"
        assert decision.content == "What do you mean?"

    def test_final_answer(self):
        decision = Decision.final_answer("The answer is 42")
        assert decision.kind == "final"
        assert decision.content == "The answer is 42"

    def test_fail(self):
        decision = Decision.fail("Cannot proceed")
        assert decision.kind == "fail"
        assert decision.reason == "Cannot proceed"


class TestTransition:
    def test_apply_tool_decision(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_user("Search for X")
        decision = Decision.call_tool("search", {"query": "X"})
        result = {"items": ["X1", "X2"]}

        new_state = Transition.apply(state, obs, decision, result)

        assert new_state.step_count == 1
        assert len(new_state.observations) == 1
        assert len(new_state.tool_results) == 1
        assert new_state.tool_results[0]["tool"] == "search"

    def test_apply_final_decision(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_user("Done")
        decision = Decision.final_answer("Result")

        new_state = Transition.apply(state, obs, decision)

        assert new_state.status == "completed"
        assert new_state.final_output == "Result"

    def test_apply_fail_decision(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_error("Error")
        decision = Decision.fail("Cannot proceed")

        new_state = Transition.apply(state, obs, decision)

        assert new_state.status == "failed"
        assert new_state.error == "Cannot proceed"


class TestTerminationPolicy:
    def test_stop_on_completed(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        state.set_final_output("Done")

        policy = TerminationPolicy()
        should_stop, reason = policy.should_stop(task, state)

        assert should_stop is True
        assert reason == TerminationReason.SUCCESS

    def test_stop_on_failed(self):
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        state.set_error("Error")

        policy = TerminationPolicy()
        should_stop, reason = policy.should_stop(task, state)

        assert should_stop is True
        assert reason == TerminationReason.FAILED

    def test_stop_on_max_steps(self):
        task = TaskSpec(goal="Test", max_steps=5)
        state = AgentState(task=task)
        state.step_count = 5

        policy = TerminationPolicy()
        should_stop, reason = policy.should_stop(task, state)

        assert should_stop is True
        assert reason == TerminationReason.MAX_STEPS

    def test_continue_running(self):
        task = TaskSpec(goal="Test", max_steps=10)
        state = AgentState(task=task)
        state.step_count = 3

        policy = TerminationPolicy()
        should_stop, reason = policy.should_stop(task, state)

        assert should_stop is False
        assert reason is None
