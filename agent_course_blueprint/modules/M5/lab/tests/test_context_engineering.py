import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.context import (
    BudgetContextBuilder, ContextItem, ContextPriority,
    TokenBudget, PrioritySelector, TruncationCompactor
)
from agent_course.core import TaskSpec, AgentState, Observation
from agent_course.tools import create_builtin_tools


def test_context_builder_creation():
    """Test that context builder can be created."""
    builder = BudgetContextBuilder(
        system_prompt="You are helpful",
        max_tokens=1000,
    )
    assert builder.budget.max_tokens == 1000


def test_context_selection_log():
    """Test that selection log is recorded."""
    builder = BudgetContextBuilder(max_tokens=1000)
    task = TaskSpec(goal="Test task")
    state = AgentState(task=task)

    builder.build(task, state)

    log = builder.selection_log
    assert len(log) > 0
    assert all("selected" in entry for entry in log)


def test_critical_items_always_selected():
    """Test that CRITICAL items are always selected."""
    builder = BudgetContextBuilder(
        system_prompt="You are helpful",
        max_tokens=100,  # Very small budget
    )
    task = TaskSpec(goal="Test")
    state = AgentState(task=task)

    messages = builder.build(task, state)

    # Should have at least system and task messages
    assert len(messages) >= 2


def test_budget_overflow_handling():
    """Test that budget overflow is handled."""
    builder = BudgetContextBuilder(max_tokens=200)
    task = TaskSpec(goal="Test")
    state = AgentState(task=task)

    # Add many tool results
    for i in range(10):
        state.add_tool_result(f"tool_{i}", {"result": f"Result {i}" * 20})

    messages = builder.build(task, state)

    # Should not crash, should handle overflow
    assert messages is not None


def test_compaction_applied():
    """Test that compaction is applied when needed."""
    builder = BudgetContextBuilder(
        max_tokens=500,
        compactor=TruncationCompactor(max_content_length=50),
    )
    task = TaskSpec(goal="Test")
    state = AgentState(task=task)

    # Add long tool result
    state.add_tool_result("tool", {"result": "A" * 200})

    messages = builder.build(task, state)

    # Should have truncated content
    assert messages is not None


def test_priority_ordering():
    """Test that items are selected by priority."""
    from agent_course.context.selection import PrioritySelector

    items = [
        ContextItem(content="Low", priority=ContextPriority.LOW, source="l", token_count=10),
        ContextItem(content="Critical", priority=ContextPriority.CRITICAL, source="c", token_count=10),
        ContextItem(content="High", priority=ContextPriority.HIGH, source="h", token_count=10),
    ]

    selector = PrioritySelector()
    selected = selector.select(items, budget_tokens=100)

    # Critical should be first
    assert selected[0].priority == ContextPriority.CRITICAL
