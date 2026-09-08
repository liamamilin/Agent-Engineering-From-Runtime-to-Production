from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:
    """Evidence with provenance tracking."""

    id: str
    content: str
    source: str
    document_id: str | None = None
    chunk_id: str | None = None
    score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class EvidenceStore:
    """Store for retrieved evidence."""

    _evidence: list[Evidence] = field(default_factory=list)

    def add(self, evidence: Evidence) -> None:
        """Add evidence to store."""
        self._evidence.append(evidence)

    def get(self, evidence_id: str) -> Evidence | None:
        """Get evidence by ID."""
        for e in self._evidence:
            if e.id == evidence_id:
                return e
        return None

    def list_all(self) -> list[Evidence]:
        """List all evidence."""
        return self._evidence.copy()

    def filter_by_source(self, source: str) -> list[Evidence]:
        """Filter evidence by source."""
        return [e for e in self._evidence if e.source == source]

    def __len__(self) -> int:
        return len(self._evidence)

    def __iter__(self):
        return iter(self._evidence)
