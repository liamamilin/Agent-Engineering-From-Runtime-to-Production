"""Evidence and Claim models for Project Understanding Agent"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class Evidence:
    """Evidence collected during project exploration"""
    id: str
    source: str  # file path or tool name
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Claim:
    """A claim about the project, backed by evidence"""
    id: str
    statement: str
    confidence: float  # 0.0 to 1.0
    evidence_ids: list[str] = field(default_factory=list)
    category: str = "general"  # architecture, dependencies, patterns, etc.
    verified: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "category": self.category,
            "verified": self.verified,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def is_supported(self) -> bool:
        """Check if claim has supporting evidence"""
        return len(self.evidence_ids) > 0 and self.confidence > 0.5


@dataclass
class EvidenceStore:
    """Storage for evidence and claims"""
    evidence: dict[str, Evidence] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    
    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to store"""
        self.evidence[evidence.id] = evidence
    
    def add_claim(self, claim: Claim) -> None:
        """Add claim to store"""
        self.claims[claim.id] = claim
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID"""
        return self.evidence.get(evidence_id)
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Get claim by ID"""
        return self.claims.get(claim_id)
    
    def get_claims_by_category(self, category: str) -> list[Claim]:
        """Get all claims in a category"""
        return [c for c in self.claims.values() if c.category == category]
    
    def get_unsupported_claims(self) -> list[Claim]:
        """Get claims without sufficient evidence"""
        return [c for c in self.claims.values() if not c.is_supported()]
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of evidence and claims"""
        return {
            "total_evidence": len(self.evidence),
            "total_claims": len(self.claims),
            "supported_claims": len([c for c in self.claims.values() if c.is_supported()]),
            "unsupported_claims": len(self.get_unsupported_claims()),
            "categories": list(set(c.category for c in self.claims.values())),
        }
