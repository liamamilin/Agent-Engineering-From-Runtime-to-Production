from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Observation:
    """New information available to the runtime at a particular step."""

    kind: str
    payload: Any

    @classmethod
    def from_user(cls, content: str) -> Observation:
        return cls(kind="user", payload=content)

    @classmethod
    def from_tool(cls, tool_name: str, result: Any) -> Observation:
        return cls(kind="tool", payload={"tool": tool_name, "result": result})

    @classmethod
    def from_error(cls, error: str) -> Observation:
        return cls(kind="error", payload=error)

    @classmethod
    def from_event(cls, event: str, data: Any = None) -> Observation:
        return cls(kind="event", payload={"event": event, "data": data})
