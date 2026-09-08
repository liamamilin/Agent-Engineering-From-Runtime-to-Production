import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.retrieval import (
    Corpus, SearchEngine, EvidenceStore,
    GroundingChecker, Claim
)
from agent_course.retrieval.corpus import create_sample_corpus


def test_corpus_creation():
    """Test that sample corpus is created."""
    corpus = create_sample_corpus()
    assert len(corpus) >= 3


def test_search_returns_results():
    """Test that search returns results."""
    corpus = create_sample_corpus()
    engine = SearchEngine(corpus)
    results = engine.search("Python")
    assert len(results) > 0


def test_evidence_has_source():
    """Test that evidence preserves source identity."""
    corpus = create_sample_corpus()
    engine = SearchEngine(corpus)
    results = engine.search("machine learning")

    for result in results:
        assert result.evidence.source is not None
        assert result.evidence.document_id is not None


def test_evidence_store():
    """Test that evidence can be stored and retrieved."""
    corpus = create_sample_corpus()
    engine = SearchEngine(corpus)
    results = engine.search("Python")

    store = EvidenceStore()
    for result in results:
        store.add(result.evidence)

    assert len(store) > 0
    assert store.get(results[0].evidence.id) is not None


def test_claim_grounding():
    """Test that claims can be checked for grounding."""
    corpus = create_sample_corpus()
    engine = SearchEngine(corpus)
    results = engine.search("Python programming")

    store = EvidenceStore()
    for result in results:
        store.add(result.evidence)

    checker = GroundingChecker(store)

    # Create a claim with evidence
    claim = Claim(
        text="Python is a programming language",
        evidence_ids=[results[0].evidence.id],
    )

    checked = checker.check_claim(claim)
    assert checked.supported is not None


def test_unsupported_claim():
    """Test that unsupported claims are detected."""
    store = EvidenceStore()
    checker = GroundingChecker(store)

    # Claim with no evidence
    claim = Claim(text="Some random fact", evidence_ids=[])
    checked = checker.check_claim(claim)

    assert checked.supported is False
    assert checked.confidence == 0.0


def test_grounding_summary():
    """Test that grounding summary is calculated."""
    corpus = create_sample_corpus()
    engine = SearchEngine(corpus)
    results = engine.search("Python")

    store = EvidenceStore()
    for result in results:
        store.add(result.evidence)

    checker = GroundingChecker(store)

    claims = [
        Claim(text="Python programming", evidence_ids=[results[0].evidence.id]),
        Claim(text="Unknown fact", evidence_ids=[]),
    ]

    checked = checker.check_claims(claims)
    summary = checker.summary(checked)

    assert summary["total_claims"] == 2
    assert "grounding_rate" in summary
