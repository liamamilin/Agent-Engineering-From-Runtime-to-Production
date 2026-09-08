"""Checkpoint system for saving and resuming Agent runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Checkpoint:
    """A saved state of an Agent run that can be resumed."""

    run_id: str
    step_count: int
    state_snapshot: dict[str, Any]
    task: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Create checkpoint from dictionary."""
        return cls(**data)


class CheckpointStore:
    """Storage for Agent run checkpoints.
    
    Supports saving, loading, and listing checkpoints for resume capability.
    """

    def __init__(self, storage_path: str | Path | None = None) -> None:
        """Initialize checkpoint store.
        
        Args:
            storage_path: Directory to store checkpoints. If None, uses in-memory storage.
        """
        self._storage_path = Path(storage_path) if storage_path else None
        self._memory_store: dict[str, Checkpoint] = {}
        
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint.
        
        Args:
            checkpoint: The checkpoint to save.
        """
        if self._storage_path:
            # File-based storage
            file_path = self._storage_path / f"{checkpoint.run_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            # In-memory storage
            self._memory_store[checkpoint.run_id] = checkpoint

    def load(self, run_id: str) -> Checkpoint | None:
        """Load a checkpoint by run ID.
        
        Args:
            run_id: The ID of the run to load.
            
        Returns:
            The checkpoint if found, None otherwise.
        """
        if self._storage_path:
            file_path = self._storage_path / f"{run_id}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Checkpoint.from_dict(data)
            return None
        else:
            return self._memory_store.get(run_id)

    def delete(self, run_id: str) -> bool:
        """Delete a checkpoint.
        
        Args:
            run_id: The ID of the run to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if self._storage_path:
            file_path = self._storage_path / f"{run_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        else:
            if run_id in self._memory_store:
                del self._memory_store[run_id]
                return True
            return False

    def list_checkpoints(self) -> list[str]:
        """List all checkpoint run IDs.
        
        Returns:
            List of run IDs.
        """
        if self._storage_path:
            return [f.stem for f in self._storage_path.glob("*.json")]
        else:
            return list(self._memory_store.keys())

    def exists(self, run_id: str) -> bool:
        """Check if a checkpoint exists.
        
        Args:
            run_id: The ID to check.
            
        Returns:
            True if exists, False otherwise.
        """
        if self._storage_path:
            file_path = self._storage_path / f"{run_id}.json"
            return file_path.exists()
        else:
            return run_id in self._memory_store
