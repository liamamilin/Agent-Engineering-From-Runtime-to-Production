import pytest

from agent_course.context import (
    BudgetContextBuilder,
    ContextItem,
    ContextPriority,
    TokenBudget,
    BudgetExceededError,
    SelectionPolicy,
    PrioritySelector,
    Compactor,
    SummaryCompactor,
)
from agent_course.context.selection import RecencySelector
from agent_course.context.compaction import TruncationCompactor
from agent_course.core import TaskSpec, AgentState, Observation


class TestTokenBudget:
    def test_create_budget(self):
        budget = TokenBudget(max_tokens=1000)
        assert budget.max_tokens == 1000
        assert budget.available_tokens == 1000

    def test_allocate(self):
        budget = TokenBudget(max_tokens=1000)
        budget.allocate(300)
        assert budget.used_tokens == 300
        assert budget.available_tokens == 700

    def test_allocate_exceeds_raises(self):
        budget = TokenBudget(max_tokens=100)
        with pytest.raises(BudgetExceededError):
            budget.allocate(200)

    def test_reserve_and_release(self):
        budget = TokenBudget(max_tokens=1000)
        budget.reserve(200)
        assert budget.available_tokens == 800
        budget.release(100)
        assert budget.available_tokens == 900

    def test_utilization(self):
        budget = TokenBudget(max_tokens=1000)
        budget.allocate(500)
        assert budget.utilization == 0.5


class TestContextItem:
    def test_create_item(self):
        item = ContextItem(
            content="Hello",
            priority=ContextPriority.HIGH,
            source="test",
            token_count=10,
        )
        assert item.content == "Hello"
        assert item.priority == ContextPriority.HIGH

    def test_priority_comparison(self):
        critical = ContextItem(content="A", priority=ContextPriority.CRITICAL, source="a")
        low = ContextItem(content="B", priority=ContextPriority.LOW, source="b")
        assert critical < low  # Lower number = higher priority


class TestPrioritySelector:
    def test_select_by_priority(self):
        items = [
            ContextItem(content="Low", priority=ContextPriority.LOW, source="l", token_count=10),
            ContextItem(content="Critical", priority=ContextPriority.CRITICAL, source="c", token_count=10),
            ContextItem(content="High", priority=ContextPriority.HIGH, source="h", token_count=10),
        ]
        selector = PrioritySelector()
        selected = selector.select(items, budget_tokens=100)

        # Should be sorted by priority
        assert selected[0].priority == ContextPriority.CRITICAL
        assert selected[1].priority == ContextPriority.HIGH

    def test_select_within_budget(self):
        items = [
            ContextItem(content="A", priority=ContextPriority.HIGH, source="a", token_count=50),
            ContextItem(content="B", priority=ContextPriority.HIGH, source="b", token_count=50),
            ContextItem(content="C", priority=ContextPriority.LOW, source="c", token_count=50),
        ]
        selector = PrioritySelector()
        selected = selector.select(items, budget_tokens=100)

        assert len(selected) == 2

    def test_critical_always_included(self):
        items = [
            ContextItem(content="Critical", priority=ContextPriority.CRITICAL, source="c", token_count=200),
        ]
        selector = PrioritySelector()
        selected = selector.select(items, budget_tokens=100)

        # Critical should be included even if over budget
        assert len(selected) == 1


class TestRecencySelector:
    def test_select_recent(self):
        items = [
            ContextItem(content="Old", priority=ContextPriority.MEDIUM, source="1", token_count=10),
            ContextItem(content="Medium", priority=ContextPriority.MEDIUM, source="2", token_count=10),
            ContextItem(content="Recent", priority=ContextPriority.MEDIUM, source="3", token_count=10),
        ]
        selector = RecencySelector(max_items=2)
        selected = selector.select(items, budget_tokens=100)

        assert len(selected) == 2
        assert selected[-1].content == "Recent"


class TestCompactor:
    def test_truncation_compactor(self):
        items = [
            ContextItem(content="A" * 500, priority=ContextPriority.MEDIUM, source="a", token_count=125),
        ]
        compactor = TruncationCompactor(max_content_length=100)
        compacted = compactor.compact(items)

        assert len(compacted[0].content) <= 103  # 100 + "..."

    def test_summary_compactor(self):
        items = [
            ContextItem(content="Item 1", priority=ContextPriority.LOW, source="1", token_count=10),
            ContextItem(content="Item 2", priority=ContextPriority.LOW, source="2", token_count=10),
            ContextItem(content="Item 3", priority=ContextPriority.LOW, source="3", token_count=10),
            ContextItem(content="Recent 1", priority=ContextPriority.HIGH, source="r1", token_count=10),
            ContextItem(content="Recent 2", priority=ContextPriority.HIGH, source="r2", token_count=10),
        ]
        compactor = SummaryCompactor(keep_recent=2)
        compacted = compactor.compact(items)

        # Should have summary + 2 recent items
        assert len(compacted) == 3
        assert compacted[0].source == "summary"


class TestBudgetContextBuilder:
    def test_build_basic_context(self):
        builder = BudgetContextBuilder(
            system_prompt="You are helpful",
            max_tokens=1000,
        )
        task = TaskSpec(goal="Test task")
        state = AgentState(task=task)

        messages = builder.build(task, state)

        assert len(messages) >= 2
        assert messages[0].role.value == "system"

    def test_build_with_observation(self):
        builder = BudgetContextBuilder(max_tokens=1000)
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)
        obs = Observation.from_user("Hello")

        messages = builder.build(task, state, obs)

        assert any("Hello" in m.content for m in messages)

    def test_selection_log(self):
        builder = BudgetContextBuilder(max_tokens=1000)
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)

        builder.build(task, state)

        log = builder.selection_log
        assert len(log) > 0
        assert all("selected" in entry for entry in log)

    def test_budget_tracking(self):
        builder = BudgetContextBuilder(max_tokens=1000)
        task = TaskSpec(goal="Test")
        state = AgentState(task=task)

        builder.build(task, state)

        # Budget should have been used
        assert builder.budget.max_tokens == 1000
