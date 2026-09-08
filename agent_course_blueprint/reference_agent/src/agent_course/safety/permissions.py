"""Permission system for controlling agent actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(str, Enum):
    """Permission levels for agent actions."""
    
    NONE = "none"  # No permission
    READ = "read"  # Read-only access
    WRITE = "write"  # Write access (includes read)
    EXECUTE = "execute"  # Execute access (includes read and write)
    ADMIN = "admin"  # Full access
    
    def includes(self, other: PermissionLevel) -> bool:
        """Check if this level includes another level."""
        hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4,
        }
        return hierarchy[self] >= hierarchy[other]


@dataclass
class Permission:
    """A permission for a specific action or resource."""
    
    resource: str  # Resource identifier (e.g., "file:/tmp", "api:external")
    level: PermissionLevel
    conditions: dict[str, Any] = field(default_factory=dict)  # Additional conditions
    
    def allows(self, action: str, context: dict[str, Any] | None = None) -> bool:
        """Check if this permission allows an action.
        
        Args:
            action: The action to check (e.g., "read", "write", "execute").
            context: Additional context for condition evaluation.
            
        Returns:
            True if allowed, False otherwise.
        """
        # Map action to permission level
        action_levels = {
            "read": PermissionLevel.READ,
            "list": PermissionLevel.READ,
            "get": PermissionLevel.READ,
            "write": PermissionLevel.WRITE,
            "create": PermissionLevel.WRITE,
            "update": PermissionLevel.WRITE,
            "delete": PermissionLevel.WRITE,
            "execute": PermissionLevel.EXECUTE,
            "run": PermissionLevel.EXECUTE,
            "admin": PermissionLevel.ADMIN,
        }
        
        required_level = action_levels.get(action, PermissionLevel.NONE)
        
        if not self.level.includes(required_level):
            return False
        
        # Check conditions
        if self.conditions:
            context = context or {}
            for key, value in self.conditions.items():
                if key not in context or context[key] != value:
                    return False
        
        return True


class PermissionManager:
    """Manages permissions for agents."""
    
    def __init__(self) -> None:
        """Initialize permission manager."""
        self._permissions: dict[str, list[Permission]] = {}
    
    def grant(self, agent_id: str, permission: Permission) -> None:
        """Grant a permission to an agent.
        
        Args:
            agent_id: The agent ID.
            permission: The permission to grant.
        """
        if agent_id not in self._permissions:
            self._permissions[agent_id] = []
        self._permissions[agent_id].append(permission)
    
    def revoke(self, agent_id: str, resource: str) -> None:
        """Revoke all permissions for a resource from an agent.
        
        Args:
            agent_id: The agent ID.
            resource: The resource identifier.
        """
        if agent_id in self._permissions:
            self._permissions[agent_id] = [
                p for p in self._permissions[agent_id]
                if p.resource != resource
            ]
    
    def check(
        self,
        agent_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if an agent has permission for an action.
        
        Args:
            agent_id: The agent ID.
            resource: The resource identifier.
            action: The action to check.
            context: Additional context for condition evaluation.
            
        Returns:
            True if allowed, False otherwise.
        """
        if agent_id not in self._permissions:
            return False
        
        for permission in self._permissions[agent_id]:
            if permission.resource == resource or permission.resource == "*":
                if permission.allows(action, context):
                    return True
        
        return False
    
    def get_permissions(self, agent_id: str) -> list[Permission]:
        """Get all permissions for an agent.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            List of permissions.
        """
        return self._permissions.get(agent_id, [])
    
    def create_read_permission(self, resource: str) -> Permission:
        """Create a read-only permission.
        
        Args:
            resource: The resource identifier.
            
        Returns:
            Permission with READ level.
        """
        return Permission(resource=resource, level=PermissionLevel.READ)
    
    def create_write_permission(self, resource: str) -> Permission:
        """Create a write permission.
        
        Args:
            resource: The resource identifier.
            
        Returns:
            Permission with WRITE level.
        """
        return Permission(resource=resource, level=PermissionLevel.WRITE)
    
    def create_execute_permission(self, resource: str) -> Permission:
        """Create an execute permission.
        
        Args:
            resource: The resource identifier.
            
        Returns:
            Permission with EXECUTE level.
        """
        return Permission(resource=resource, level=PermissionLevel.EXECUTE)
    
    def create_admin_permission(self, resource: str) -> Permission:
        """Create an admin permission.
        
        Args:
            resource: The resource identifier.
            
        Returns:
            Permission with ADMIN level.
        """
        return Permission(resource=resource, level=PermissionLevel.ADMIN)
