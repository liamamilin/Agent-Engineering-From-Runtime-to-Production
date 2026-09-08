from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskSpec:
    """Defines what the run is trying to accomplish."""

    goal: str
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    max_steps: int = 20
    max_cost_usd: float | None = None
    output_contract: str | None = None
