from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class ContextPriority(IntEnum):
    """Priority levels for context items."""

    CRITICAL = 0  # Must include (system prompt, task)
    HIGH = 1  # Should include (recent observations)
    MEDIUM = 2  # Nice to have (tool results)
    LOW = 3  # Optional (historical data)


@dataclass
class ContextItem:
    """An item to be included in context."""

    content: str
    priority: ContextPriority
    source: str  # Where this came from
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: ContextItem) -> bool:
        """For sorting by priority."""
        return self.priority < other.priority


class SelectionPolicy:
    """Base class for context selection policies."""

    def select(
        self,
        items: list[ContextItem],
        budget_tokens: int,
    ) -> list[ContextItem]:
        """Select items within budget."""
        raise NotImplementedError


class PrioritySelector(SelectionPolicy):
    """Select items by priority, then by recency."""

    def select(
        self,
        items: list[ContextItem],
        budget_tokens: int,
    ) -> list[ContextItem]:
        """Select items by priority within budget."""
        # Sort by priority (lower is higher priority)
        sorted_items = sorted(items, key=lambda x: x.priority)

        selected: list[ContextItem] = []
        total_tokens = 0

        for item in sorted_items:
            if total_tokens + item.token_count <= budget_tokens:
                selected.append(item)
                total_tokens += item.token_count
            elif item.priority == ContextPriority.CRITICAL:
                # Always include critical items, even if over budget
                selected.append(item)
                total_tokens += item.token_count

        return selected


class RecencySelector(SelectionPolicy):
    """Select items by recency within budget."""

    def __init__(self, max_items: int | None = None):
        self._max_items = max_items

    def select(
        self,
        items: list[ContextItem],
        budget_tokens: int,
    ) -> list[ContextItem]:
        """Select most recent items within budget."""
        # Items are assumed to be in chronological order
        selected: list[ContextItem] = []
        total_tokens = 0

        # Iterate in reverse (most recent first)
        for item in reversed(items):
            if total_tokens + item.token_count <= budget_tokens:
                selected.insert(0, item)  # Insert at beginning to maintain order
                total_tokens += item.token_count

            if self._max_items and len(selected) >= self._max_items:
                break

        return selected
