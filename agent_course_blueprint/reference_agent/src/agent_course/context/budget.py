from __future__ import annotations

from dataclasses import dataclass, field


class BudgetExceededError(Exception):
    """Raised when token budget is exceeded."""

    pass


@dataclass
class TokenBudget:
    """Token budget tracker."""

    max_tokens: int
    used_tokens: int = 0
    reserved_tokens: int = 0

    @property
    def available_tokens(self) -> int:
        """Available tokens for new content."""
        return max(0, self.max_tokens - self.used_tokens - self.reserved_tokens)

    @property
    def utilization(self) -> float:
        """Budget utilization ratio."""
        if self.max_tokens == 0:
            return 0.0
        return self.used_tokens / self.max_tokens

    def allocate(self, tokens: int) -> None:
        """Allocate tokens from budget."""
        if tokens > self.available_tokens:
            raise BudgetExceededError(
                f"Cannot allocate {tokens} tokens. "
                f"Available: {self.available_tokens}, "
                f"Used: {self.used_tokens}, "
                f"Reserved: {self.reserved_tokens}"
            )
        self.used_tokens += tokens

    def reserve(self, tokens: int) -> None:
        """Reserve tokens for future use."""
        if tokens > self.available_tokens:
            raise BudgetExceededError(
                f"Cannot reserve {tokens} tokens. Available: {self.available_tokens}"
            )
        self.reserved_tokens += tokens

    def release(self, tokens: int) -> None:
        """Release reserved tokens."""
        self.reserved_tokens = max(0, self.reserved_tokens - tokens)

    def reset(self) -> None:
        """Reset budget."""
        self.used_tokens = 0
        self.reserved_tokens = 0
