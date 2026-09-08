"""Budget management for resource control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BudgetExceededError(Exception):
    """Raised when a budget is exceeded."""
    
    pass


class BudgetType(str, Enum):
    """Types of budgets."""
    
    TOKENS = "tokens"
    STEPS = "steps"
    TIME = "time"  # seconds
    COST = "cost"  # USD
    API_CALLS = "api_calls"


@dataclass
class Budget:
    """A budget for a specific resource."""
    
    budget_type: BudgetType
    limit: float
    used: float = 0.0
    
    @property
    def remaining(self) -> float:
        """Get remaining budget."""
        return max(0.0, self.limit - self.used)
    
    @property
    def utilization(self) -> float:
        """Get budget utilization (0.0 to 1.0)."""
        if self.limit == 0:
            return 0.0
        return self.used / self.limit
    
    @property
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.used > self.limit
    
    def consume(self, amount: float) -> None:
        """Consume budget.
        
        Args:
            amount: Amount to consume.
            
        Raises:
            BudgetExceededError: If budget would be exceeded.
        """
        if self.used + amount > self.limit:
            raise BudgetExceededError(
                f"Budget exceeded: {self.budget_type.value} "
                f"(used={self.used}, limit={self.limit}, requested={amount})"
            )
        self.used += amount
    
    def try_consume(self, amount: float) -> bool:
        """Try to consume budget without raising exception.
        
        Args:
            amount: Amount to consume.
            
        Returns:
            True if consumed, False if would exceed.
        """
        if self.used + amount > self.limit:
            return False
        self.used += amount
        return True
    
    def reset(self) -> None:
        """Reset budget usage."""
        self.used = 0.0


class BudgetManager:
    """Manages budgets for agents."""
    
    def __init__(self) -> None:
        """Initialize budget manager."""
        self._budgets: dict[str, dict[BudgetType, Budget]] = {}
    
    def create_budget(
        self,
        agent_id: str,
        budget_type: BudgetType,
        limit: float,
    ) -> Budget:
        """Create a budget for an agent.
        
        Args:
            agent_id: The agent ID.
            budget_type: The type of budget.
            limit: The budget limit.
            
        Returns:
            The created budget.
        """
        if agent_id not in self._budgets:
            self._budgets[agent_id] = {}
        
        budget = Budget(budget_type=budget_type, limit=limit)
        self._budgets[agent_id][budget_type] = budget
        return budget
    
    def get_budget(self, agent_id: str, budget_type: BudgetType) -> Budget | None:
        """Get a budget for an agent.
        
        Args:
            agent_id: The agent ID.
            budget_type: The type of budget.
            
        Returns:
            The budget, or None if not found.
        """
        if agent_id not in self._budgets:
            return None
        return self._budgets[agent_id].get(budget_type)
    
    def consume(
        self,
        agent_id: str,
        budget_type: BudgetType,
        amount: float,
    ) -> None:
        """Consume budget for an agent.
        
        Args:
            agent_id: The agent ID.
            budget_type: The type of budget.
            amount: Amount to consume.
            
        Raises:
            BudgetExceededError: If budget would be exceeded.
        """
        budget = self.get_budget(agent_id, budget_type)
        if budget is None:
            return  # No budget means unlimited
        budget.consume(amount)
    
    def try_consume(
        self,
        agent_id: str,
        budget_type: BudgetType,
        amount: float,
    ) -> bool:
        """Try to consume budget without raising exception.
        
        Args:
            agent_id: The agent ID.
            budget_type: The type of budget.
            amount: Amount to consume.
            
        Returns:
            True if consumed, False if would exceed or no budget.
        """
        budget = self.get_budget(agent_id, budget_type)
        if budget is None:
            return True  # No budget means unlimited
        return budget.try_consume(amount)
    
    def check_budget(self, agent_id: str, budget_type: BudgetType) -> bool:
        """Check if budget is available (not exceeded).
        
        Args:
            agent_id: The agent ID.
            budget_type: The type of budget.
            
        Returns:
            True if budget is available, False if exceeded.
        """
        budget = self.get_budget(agent_id, budget_type)
        if budget is None:
            return True  # No budget means unlimited
        return not budget.is_exceeded
    
    def get_utilization(self, agent_id: str) -> dict[BudgetType, float]:
        """Get budget utilization for an agent.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            Dictionary of budget type to utilization.
        """
        if agent_id not in self._budgets:
            return {}
        
        return {
            budget_type: budget.utilization
            for budget_type, budget in self._budgets[agent_id].items()
        }
    
    def reset(self, agent_id: str) -> None:
        """Reset all budgets for an agent.
        
        Args:
            agent_id: The agent ID.
        """
        if agent_id in self._budgets:
            for budget in self._budgets[agent_id].values():
                budget.reset()
    
    def create_token_budget(self, agent_id: str, limit: int) -> Budget:
        """Create a token budget.
        
        Args:
            agent_id: The agent ID.
            limit: Token limit.
            
        Returns:
            The created budget.
        """
        return self.create_budget(agent_id, BudgetType.TOKENS, limit)
    
    def create_step_budget(self, agent_id: str, limit: int) -> Budget:
        """Create a step budget.
        
        Args:
            agent_id: The agent ID.
            limit: Step limit.
            
        Returns:
            The created budget.
        """
        return self.create_budget(agent_id, BudgetType.STEPS, limit)
    
    def create_time_budget(self, agent_id: str, limit_seconds: float) -> Budget:
        """Create a time budget.
        
        Args:
            agent_id: The agent ID.
            limit_seconds: Time limit in seconds.
            
        Returns:
            The created budget.
        """
        return self.create_budget(agent_id, BudgetType.TIME, limit_seconds)
    
    def create_cost_budget(self, agent_id: str, limit_usd: float) -> Budget:
        """Create a cost budget.
        
        Args:
            agent_id: The agent ID.
            limit_usd: Cost limit in USD.
            
        Returns:
            The created budget.
        """
        return self.create_budget(agent_id, BudgetType.COST, limit_usd)
