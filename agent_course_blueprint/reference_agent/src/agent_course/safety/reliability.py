"""Reliability mechanisms for fault tolerance."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class CircuitState(str, Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class RetryPolicy:
    """Policy for retrying failed operations."""
    
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)
    
    def execute(self, fn: Callable[[], Any]) -> Any:
        """Execute function with retry logic.
        
        Args:
            fn: Function to execute.
            
        Returns:
            Function result.
            
        Raises:
            Exception: If all retries fail.
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    time.sleep(delay)
        
        raise last_exception  # type: ignore[misc]
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if an exception should be retried.
        
        Args:
            exception: The exception to check.
            
        Returns:
            True if should retry, False otherwise.
        """
        return isinstance(exception, self.retryable_exceptions)


@dataclass
class TimeoutPolicy:
    """Policy for timing out operations."""
    
    timeout_seconds: float
    
    def execute(self, fn: Callable[[], Any]) -> Any:
        """Execute function with timeout.
        
        Args:
            fn: Function to execute.
            
        Returns:
            Function result.
            
        Raises:
            TimeoutError: If operation times out.
        """
        import threading
        
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = fn()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=self.timeout_seconds)
        
        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
        
        if exception:
            raise exception
        
        return result


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    
    def call(self, fn: Callable[[], Any]) -> Any:
        """Call function through circuit breaker.
        
        Args:
            fn: Function to call.
            
        Returns:
            Function result.
            
        Raises:
            Exception: If circuit is open or function fails.
        """
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = fn()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def reset(self) -> None:
        """Reset circuit breaker."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0.0


class ReliabilityManager:
    """Manages reliability mechanisms for agents."""
    
    def __init__(self) -> None:
        """Initialize reliability manager."""
        self._retry_policies: dict[str, RetryPolicy] = {}
        self._timeout_policies: dict[str, TimeoutPolicy] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
    
    def set_retry_policy(self, agent_id: str, policy: RetryPolicy) -> None:
        """Set retry policy for an agent.
        
        Args:
            agent_id: The agent ID.
            policy: The retry policy.
        """
        self._retry_policies[agent_id] = policy
    
    def set_timeout_policy(self, agent_id: str, policy: TimeoutPolicy) -> None:
        """Set timeout policy for an agent.
        
        Args:
            agent_id: The agent ID.
            policy: The timeout policy.
        """
        self._timeout_policies[agent_id] = policy
    
    def set_circuit_breaker(self, agent_id: str, breaker: CircuitBreaker) -> None:
        """Set circuit breaker for an agent.
        
        Args:
            agent_id: The agent ID.
            breaker: The circuit breaker.
        """
        self._circuit_breakers[agent_id] = breaker
    
    def execute_with_retry(self, agent_id: str, fn: Callable[[], Any]) -> Any:
        """Execute function with retry policy.
        
        Args:
            agent_id: The agent ID.
            fn: Function to execute.
            
        Returns:
            Function result.
        """
        policy = self._retry_policies.get(agent_id)
        if policy is None:
            return fn()
        return policy.execute(fn)
    
    def execute_with_timeout(self, agent_id: str, fn: Callable[[], Any]) -> Any:
        """Execute function with timeout policy.
        
        Args:
            agent_id: The agent ID.
            fn: Function to execute.
            
        Returns:
            Function result.
        """
        policy = self._timeout_policies.get(agent_id)
        if policy is None:
            return fn()
        return policy.execute(fn)
    
    def execute_with_circuit_breaker(self, agent_id: str, fn: Callable[[], Any]) -> Any:
        """Execute function through circuit breaker.
        
        Args:
            agent_id: The agent ID.
            fn: Function to execute.
            
        Returns:
            Function result.
        """
        breaker = self._circuit_breakers.get(agent_id)
        if breaker is None:
            return fn()
        return breaker.call(fn)
    
    def execute_with_all(
        self,
        agent_id: str,
        fn: Callable[[], Any],
    ) -> Any:
        """Execute function with all reliability mechanisms.
        
        Args:
            agent_id: The agent ID.
            fn: Function to execute.
            
        Returns:
            Function result.
        """
        # Start with the base function
        current_fn = fn
        
        # Apply timeout
        timeout_policy = self._timeout_policies.get(agent_id)
        if timeout_policy:
            def timeout_wrapper():
                return timeout_policy.execute(current_fn)
            current_fn = timeout_wrapper
        
        # Apply retry
        retry_policy = self._retry_policies.get(agent_id)
        if retry_policy:
            def retry_wrapper():
                return retry_policy.execute(current_fn)
            current_fn = retry_wrapper
        
        # Apply circuit breaker
        breaker = self._circuit_breakers.get(agent_id)
        if breaker:
            return breaker.call(current_fn)
        
        return current_fn()
