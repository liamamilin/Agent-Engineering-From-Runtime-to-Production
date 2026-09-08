"""Memory store for persistent Agent knowledge."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryType(str, Enum):
    """Types of memory an Agent can store."""
    
    EPISODIC = "episodic"  # Events and experiences
    SEMANTIC = "semantic"  # Facts and knowledge
    USER = "user"  # User preferences and profile


@dataclass
class MemoryRecord:
    """A single memory record with metadata."""
    
    id: str
    memory_type: MemoryType
    content: str
    source: str  # Where this memory came from
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: str | None = None
    importance: float = 0.5  # 0.0 to 1.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    invalidated: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["memory_type"] = self.memory_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        """Create from dictionary."""
        data = data.copy()
        data["memory_type"] = MemoryType(data["memory_type"])
        return cls(**data)
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()


class MemoryStore:
    """Storage for Agent memories with type-based organization.
    
    Supports episodic (events), semantic (facts), and user (preferences) memory.
    """
    
    def __init__(self, storage_path: str | Path | None = None) -> None:
        """Initialize memory store.
        
        Args:
            storage_path: Directory to store memories. If None, uses in-memory storage.
        """
        self._storage_path = Path(storage_path) if storage_path else None
        self._memories: dict[str, MemoryRecord] = {}
        
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        """Load memories from disk."""
        if not self._storage_path:
            return
        
        for file_path in self._storage_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                memory = MemoryRecord.from_dict(data)
                self._memories[memory.id] = memory
            except (json.JSONDecodeError, KeyError):
                continue
    
    def _save_to_disk(self, memory: MemoryRecord) -> None:
        """Save a single memory to disk."""
        if not self._storage_path:
            return
        
        file_path = self._storage_path / f"{memory.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory.to_dict(), f, indent=2, ensure_ascii=False)
    
    def add(self, memory: MemoryRecord) -> None:
        """Add a memory record.
        
        Args:
            memory: The memory to add.
        """
        self._memories[memory.id] = memory
        self._save_to_disk(memory)
    
    def get(self, memory_id: str) -> MemoryRecord | None:
        """Get a memory by ID.
        
        Args:
            memory_id: The ID of the memory.
            
        Returns:
            The memory if found and not invalidated, None otherwise.
        """
        memory = self._memories.get(memory_id)
        if memory and not memory.invalidated:
            memory.touch()
            self._save_to_disk(memory)
            return memory
        return None
    
    def get_by_type(self, memory_type: MemoryType) -> list[MemoryRecord]:
        """Get all memories of a specific type.
        
        Args:
            memory_type: The type of memories to retrieve.
            
        Returns:
            List of memories of that type (excluding invalidated).
        """
        return [
            m for m in self._memories.values()
            if m.memory_type == memory_type and not m.invalidated
        ]
    
    def search(self, query: str, memory_type: MemoryType | None = None) -> list[MemoryRecord]:
        """Search memories by content.
        
        Args:
            query: Search query (simple substring match).
            memory_type: Optional type filter.
            
        Returns:
            List of matching memories (excluding invalidated).
        """
        query_lower = query.lower()
        results = []
        
        for memory in self._memories.values():
            if memory.invalidated:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            if query_lower in memory.content.lower():
                results.append(memory)
        
        # Sort by importance and access count
        results.sort(key=lambda m: (m.importance, m.access_count), reverse=True)
        return results
    
    def invalidate(self, memory_id: str) -> bool:
        """Invalidate a memory (soft delete).
        
        Args:
            memory_id: The ID of the memory to invalidate.
            
        Returns:
            True if invalidated, False if not found.
        """
        memory = self._memories.get(memory_id)
        if memory:
            memory.invalidated = True
            memory.updated_at = datetime.now().isoformat()
            self._save_to_disk(memory)
            return True
        return False
    
    def delete(self, memory_id: str) -> bool:
        """Permanently delete a memory.
        
        Args:
            memory_id: The ID of the memory to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if memory_id in self._memories:
            del self._memories[memory_id]
            if self._storage_path:
                file_path = self._storage_path / f"{memory_id}.json"
                if file_path.exists():
                    file_path.unlink()
            return True
        return False
    
    def list_all(self, include_invalidated: bool = False) -> list[MemoryRecord]:
        """List all memories.
        
        Args:
            include_invalidated: Whether to include invalidated memories.
            
        Returns:
            List of all memories.
        """
        if include_invalidated:
            return list(self._memories.values())
        return [m for m in self._memories.values() if not m.invalidated]
    
    def count(self, memory_type: MemoryType | None = None) -> int:
        """Count memories.
        
        Args:
            memory_type: Optional type filter.
            
        Returns:
            Number of memories (excluding invalidated).
        """
        if memory_type:
            return len(self.get_by_type(memory_type))
        return len([m for m in self._memories.values() if not m.invalidated])
