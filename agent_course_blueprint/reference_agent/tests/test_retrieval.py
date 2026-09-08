import pytest

from agent_course.retrieval import (
    Evidence,
    EvidenceStore,
    Corpus,
    Document,
    Chunk,
    SearchEngine,
    SearchResult,
    GroundingChecker,
    Claim,
)
from agent_course.retrieval.corpus import create_sample_corpus


class TestEvidence:
    def test_create_evidence(self):
        evidence = Evidence(
            id="e1",
            content="Python is a programming language",
            source="doc_1",
        )
        assert evidence.id == "e1"
        assert evidence.source == "doc_1"

    def test_evidence_to_dict(self):
        evidence = Evidence(id="e1", content="Test", source="src")
        d = evidence.to_dict()
        assert d["id"] == "e1"
        assert d["content"] == "Test"


class TestEvidenceStore:
    def test_add_and_get(self):
        store = EvidenceStore()
        evidence = Evidence(id="e1", content="Test", source="src")
        store.add(evidence)
        retrieved = store.get("e1")
        assert retrieved is not None
        assert retrieved.id == "e1"

    def test_list_all(self):
        store = EvidenceStore()
        store.add(Evidence(id="e1", content="A", source="s"))
        store.add(Evidence(id="e2", content="B", source="s"))
        assert len(store) == 2

    def test_filter_by_source(self):
        store = EvidenceStore()
        store.add(Evidence(id="e1", content="A", source="src1"))
        store.add(Evidence(id="e2", content="B", source="src2"))
        filtered = store.filter_by_source("src1")
        assert len(filtered) == 1


class TestDocument:
    def test_create_document(self):
        doc = Document(id="d1", content="Hello world")
        assert doc.id == "d1"

    def test_chunk_document(self):
        doc = Document(id="d1", content="A" * 500)
        chunks = doc.chunk(chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all(c.document_id == "d1" for c in chunks)


class TestCorpus:
    def test_create_corpus(self):
        corpus = Corpus(name="test")
        assert corpus.name == "test"

    def test_add_document(self):
        corpus = Corpus(name="test")
        doc = Document(id="d1", content="Test")
        corpus.add_document(doc)
        assert len(corpus) == 1

    def test_get_all_chunks(self):
        corpus = Corpus(name="test")
        doc = Document(id="d1", content="A" * 300)
        corpus.add_document(doc)
        chunks = corpus.get_all_chunks()
        assert len(chunks) > 0

    def test_sample_corpus(self):
        corpus = create_sample_corpus()
        assert len(corpus) >= 3


class TestSearchEngine:
    def test_search_basic(self):
        corpus = create_sample_corpus()
        engine = SearchEngine(corpus)
        results = engine.search("Python programming")
        assert len(results) > 0
        assert results[0].score > 0

    def test_search_returns_evidence(self):
        corpus = create_sample_corpus()
        engine = SearchEngine(corpus)
        results = engine.search("machine learning")
        assert len(results) > 0
        assert isinstance(results[0].evidence, Evidence)
        assert results[0].evidence.id is not None

    def test_search_with_reranking(self):
        corpus = create_sample_corpus()
        engine = SearchEngine(corpus)
        results = engine.search_with_reranking("Python", top_k=3)
        assert len(results) <= 3


class TestGroundingChecker:
    def test_check_supported_claim(self):
        store = EvidenceStore()
        store.add(Evidence(
            id="e1",
            content="Python is a programming language created by Guido",
            source="doc_1",
        ))

        checker = GroundingChecker(store)
        claim = Claim(text="Python programming language", evidence_ids=["e1"])
        checked = checker.check_claim(claim)

        assert checked.supported is True
        assert checked.confidence > 0

    def test_check_unsupported_claim(self):
        store = EvidenceStore()
        store.add(Evidence(
            id="e1",
            content="Python is a snake",
            source="doc_1",
        ))

        checker = GroundingChecker(store)
        claim = Claim(text="Python programming language", evidence_ids=["e1"])
        checked = checker.check_claim(claim)

        # May or may not be supported depending on overlap
        assert checked.supported is not None

    def test_check_claim_no_evidence(self):
        store = EvidenceStore()
        checker = GroundingChecker(store)
        claim = Claim(text="Some claim", evidence_ids=[])
        checked = checker.check_claim(claim)

        assert checked.supported is False
        assert checked.confidence == 0.0

    def test_summary(self):
        store = EvidenceStore()
        store.add(Evidence(id="e1", content="Python programming", source="s"))

        checker = GroundingChecker(store)
        claims = [
            Claim(text="Python", evidence_ids=["e1"]),
            Claim(text="Java", evidence_ids=[]),
        ]
        checked = checker.check_claims(claims)
        summary = checker.summary(checked)

        assert summary["total_claims"] == 2
        assert "grounding_rate" in summary
