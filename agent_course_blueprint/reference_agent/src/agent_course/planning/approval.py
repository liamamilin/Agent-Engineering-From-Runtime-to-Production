"""Human approval system for side-effecting actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalCheckpoint:
    """A checkpoint requiring human approval before proceeding."""
    
    id: str
    action: str
    arguments: dict[str, Any]
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: str | None = None
    resolved_by: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def approve(self, approved_by: str = "human", notes: str | None = None) -> None:
        """Approve the checkpoint."""
        self.status = ApprovalStatus.APPROVED
        self.resolved_at = datetime.now().isoformat()
        self.resolved_by = approved_by
        self.notes = notes
    
    def reject(self, rejected_by: str = "human", notes: str | None = None) -> None:
        """Reject the checkpoint."""
        self.status = ApprovalStatus.REJECTED
        self.resolved_at = datetime.now().isoformat()
        self.rejected_by = rejected_by
        self.notes = notes
    
    def is_pending(self) -> bool:
        """Check if approval is still pending."""
        return self.status == ApprovalStatus.PENDING
    
    def is_approved(self) -> bool:
        """Check if approval was granted."""
        return self.status == ApprovalStatus.APPROVED
    
    def is_rejected(self) -> bool:
        """Check if approval was rejected."""
        return self.status == ApprovalStatus.REJECTED


@dataclass
class HumanApprovalPolicy:
    """Policy for determining when human approval is required."""
    
    require_approval_for: list[str] = field(default_factory=list)  # Action names
    auto_approve_safe: bool = True  # Auto-approve read-only actions
    timeout_seconds: int | None = None  # Approval timeout
    
    def requires_approval(self, action: str, arguments: dict[str, Any]) -> bool:
        """Determine if an action requires approval.
        
        Args:
            action: The action name.
            arguments: The action arguments.
        
        Returns:
            True if approval is required, False otherwise.
        """
        # Check if action is in the require list
        if action in self.require_approval_for:
            return True
        
        # Auto-approve safe actions if enabled
        if self.auto_approve_safe and self._is_safe_action(action, arguments):
            return False
        
        # Default: require approval for unknown actions
        return True
    
    def _is_safe_action(self, action: str, arguments: dict[str, Any]) -> bool:
        """Determine if an action is safe (read-only).
        
        This is a simple heuristic. In production, this should be more sophisticated.
        """
        safe_keywords = ["read", "get", "search", "list", "check", "validate"]
        return any(keyword in action.lower() for keyword in safe_keywords)
    
    def create_checkpoint(
        self,
        checkpoint_id: str,
        action: str,
        arguments: dict[str, Any],
        reason: str,
    ) -> ApprovalCheckpoint:
        """Create an approval checkpoint.
        
        Args:
            checkpoint_id: Unique identifier.
            action: The action requiring approval.
            arguments: The action arguments.
            reason: Why approval is needed.
        
        Returns:
            A new ApprovalCheckpoint.
        """
        return ApprovalCheckpoint(
            id=checkpoint_id,
            action=action,
            arguments=arguments,
            reason=reason,
        )


class ApprovalManager:
    """Manages approval checkpoints and their resolution."""
    
    def __init__(self, policy: HumanApprovalPolicy | None = None) -> None:
        """Initialize approval manager.
        
        Args:
            policy: The approval policy. If None, uses default policy.
        """
        self._policy = policy or HumanApprovalPolicy()
        self._checkpoints: dict[str, ApprovalCheckpoint] = {}
    
    def request_approval(
        self,
        checkpoint_id: str,
        action: str,
        arguments: dict[str, Any],
        reason: str,
    ) -> ApprovalCheckpoint:
        """Request approval for an action.
        
        Args:
            checkpoint_id: Unique identifier.
            action: The action requiring approval.
            arguments: The action arguments.
            reason: Why approval is needed.
        
        Returns:
            The created ApprovalCheckpoint.
        """
        checkpoint = self._policy.create_checkpoint(
            checkpoint_id, action, arguments, reason
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint
    
    def get_checkpoint(self, checkpoint_id: str) -> ApprovalCheckpoint | None:
        """Get a checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)
    
    def approve(self, checkpoint_id: str, approved_by: str = "human", notes: str | None = None) -> bool:
        """Approve a checkpoint.
        
        Args:
            checkpoint_id: The checkpoint ID.
            approved_by: Who approved it.
            notes: Optional notes.
        
        Returns:
            True if approved, False if checkpoint not found.
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint and checkpoint.is_pending():
            checkpoint.approve(approved_by, notes)
            return True
        return False
    
    def reject(self, checkpoint_id: str, rejected_by: str = "human", notes: str | None = None) -> bool:
        """Reject a checkpoint.
        
        Args:
            checkpoint_id: The checkpoint ID.
            rejected_by: Who rejected it.
            notes: Optional notes.
        
        Returns:
            True if rejected, False if checkpoint not found.
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint and checkpoint.is_pending():
            checkpoint.reject(rejected_by, notes)
            return True
        return False
    
    def get_pending_checkpoints(self) -> list[ApprovalCheckpoint]:
        """Get all pending checkpoints."""
        return [cp for cp in self._checkpoints.values() if cp.is_pending()]
    
    def get_all_checkpoints(self) -> list[ApprovalCheckpoint]:
        """Get all checkpoints."""
        return list(self._checkpoints.values())
