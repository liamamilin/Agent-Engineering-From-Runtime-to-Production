from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agent_course.retrieval.corpus import Corpus, Chunk
from agent_course.retrieval.evidence import Evidence


@dataclass
class SearchResult:
    """A search result with score."""

    evidence: Evidence
    score: float
    rank: int = 0


class SearchEngine:
    """Simple keyword-based search engine."""

    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus
        self._index: dict[str, list[Chunk]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Build inverted index from corpus."""
        chunks = self._corpus.get_all_chunks()

        for chunk in chunks:
            # Simple tokenization
            words = re.findall(r'\w+', chunk.content.lower())
            for word in set(words):  # Unique words in chunk
                if word not in self._index:
                    self._index[word] = []
                self._index[word].append(chunk)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Search for chunks matching query."""
        # Tokenize query
        query_words = re.findall(r'\w+', query.lower())

        # Score chunks
        scores: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}

        for word in query_words:
            if word in self._index:
                for chunk in self._index[word]:
                    if chunk.id not in scores:
                        scores[chunk.id] = 0.0
                        chunk_map[chunk.id] = chunk
                    scores[chunk.id] += 1.0

        # Normalize scores
        max_score = max(scores.values()) if scores else 1.0
        for chunk_id in scores:
            scores[chunk_id] /= max_score

        # Sort by score
        sorted_chunks = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        # Convert to SearchResult
        results = []
        for rank, (chunk_id, score) in enumerate(sorted_chunks, 1):
            chunk = chunk_map[chunk_id]
            doc = self._corpus.get_document(chunk.document_id)

            evidence = Evidence(
                id=f"evidence_{rank}",
                content=chunk.content,
                source=doc.title if doc else "unknown",
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                score=score,
            )

            results.append(SearchResult(
                evidence=evidence,
                score=score,
                rank=rank,
            ))

        return results

    def search_with_reranking(
        self,
        query: str,
        top_k: int = 5,
        rerank_top_n: int = 10,
    ) -> list[SearchResult]:
        """Search with simple reranking based on exact phrase match."""
        # Initial search
        results = self.search(query, top_k=rerank_top_n)

        # Rerank based on exact phrase match
        query_lower = query.lower()
        for result in results:
            if query_lower in result.evidence.content.lower():
                result.score += 0.5  # Boost exact matches

        # Re-sort
        results.sort(key=lambda x: x.score, reverse=True)

        # Update ranks and limit
        for i, result in enumerate(results[:top_k], 1):
            result.rank = i

        return results[:top_k]
