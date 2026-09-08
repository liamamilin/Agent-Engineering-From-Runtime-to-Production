import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from simulate import simulate_run
from agent_course.core import TerminationReason


def test_simulate_run_completes():
    result = simulate_run()
    assert result["should_stop"] is True
    assert result["termination_reason"] == TerminationReason.SUCCESS


def test_simulate_run_has_three_steps():
    result = simulate_run()
    assert len(result["trace"]) == 3
    assert result["state"].step_count == 3


def test_simulate_run_has_final_output():
    result = simulate_run()
    assert result["state"].final_output is not None
    assert "Python" in result["state"].final_output


def test_simulate_run_has_tool_results():
    result = simulate_run()
    assert len(result["state"].tool_results) == 2


def test_trace_records_decisions():
    result = simulate_run()
    decisions = [step["decision"] for step in result["trace"]]
    assert decisions[0].kind == "tool"
    assert decisions[0].name == "search"
    assert decisions[1].kind == "tool"
    assert decisions[1].name == "get_details"
    assert decisions[2].kind == "final"
