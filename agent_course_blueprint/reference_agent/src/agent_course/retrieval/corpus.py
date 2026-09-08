from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A chunk of a document."""

    id: str
    content: str
    document_id: str
    start_index: int = 0
    end_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """A document in the corpus."""

    id: str
    content: str
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)

    def chunk(self, chunk_size: int = 200, overlap: int = 50) -> list[Chunk]:
        """Split document into chunks."""
        self.chunks = []
        start = 0
        chunk_idx = 0

        while start < len(self.content):
            end = min(start + chunk_size, len(self.content))
            chunk_content = self.content[start:end]

            chunk = Chunk(
                id=f"{self.id}_chunk_{chunk_idx}",
                content=chunk_content,
                document_id=self.id,
                start_index=start,
                end_index=end,
            )
            self.chunks.append(chunk)

            start = end - overlap if end < len(self.content) else end
            chunk_idx += 1

        return self.chunks


@dataclass
class Corpus:
    """A collection of documents."""

    name: str
    documents: list[Document] = field(default_factory=list)

    def add_document(self, doc: Document) -> None:
        """Add a document to the corpus."""
        self.documents.append(doc)

    def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    def get_all_chunks(self) -> list[Chunk]:
        """Get all chunks from all documents."""
        chunks = []
        for doc in self.documents:
            if not doc.chunks:
                doc.chunk()
            chunks.extend(doc.chunks)
        return chunks

    def __len__(self) -> int:
        return len(self.documents)


def create_sample_corpus() -> Corpus:
    """Create a sample corpus for testing."""
    corpus = Corpus(name="sample_corpus")

    # Document 1: Python basics
    doc1 = Document(
        id="doc_1",
        title="Python Programming",
        content="Python is a high-level, interpreted programming language. "
                "It was created by Guido van Rossum and first released in 1991. "
                "Python features dynamic typing and garbage collection. "
                "It supports multiple programming paradigms including procedural, "
                "object-oriented, and functional programming.",
    )
    doc1.chunk(chunk_size=100, overlap=20)
    corpus.add_document(doc1)

    # Document 2: Machine Learning
    doc2 = Document(
        id="doc_2",
        title="Machine Learning Basics",
        content="Machine learning is a subset of artificial intelligence. "
                "It enables systems to learn from data without explicit programming. "
                "Common types include supervised, unsupervised, and reinforcement learning. "
                "Neural networks are inspired by biological neural networks.",
    )
    doc2.chunk(chunk_size=100, overlap=20)
    corpus.add_document(doc2)

    # Document 3: Agent Systems
    doc3 = Document(
        id="doc_3",
        title="Agent Engineering",
        content="An agent is a stateful runtime controller that pursues tasks. "
                "Agents observe their environment, make decisions, and take actions. "
                "Key components include task specification, state management, and termination. "
                "Agents can use tools to interact with their environment.",
    )
    doc3.chunk(chunk_size=100, overlap=20)
    corpus.add_document(doc3)

    return corpus
