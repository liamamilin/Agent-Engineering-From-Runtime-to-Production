from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True)
class ToolParameter:
    """A parameter in a tool schema."""

    name: str
    type: ParameterType
    description: str = ""
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        return schema


@dataclass(frozen=True)
class ToolSchema:
    """Schema definition for a tool."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    requires_permission: bool = False
    idempotent: bool = True

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def get_parameter(self, name: str) -> ToolParameter | None:
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
