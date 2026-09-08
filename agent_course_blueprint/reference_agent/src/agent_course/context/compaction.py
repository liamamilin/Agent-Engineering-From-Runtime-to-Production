from __future__ import annotations

from typing import Any

from agent_course.context.selection import ContextItem


class Compactor:
    """Base class for context compaction."""

    def compact(self, items: list[ContextItem]) -> list[ContextItem]:
        """Compact items to reduce token count."""
        raise NotImplementedError


class SummaryCompactor(Compactor):
    """Compacts items by summarizing older content."""

    def __init__(self, keep_recent: int = 5):
        self._keep_recent = keep_recent

    def compact(self, items: list[ContextItem]) -> list[ContextItem]:
        """Keep recent items, summarize older ones."""
        if len(items) <= self._keep_recent:
            return items

        # Split into old and recent
        old_items = items[:-self._keep_recent]
        recent_items = items[-self._keep_recent:]

        # Create summary of old items
        if old_items:
            summary_content = self._summarize(old_items)
            summary_item = ContextItem(
                content=summary_content,
                priority=old_items[0].priority,
                source="summary",
                token_count=len(summary_content) // 4,  # Rough estimate
            )
            return [summary_item] + recent_items

        return recent_items

    def _summarize(self, items: list[ContextItem]) -> str:
        """Create a simple summary of items."""
        # Simple concatenation with truncation
        summaries = []
        for item in items[:3]:  # Only summarize first 3
            content = item.content[:100]  # Truncate
            summaries.append(f"[{item.source}]: {content}...")

        return "Previous context: " + " | ".join(summaries)


class TruncationCompactor(Compactor):
    """Compacts by truncating item content."""

    def __init__(self, max_content_length: int = 200):
        self._max_length = max_content_length

    def compact(self, items: list[ContextItem]) -> list[ContextItem]:
        """Truncate long items."""
        compacted = []
        for item in items:
            if len(item.content) > self._max_length:
                new_content = item.content[:self._max_length] + "..."
                new_item = ContextItem(
                    content=new_content,
                    priority=item.priority,
                    source=item.source,
                    token_count=len(new_content) // 4,
                    metadata={**item.metadata, "truncated": True},
                )
                compacted.append(new_item)
            else:
                compacted.append(item)
        return compacted
