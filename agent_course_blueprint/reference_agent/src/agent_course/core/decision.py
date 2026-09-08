from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Decision:
    """A typed runtime choice produced by the policy."""

    kind: Literal["tool", "ask_user", "final", "fail"]
    name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    content: Any = None
    reason: str | None = None

    @classmethod
    def call_tool(cls, name: str, arguments: dict[str, Any] | None = None) -> Decision:
        return cls(kind="tool", name=name, arguments=arguments or {})

    @classmethod
    def ask_user(cls, question: str) -> Decision:
        return cls(kind="ask_user", content=question)

    @classmethod
    def final_answer(cls, content: Any) -> Decision:
        return cls(kind="final", content=content)

    @classmethod
    def fail(cls, reason: str) -> Decision:
        return cls(kind="fail", reason=reason)
