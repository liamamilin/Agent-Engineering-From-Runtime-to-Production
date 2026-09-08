from __future__ import annotations

from typing import Any

from agent_course.core.task import TaskSpec
from agent_course.core.state import AgentState
from agent_course.core.observation import Observation
from agent_course.llm.base import Message
from agent_course.tools.registry import ToolRegistry
from agent_course.context.budget import TokenBudget
from agent_course.context.selection import (
    ContextItem,
    ContextPriority,
    SelectionPolicy,
    PrioritySelector,
)
from agent_course.context.compaction import Compactor, TruncationCompactor


class BudgetContextBuilder:
    """Budget-aware context builder with selection policy."""

    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int = 4000,
        selector: SelectionPolicy | None = None,
        compactor: Compactor | None = None,
    ) -> None:
        self._system_prompt = system_prompt
        self._budget = TokenBudget(max_tokens=max_tokens)
        self._selector = selector or PrioritySelector()
        self._compactor = compactor or TruncationCompactor()
        self._selection_log: list[dict[str, Any]] = []

    def build(
        self,
        task: TaskSpec,
        state: AgentState,
        observation: Observation | None = None,
        tools: ToolRegistry | None = None,
    ) -> list[Message]:
        """Build context messages within budget."""
        self._budget.reset()
        self._selection_log = []

        # Collect all context items
        items = self._collect_items(task, state, observation, tools)

        # Apply compaction if needed
        items = self._compactor.compact(items)

        # Select items within budget
        selected = self._selector.select(items, self._budget.max_tokens)

        # Log selections
        for item in items:
            self._selection_log.append({
                "source": item.source,
                "priority": item.priority.name,
                "tokens": item.token_count,
                "selected": item in selected,
            })

        # Build messages from selected items
        messages = self._build_messages(selected)

        return messages

    def _collect_items(
        self,
        task: TaskSpec,
        state: AgentState,
        observation: Observation | None,
        tools: ToolRegistry | None,
    ) -> list[ContextItem]:
        """Collect all potential context items."""
        items: list[ContextItem] = []

        # System prompt (CRITICAL)
        items.append(ContextItem(
            content=self._system_prompt,
            priority=ContextPriority.CRITICAL,
            source="system",
            token_count=len(self._system_prompt) // 4,
        ))

        # Task description (CRITICAL)
        task_content = f"Task: {task.goal}"
        if task.success_criteria:
            task_content += f"\nSuccess criteria: {', '.join(task.success_criteria)}"
        items.append(ContextItem(
            content=task_content,
            priority=ContextPriority.CRITICAL,
            source="task",
            token_count=len(task_content) // 4,
        ))

        # Current observation (HIGH)
        if observation:
            obs_content = str(observation.payload)
            items.append(ContextItem(
                content=obs_content,
                priority=ContextPriority.HIGH,
                source=f"observation:{observation.kind}",
                token_count=len(obs_content) // 4,
            ))

        # Recent tool results (MEDIUM)
        for i, result in enumerate(state.tool_results[-5:]):  # Last 5
            content = str(result)
            items.append(ContextItem(
                content=content,
                priority=ContextPriority.MEDIUM,
                source=f"tool_result:{i}",
                token_count=len(content) // 4,
            ))

        # Tool descriptions (LOW)
        if tools:
            for tool in tools.list_tools():
                content = f"{tool.name}: {tool.description}"
                items.append(ContextItem(
                    content=content,
                    priority=ContextPriority.LOW,
                    source=f"tool:{tool.name}",
                    token_count=len(content) // 4,
                ))

        return items

    def _build_messages(self, items: list[ContextItem]) -> list[Message]:
        """Build messages from selected items."""
        messages: list[Message] = []

        for item in items:
            if item.source == "system":
                messages.append(Message.system(item.content))
            elif item.source == "task":
                messages.append(Message.user(item.content))
            elif item.source.startswith("observation:user"):
                messages.append(Message.user(item.content))
            elif item.source.startswith("observation:tool"):
                messages.append(Message.tool(
                    tool_call_id="call_unknown",
                    content=item.content,
                ))
            elif item.source.startswith("tool_result"):
                messages.append(Message.assistant(item.content))
            elif item.source.startswith("tool:"):
                # Tool descriptions could be added as system message
                pass

        return messages

    @property
    def selection_log(self) -> list[dict[str, Any]]:
        """Log of what was selected/dropped."""
        return self._selection_log.copy()

    @property
    def budget(self) -> TokenBudget:
        """Current budget state."""
        return self._budget
