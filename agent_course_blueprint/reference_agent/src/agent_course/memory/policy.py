"""Memory policies for controlling write, read, and forgetting behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from agent_course.memory.store import MemoryRecord, MemoryType


@dataclass
class MemoryWritePolicy:
    """Policy for controlling when memories are written.
    
    Not every message should be stored as memory. This policy
    determines what gets persisted based on importance, type, and rules.
    """
    
    min_importance: float = 0.5  # Minimum importance to store
    auto_store_user: bool = True  # Always store user preferences
    auto_store_episodes: bool = False  # Don't auto-store all events
    required_tags: list[str] | None = None  # Must have these tags to store
    
    def should_store(self, memory: MemoryRecord) -> bool:
        """Determine if a memory should be stored.
        
        Args:
            memory: The memory to evaluate.
            
        Returns:
            True if should be stored, False otherwise.
        """
        # Check importance threshold
        if memory.importance < self.min_importance:
            return False
        
        # User memories always stored if enabled
        if memory.memory_type == MemoryType.USER and self.auto_store_user:
            return True
        
        # Episodic memories only if enabled
        if memory.memory_type == MemoryType.EPISODIC and not self.auto_store_episodes:
            return False
        
        # Check required tags
        if self.required_tags:
            if not all(tag in memory.tags for tag in self.required_tags):
                return False
        
        return True


@dataclass
class MemoryReadPolicy:
    """Policy for controlling how memories are retrieved.
    
    Determines which memories are relevant and how they should
    be ranked and filtered for context construction.
    """
    
    max_memories: int = 10  # Maximum memories to retrieve
    min_importance: float = 0.3  # Minimum importance to consider
    prefer_recent: bool = True  # Prefer recently accessed memories
    type_weights: dict[MemoryType, float] | None = None  # Weight by type
    
    def filter_and_rank(
        self,
        memories: list[MemoryRecord],
        context: dict[str, Any] | None = None,
    ) -> list[MemoryRecord]:
        """Filter and rank memories for retrieval.
        
        Args:
            memories: Candidate memories.
            context: Optional context for relevance scoring.
            
        Returns:
            Filtered and ranked list of memories.
        """
        # Filter by importance
        filtered = [m for m in memories if m.importance >= self.min_importance]
        
        # Score memories
        scored = []
        for memory in filtered:
            score = memory.importance
            
            # Boost by access count (recency proxy)
            if self.prefer_recent:
                score += memory.access_count * 0.1
            
            # Boost by type weight
            if self.type_weights:
                score *= self.type_weights.get(memory.memory_type, 1.0)
            
            # Context relevance (simple tag matching)
            if context and "tags" in context:
                context_tags = set(context["tags"])
                memory_tags = set(memory.tags)
                overlap = len(context_tags & memory_tags)
                score += overlap * 0.2
            
            scored.append((score, memory))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N
        return [m for _, m in scored[:self.max_memories]]


@dataclass
class ForgettingPolicy:
    """Policy for forgetting and invalidating old memories.
    
    Implements strategies like time-based decay, importance-based
    retention, and conflict resolution.
    """
    
    max_age_days: int | None = None  # Forget memories older than this
    min_access_count: int = 0  # Forget memories accessed fewer times
    low_importance_threshold: float = 0.2  # Forget if below this
    
    def should_forget(self, memory: MemoryRecord) -> bool:
        """Determine if a memory should be forgotten.
        
        Args:
            memory: The memory to evaluate.
            
        Returns:
            True if should be forgotten, False otherwise.
        """
        # Check age
        if self.max_age_days:
            created = datetime.fromisoformat(memory.created_at)
            age = datetime.now() - created
            if age.days > self.max_age_days:
                return True
        
        # Check access count
        if memory.access_count < self.min_access_count:
            return True
        
        # Check importance
        if memory.importance < self.low_importance_threshold:
            return True
        
        return False
    
    def apply_forgetting(self, memories: list[MemoryRecord]) -> list[str]:
        """Apply forgetting policy to a list of memories.
        
        Args:
            memories: Memories to evaluate.
            
        Returns:
            List of memory IDs that should be forgotten.
        """
        to_forget = []
        for memory in memories:
            if self.should_forget(memory):
                to_forget.append(memory.id)
        return to_forget
    
    def resolve_conflict(
        self,
        old_memory: MemoryRecord,
        new_memory: MemoryRecord,
    ) -> MemoryRecord:
        """Resolve conflict between old and new memory.
        
        Args:
            old_memory: The existing memory.
            new_memory: The new conflicting memory.
            
        Returns:
            The memory to keep (usually the new one).
        """
        # Default: keep the newer memory
        # Could be extended with more sophisticated logic
        
        # If old is more important, keep it
        if old_memory.importance > new_memory.importance * 1.5:
            return old_memory
        
        # Otherwise, keep the new one
        return new_memory
