import pytest
import tempfile
from pathlib import Path

from agent_course.evals import (
    EvalCase,
    EvalDataset,
    load_dataset,
    save_dataset,
    Evaluator,
    EvalResult,
    MetricCalculator,
    ReplayHarness,
    TaskSuccessMetric,
    ActionCorrectnessMetric,
    FailureClassifier,
    FailureLayer,
)
from agent_course.evals.dataset import create_sample_dataset
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent


class TestEvalCase:
    def test_create_case(self):
        case = EvalCase(
            id="test_001",
            task_goal="Test task",
            success_criteria=["Success"],
        )
        assert case.id == "test_001"
        assert case.task_goal == "Test task"

    def test_to_dict(self):
        case = EvalCase(
            id="test_001",
            task_goal="Test",
            success_criteria=["OK"],
        )
        d = case.to_dict()
        assert d["id"] == "test_001"
        assert d["task_goal"] == "Test"

    def test_from_dict(self):
        d = {"id": "test_001", "task_goal": "Test", "success_criteria": ["OK"]}
        case = EvalCase.from_dict(d)
        assert case.id == "test_001"


class TestEvalDataset:
    def test_create_dataset(self):
        dataset = EvalDataset(name="test_dataset")
        assert dataset.name == "test_dataset"
        assert len(dataset) == 0

    def test_add_case(self):
        dataset = EvalDataset(name="test")
        case = EvalCase(id="1", task_goal="Test", success_criteria=[])
        dataset.add_case(case)
        assert len(dataset) == 1

    def test_get_case(self):
        dataset = EvalDataset(name="test")
        case = EvalCase(id="1", task_goal="Test", success_criteria=[])
        dataset.add_case(case)
        retrieved = dataset.get_case("1")
        assert retrieved is not None
        assert retrieved.id == "1"

    def test_save_and_load(self):
        dataset = EvalDataset(name="test", version="1.0", description="Test dataset")
        dataset.add_case(EvalCase(id="1", task_goal="Task 1", success_criteria=["OK"]))
        dataset.add_case(EvalCase(id="2", task_goal="Task 2", success_criteria=["Done"]))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dataset.jsonl"
            save_dataset(dataset, path)

            loaded = load_dataset(path)
            assert loaded.name == "test"
            assert len(loaded) == 2
            assert loaded.get_case("1") is not None

    def test_sample_dataset(self):
        dataset = create_sample_dataset()
        assert len(dataset) >= 10
        assert dataset.name == "sample_agent_eval"


class TestEvaluator:
    def test_evaluate_simple_case(self):
        model = FakeModel(responses=[
            ModelResponse(content="105"),
        ])
        agent = Agent(model=model)
        evaluator = Evaluator(agent)

        case = EvalCase(
            id="calc_001",
            task_goal="Calculate 15 * 7",
            success_criteria=["Result is 105"],
            expected_output="105",
        )

        result = evaluator.evaluate_case(case)
        assert result.case_id == "calc_001"
        assert result.task_success is True
        assert result.output_correctness == 1.0

    def test_evaluate_with_tool_calls(self):
        model = FakeModel(responses=[
            ModelResponse(
                content="",
                tool_calls=[{"name": "calculator", "arguments": {"expression": "15 * 7"}}],
            ),
            ModelResponse(content="105"),
        ])
        tools = create_builtin_tools()
        agent = Agent(model=model, tools=tools)
        evaluator = Evaluator(agent)

        case = EvalCase(
            id="calc_002",
            task_goal="Calculate 15 * 7",
            success_criteria=["Result is 105"],
            expected_tool_calls=["calculator"],
        )

        result = evaluator.evaluate_case(case)
        assert "calculator" in result.tool_calls
        assert result.action_correctness == 1.0

    def test_evaluate_dataset(self):
        model = FakeModel(responses=[
            ModelResponse(content="Done"),
        ])
        agent = Agent(model=model)
        evaluator = Evaluator(agent)

        dataset = EvalDataset(name="test")
        dataset.add_case(EvalCase(id="1", task_goal="Task 1", success_criteria=[]))
        dataset.add_case(EvalCase(id="2", task_goal="Task 2", success_criteria=[]))

        results = evaluator.evaluate_dataset(dataset)
        assert len(results) == 2


class TestMetricCalculator:
    def test_calculate_summary(self):
        results = [
            EvalResult(
                case_id="1",
                task_success=True,
                action_correctness=1.0,
                output_correctness=1.0,
                step_count=2,
                latency_ms=100.0,
            ),
            EvalResult(
                case_id="2",
                task_success=False,
                action_correctness=0.5,
                output_correctness=0.0,
                step_count=5,
                latency_ms=200.0,
            ),
        ]

        summary = MetricCalculator.calculate_summary(results)
        assert summary["total_cases"] == 2
        assert summary["successful_cases"] == 1
        assert summary["task_success_rate"] == 0.5
        assert summary["avg_action_correctness"] == 0.75


class TestMetrics:
    def test_task_success_metric(self):
        results = [
            EvalResult(case_id="1", task_success=True, action_correctness=1.0, output_correctness=1.0, step_count=1),
            EvalResult(case_id="2", task_success=True, action_correctness=1.0, output_correctness=1.0, step_count=1),
            EvalResult(case_id="3", task_success=False, action_correctness=0.0, output_correctness=0.0, step_count=1),
        ]
        assert TaskSuccessMetric.calculate(results) == 2 / 3

    def test_action_correctness_metric(self):
        results = [
            EvalResult(case_id="1", task_success=True, action_correctness=1.0, output_correctness=1.0, step_count=1),
            EvalResult(case_id="2", task_success=True, action_correctness=0.5, output_correctness=1.0, step_count=1),
        ]
        assert ActionCorrectnessMetric.calculate(results) == 0.75


class TestFailureClassifier:
    def test_classify_success(self):
        result = EvalResult(
            case_id="1",
            task_success=True,
            action_correctness=1.0,
            output_correctness=1.0,
            step_count=1,
        )
        layer = FailureClassifier.classify(result)
        assert layer is None

    def test_classify_action_failure(self):
        result = EvalResult(
            case_id="1",
            task_success=False,
            action_correctness=0.0,
            output_correctness=0.0,
            step_count=1,
            errors=["Tool execution failed"],
        )
        layer = FailureClassifier.classify(result)
        assert layer == FailureLayer.ACTION

    def test_classify_batch(self):
        results = [
            EvalResult(case_id="1", task_success=True, action_correctness=1.0, output_correctness=1.0, step_count=1),
            EvalResult(case_id="2", task_success=False, action_correctness=0.0, output_correctness=0.0, step_count=1, errors=["Tool error"]),
        ]
        classified = FailureClassifier.classify_batch(results)
        assert len(classified[FailureLayer.ACTION]) == 1


class TestReplayHarness:
    def test_replay_from_trace(self):
        from agent_course.tracing import Trace, StepRecord

        # Create a simple trace
        trace = Trace(task={"goal": "Test", "success_criteria": []})
        step = StepRecord(
            step_number=1,
            decision={"kind": "final", "content": "Done"},
        )
        trace.add_step(step)
        trace.finish(output="Done", reason="success")

        harness = ReplayHarness()
        result = harness.replay_from_trace(trace)

        assert "comparison" in result
        assert "replay_trace" in result
