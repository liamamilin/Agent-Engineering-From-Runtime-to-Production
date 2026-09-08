from __future__ import annotations

import re
from typing import Any

from agent_course.llm.base import ModelAdapter, ModelResponse, Message


class StructuredOutput:
    """Parse and validate structured output from model responses."""

    @staticmethod
    def parse_json(content: str) -> dict[str, Any]:
        """Extract JSON from model response content."""
        import json

        content = content.strip()

        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object
        brace_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse JSON from content: {content[:100]}...")


class SchemaValidator:
    """Validate structured output against a schema."""

    def __init__(self, required_fields: dict[str, type]) -> None:
        self._required_fields = required_fields

    def validate(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate data against schema.

        Returns (is_valid, list_of_errors).
        """
        errors = []

        for field_name, field_type in self._required_fields.items():
            if field_name not in data:
                errors.append(f"Missing required field: {field_name}")
            elif not isinstance(data[field_name], field_type):
                errors.append(
                    f"Field '{field_name}' should be {field_type.__name__}, "
                    f"got {type(data[field_name]).__name__}"
                )

        return len(errors) == 0, errors

    @classmethod
    def for_decision(cls) -> SchemaValidator:
        """Create a validator for agent decisions."""
        return cls({
            "kind": str,
            "name": str,
            "arguments": dict,
        })

    @classmethod
    def for_answer(cls) -> SchemaValidator:
        """Create a validator for final answers."""
        return cls({
            "answer": str,
            "confidence": (int, float),
        })
