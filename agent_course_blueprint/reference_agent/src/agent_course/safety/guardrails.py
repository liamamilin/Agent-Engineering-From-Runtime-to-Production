"""Guardrails for input/output validation and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Guardrail:
    """Base guardrail for validation."""
    
    name: str
    description: str
    check_fn: Callable[[Any], tuple[bool, str]]  # Returns (is_valid, error_message)
    
    def check(self, value: Any) -> tuple[bool, str]:
        """Check if value passes the guardrail.
        
        Args:
            value: The value to check.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        return self.check_fn(value)


@dataclass
class InputGuardrail(Guardrail):
    """Guardrail for validating agent inputs."""
    
    pass


@dataclass
class OutputGuardrail(Guardrail):
    """Guardrail for validating agent outputs."""
    
    pass


class GuardrailManager:
    """Manages guardrails for agents."""
    
    def __init__(self) -> None:
        """Initialize guardrail manager."""
        self._input_guardrails: list[InputGuardrail] = []
        self._output_guardrails: list[OutputGuardrail] = []
    
    def add_input_guardrail(self, guardrail: InputGuardrail) -> None:
        """Add an input guardrail.
        
        Args:
            guardrail: The guardrail to add.
        """
        self._input_guardrails.append(guardrail)
    
    def add_output_guardrail(self, guardrail: OutputGuardrail) -> None:
        """Add an output guardrail.
        
        Args:
            guardrail: The guardrail to add.
        """
        self._output_guardrails.append(guardrail)
    
    def check_input(self, value: Any) -> tuple[bool, list[str]]:
        """Check input against all input guardrails.
        
        Args:
            value: The input value to check.
            
        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []
        for guardrail in self._input_guardrails:
            is_valid, error_msg = guardrail.check(value)
            if not is_valid:
                errors.append(f"{guardrail.name}: {error_msg}")
        
        return len(errors) == 0, errors
    
    def check_output(self, value: Any) -> tuple[bool, list[str]]:
        """Check output against all output guardrails.
        
        Args:
            value: The output value to check.
            
        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors = []
        for guardrail in self._output_guardrails:
            is_valid, error_msg = guardrail.check(value)
            if not is_valid:
                errors.append(f"{guardrail.name}: {error_msg}")
        
        return len(errors) == 0, errors
    
    def create_length_guardrail(
        self,
        name: str,
        max_length: int,
        is_input: bool = True,
    ) -> Guardrail:
        """Create a length guardrail.
        
        Args:
            name: Guardrail name.
            max_length: Maximum allowed length.
            is_input: True for input guardrail, False for output.
            
        Returns:
            Guardrail that checks length.
        """
        def check_length(value: Any) -> tuple[bool, str]:
            if isinstance(value, str):
                if len(value) > max_length:
                    return False, f"Length {len(value)} exceeds maximum {max_length}"
            return True, ""
        
        guardrail = Guardrail(
            name=name,
            description=f"Maximum length: {max_length}",
            check_fn=check_length,
        )
        
        if is_input:
            return InputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
        else:
            return OutputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
    
    def create_pattern_guardrail(
        self,
        name: str,
        pattern: str,
        is_input: bool = True,
    ) -> Guardrail:
        """Create a pattern guardrail.
        
        Args:
            name: Guardrail name.
            pattern: Regex pattern to match.
            is_input: True for input guardrail, False for output.
            
        Returns:
            Guardrail that checks pattern.
        """
        import re
        
        def check_pattern(value: Any) -> tuple[bool, str]:
            if isinstance(value, str):
                if not re.search(pattern, value):
                    return False, f"Does not match pattern: {pattern}"
            return True, ""
        
        guardrail = Guardrail(
            name=name,
            description=f"Must match pattern: {pattern}",
            check_fn=check_pattern,
        )
        
        if is_input:
            return InputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
        else:
            return OutputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
    
    def create_blocked_words_guardrail(
        self,
        name: str,
        blocked_words: list[str],
        is_input: bool = True,
    ) -> Guardrail:
        """Create a blocked words guardrail.
        
        Args:
            name: Guardrail name.
            blocked_words: List of blocked words.
            is_input: True for input guardrail, False for output.
            
        Returns:
            Guardrail that checks for blocked words.
        """
        def check_blocked(value: Any) -> tuple[bool, str]:
            if isinstance(value, str):
                value_lower = value.lower()
                for word in blocked_words:
                    if word.lower() in value_lower:
                        return False, f"Contains blocked word: {word}"
            return True, ""
        
        guardrail = Guardrail(
            name=name,
            description=f"Blocked words: {', '.join(blocked_words)}",
            check_fn=check_blocked,
        )
        
        if is_input:
            return InputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
        else:
            return OutputGuardrail(
                name=guardrail.name,
                description=guardrail.description,
                check_fn=guardrail.check_fn,
            )
