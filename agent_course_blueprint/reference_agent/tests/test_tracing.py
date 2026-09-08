import pytest

from agent_course.tracing import Trace, StepRecord, RunSummary


class TestTrace:
    def test_create_trace(self):
        trace = Trace(task={"goal": "Test"})
        assert trace.run_id is not None
        assert trace.total_steps == 0
        assert trace.steps == []

    def test_add_step(self):
        trace = Trace(task={"goal": "Test"})
        step = StepRecord(step_number=1)
        trace.add_step(step)
        assert trace.total_steps == 1
        assert len(trace.steps) == 1

    def test_finish(self):
        trace = Trace(task={"goal": "Test"})
        trace.finish(output="Done", reason="success")
        assert trace.final_output == "Done"
        assert trace.termination_reason == "success"
        assert trace.end_time is not None


class TestStepRecord:
    def test_create_step(self):
        step = StepRecord(step_number=1)
        assert step.step_id is not None
        assert step.step_number == 1
        assert step.timestamp is not None


class TestRunSummary:
    def test_from_trace(self):
        trace = Trace(task={"goal": "Test goal"})
        step1 = StepRecord(
            step_number=1,
            decision={"kind": "tool", "name": "search"},
            state_snapshot={},
        )
        step2 = StepRecord(
            step_number=2,
            decision={"kind": "final"},
            state_snapshot={},
        )
        trace.add_step(step1)
        trace.add_step(step2)
        trace.finish(output="Done", reason="success")

        summary = RunSummary.from_trace(trace)

        assert summary.run_id == trace.run_id
        assert summary.task_goal == "Test goal"
        assert summary.total_steps == 2
        assert summary.termination_reason == "success"
        assert summary.success is True
        assert "search" in summary.tool_calls
