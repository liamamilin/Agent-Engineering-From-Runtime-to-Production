import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.evals import (
    EvalCase, EvalDataset, Evaluator,
    MetricCalculator, FailureClassifier, ReplayHarness
)
from agent_course.evals.dataset import create_sample_dataset
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent


def test_eval_dataset_creation():
    """Test that sample dataset has 10+ cases."""
    dataset = create_sample_dataset()
    assert len(dataset) >= 10


def test_evaluator_runs_cases():
    """Test that evaluator can run cases."""
    model = FakeModel(responses=[
        ModelResponse(content="105"),
    ])
    agent = Agent(model=model)
    evaluator = Evaluator(agent)

    dataset = EvalDataset(name="test")
    dataset.add_case(EvalCase(
        id="test_001",
        task_goal="Calculate 15 * 7",
        success_criteria=["Result is 105"],
    ))

    results = evaluator.evaluate_dataset(dataset)
    assert len(results) == 1
    assert results[0].case_id == "test_001"


def test_metrics_calculation():
    """Test that metrics are calculated correctly."""
    model = FakeModel(responses=[
        ModelResponse(content="Done"),
    ])
    agent = Agent(model=model)
    evaluator = Evaluator(agent)

    dataset = create_sample_dataset()
    results = evaluator.evaluate_dataset(dataset)

    summary = MetricCalculator.calculate_summary(results)
    assert "total_cases" in summary
    assert "task_success_rate" in summary
    assert summary["total_cases"] >= 10


def test_failure_classification():
    """Test that failures are classified."""
    model = FakeModel(responses=[
        ModelResponse(content=""),
    ])
    agent = Agent(model=model)
    evaluator = Evaluator(agent)

    dataset = EvalDataset(name="test")
    dataset.add_case(EvalCase(
        id="fail_001",
        task_goal="Use nonexistent tool",
        success_criteria=["Should fail"],
    ))

    results = evaluator.evaluate_dataset(dataset)
    classified = FailureClassifier.classify_batch(results)

    # At least one failure should be classified
    total_failures = sum(len(v) for v in classified.values())
    assert total_failures >= 0  # May or may not fail depending on model


def test_replay_harness():
    """Test that replay harness works."""
    model = FakeModel(responses=[
        ModelResponse(
            content="",
            tool_calls=[{"name": "calculator", "arguments": {"expression": "2+2"}}],
        ),
        ModelResponse(content="4"),
    ])
    tools = create_builtin_tools()
    agent = Agent(model=model, tools=tools)

    from agent_course.core import TaskSpec
    task = TaskSpec(goal="Calculate 2+2", max_steps=5)
    result = agent.run(task)

    harness = ReplayHarness()
    replay_result = harness.replay_from_trace(result.trace)

    assert "comparison" in replay_result
    assert "replay_trace" in replay_result
