from __future__ import annotations

import time
from typing import Any, Callable

from agent_course.llm.base import ModelAdapter, ModelResponse, Message


class RetryableError(Exception):
    """An error that can be retried."""

    pass


class RetryPolicy:
    """Policy for retrying failed model calls."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple[type[Exception], ...] = (RetryableError,),
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    def execute(self, func: Callable[[], ModelResponse]) -> ModelResponse:
        """Execute a function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    time.sleep(delay)

        raise last_exception  # type: ignore[misc]


class RetryingModelAdapter(ModelAdapter):
    """Wrapper that adds retry logic to a model adapter."""

    def __init__(self, adapter: ModelAdapter, retry_policy: RetryPolicy | None = None) -> None:
        self._adapter = adapter
        self._retry_policy = retry_policy or RetryPolicy()

    def _call(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> ModelResponse:
        def do_call() -> ModelResponse:
            return self._adapter.complete(
                messages, tools=tools, temperature=temperature,
                max_tokens=max_tokens, **kwargs
            )

        return self._retry_policy.execute(do_call)
