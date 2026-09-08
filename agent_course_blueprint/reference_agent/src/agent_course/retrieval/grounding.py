from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_course.retrieval.evidence import Evidence, EvidenceStore


@dataclass
class Claim:
    """A claim that may be supported by evidence."""

    text: str
    evidence_ids: list[str] = field(default_factory=list)
    supported: bool | None = None  # None = not checked
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class GroundingChecker:
    """Checks if claims are supported by evidence."""

    def __init__(self, evidence_store: EvidenceStore) -> None:
        self._evidence_store = evidence_store

    def check_claim(self, claim: Claim) -> Claim:
        """Check if a claim is supported by its attached evidence."""
        if not claim.evidence_ids:
            claim.supported = False
            claim.confidence = 0.0
            return claim

        # Check each piece of evidence
        supporting_count = 0
        total_count = 0

        for evidence_id in claim.evidence_ids:
            evidence = self._evidence_store.get(evidence_id)
            if evidence:
                total_count += 1
                if self._supports(evidence, claim.text):
                    supporting_count += 1

        if total_count == 0:
            claim.supported = False
            claim.confidence = 0.0
        else:
            claim.confidence = supporting_count / total_count
            claim.supported = claim.confidence >= 0.5

        return claim

    def check_claims(self, claims: list[Claim]) -> list[Claim]:
        """Check multiple claims."""
        return [self.check_claim(claim) for claim in claims]

    def _supports(self, evidence: Evidence, claim_text: str) -> bool:
        """Check if evidence supports a claim (simple keyword overlap)."""
        # Simple heuristic: check keyword overlap
        evidence_words = set(evidence.content.lower().split())
        claim_words = set(claim_text.lower().split())

        # Remove stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        evidence_words -= stop_words
        claim_words -= stop_words

        if not claim_words:
            return False

        overlap = len(evidence_words & claim_words)
        overlap_ratio = overlap / len(claim_words)

        return overlap_ratio >= 0.3  # At least 30% keyword overlap

    def get_unsupported_claims(self, claims: list[Claim]) -> list[Claim]:
        """Get claims that are not supported."""
        return [c for c in claims if c.supported is False]

    def get_supported_claims(self, claims: list[Claim]) -> list[Claim]:
        """Get claims that are supported."""
        return [c for c in claims if c.supported is True]

    def summary(self, claims: list[Claim]) -> dict[str, Any]:
        """Generate a summary of grounding status."""
        total = len(claims)
        supported = len(self.get_supported_claims(claims))
        unsupported = len(self.get_unsupported_claims(claims))
        unchecked = total - supported - unsupported

        return {
            "total_claims": total,
            "supported": supported,
            "unsupported": unsupported,
            "unchecked": unchecked,
            "grounding_rate": supported / total if total > 0 else 0.0,
        }
