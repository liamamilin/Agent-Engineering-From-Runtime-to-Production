from __future__ import annotations

from typing import Any

from agent_course.tools.schema import ToolSchema, ParameterType


class ValidationError(Exception):
    """Raised when tool arguments fail validation."""

    pass


class ToolValidator:
    """Validates tool arguments against schema."""

    def validate(self, schema: ToolSchema, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate arguments against tool schema.

        Returns validated arguments with defaults applied.
        Raises ValidationError if validation fails.
        """
        validated: dict[str, Any] = {}

        # Check required parameters
        for param in schema.parameters:
            if param.name in arguments:
                value = arguments[param.name]
                validated[param.name] = self._validate_type(param, value)
            elif param.required:
                raise ValidationError(f"Missing required parameter: {param.name}")
            elif param.default is not None:
                validated[param.name] = param.default

        # Check for unknown parameters
        known_params = {p.name for p in schema.parameters}
        for name in arguments:
            if name not in known_params:
                raise ValidationError(f"Unknown parameter: {name}")

        return validated

    def _validate_type(self, param: Any, value: Any) -> Any:
        """Validate and convert a parameter value."""
        expected_type = param.type

        if expected_type == ParameterType.STRING:
            if not isinstance(value, str):
                raise ValidationError(
                    f"Parameter '{param.name}' should be string, got {type(value).__name__}"
                )
            if param.enum and value not in param.enum:
                raise ValidationError(
                    f"Parameter '{param.name}' must be one of {param.enum}"
                )
            return value

        elif expected_type == ParameterType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(
                    f"Parameter '{param.name}' should be integer, got {type(value).__name__}"
                )
            return value

        elif expected_type == ParameterType.NUMBER:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValidationError(
                    f"Parameter '{param.name}' should be number, got {type(value).__name__}"
                )
            return value

        elif expected_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(
                    f"Parameter '{param.name}' should be boolean, got {type(value).__name__}"
                )
            return value

        elif expected_type == ParameterType.ARRAY:
            if not isinstance(value, list):
                raise ValidationError(
                    f"Parameter '{param.name}' should be array, got {type(value).__name__}"
                )
            return value

        elif expected_type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                raise ValidationError(
                    f"Parameter '{param.name}' should be object, got {type(value).__name__}"
                )
            return value

        return value
