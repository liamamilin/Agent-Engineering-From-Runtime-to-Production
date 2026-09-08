"""Lab tests for M10 Safety, Reliability & Resource Control."""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.safety import (
    Permission,
    PermissionLevel,
    PermissionManager,
    Guardrail,
    InputGuardrail,
    OutputGuardrail,
    GuardrailManager,
    Budget,
    BudgetManager,
    BudgetExceededError,
    RetryPolicy,
    TimeoutPolicy,
    CircuitBreaker,
    ReliabilityManager,
)
from agent_course.safety.budgets import BudgetType
from agent_course.safety.reliability import CircuitState


def test_permission_system():
    """Test permission system with different levels."""
    manager = PermissionManager()
    
    # Grant READ permission
    read_perm = Permission(
        resource="file:/data",
        level=PermissionLevel.READ,
    )
    manager.grant("agent_1", read_perm)
    
    # Should allow READ
    assert manager.check("agent_1", "file:/data", "read")
    
    # Should not allow WRITE
    assert not manager.check("agent_1", "file:/data", "write")
    
    # Grant WRITE permission
    write_perm = Permission(
        resource="file:/data",
        level=PermissionLevel.WRITE,
    )
    manager.grant("agent_1", write_perm)
    
    # Should now allow WRITE
    assert manager.check("agent_1", "file:/data", "write")


def test_conditional_permission():
    """Test permission with conditions."""
    manager = PermissionManager()
    
    # Grant permission with condition
    perm = Permission(
        resource="api:external",
        level=PermissionLevel.READ,
        conditions={"environment": "production"},
    )
    manager.grant("agent_1", perm)
    
    # Should allow with correct condition
    assert manager.check("agent_1", "api:external", "read", {"environment": "production"})
    
    # Should not allow with wrong condition
    assert not manager.check("agent_1", "api:external", "read", {"environment": "development"})
    
    # Should not allow without condition
    assert not manager.check("agent_1", "api:external", "read", {})


def test_guardrail_length_limit():
    """Test guardrail with length limit."""
    manager = GuardrailManager()
    
    # Add length guardrail
    length_guardrail = manager.create_length_guardrail(
        "max_length",
        max_length=100,
        is_input=True,
    )
    manager.add_input_guardrail(length_guardrail)
    
    # Should pass short input
    is_valid, errors = manager.check_input("Short input")
    assert is_valid
    assert len(errors) == 0
    
    # Should fail long input
    long_input = "x" * 101
    is_valid, errors = manager.check_input(long_input)
    assert not is_valid
    assert len(errors) > 0


def test_guardrail_blocked_words():
    """Test guardrail with blocked words."""
    manager = GuardrailManager()
    
    # Add blocked words guardrail
    blocked_guardrail = manager.create_blocked_words_guardrail(
        "no_bad_words",
        blocked_words=["evil", "hack"],
        is_input=True,
    )
    manager.add_input_guardrail(blocked_guardrail)
    
    # Should pass clean input
    is_valid, errors = manager.check_input("Good input")
    assert is_valid
    
    # Should fail input with blocked word
    is_valid, errors = manager.check_input("This is evil")
    assert not is_valid
    assert len(errors) > 0


def test_budget_management():
    """Test budget management and consumption."""
    manager = BudgetManager()
    
    # Create token budget
    budget = manager.create_budget("agent_1", BudgetType.TOKENS, limit=1000)
    assert budget.limit == 1000
    assert budget.used == 0
    
    # Consume budget
    manager.consume("agent_1", BudgetType.TOKENS, 500)
    assert budget.used == 500
    
    # Check budget
    assert manager.check_budget("agent_1", BudgetType.TOKENS)
    
    # Consume more
    manager.consume("agent_1", BudgetType.TOKENS, 400)
    assert budget.used == 900
    
    # Try to consume over limit
    with pytest.raises(BudgetExceededError):
        manager.consume("agent_1", BudgetType.TOKENS, 200)


def test_budget_try_consume():
    """Test try_consume without exception."""
    manager = BudgetManager()
    manager.create_budget("agent_1", BudgetType.STEPS, limit=10)
    
    # Try to consume within limit
    success = manager.try_consume("agent_1", BudgetType.STEPS, 5)
    assert success
    
    # Try to consume over limit
    success = manager.try_consume("agent_1", BudgetType.STEPS, 10)
    assert not success
    
    # Budget should not be exceeded
    assert manager.check_budget("agent_1", BudgetType.STEPS)


def test_retry_policy():
    """Test retry policy with exponential backoff."""
    policy = RetryPolicy(
        max_retries=3,
        base_delay=0.01,
        max_delay=1.0,
        exponential_base=2.0,
    )
    
    # Test successful execution
    call_count = 0
    def successful_fn():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = policy.execute(successful_fn)
    assert result == "success"
    assert call_count == 1
    
    # Test retry on failure
    call_count = 0
    def failing_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = policy.execute(failing_fn)
    assert result == "success"
    assert call_count == 3


def test_retry_max_retries():
    """Test retry policy with max retries exceeded."""
    policy = RetryPolicy(max_retries=2, base_delay=0.01)
    
    def always_failing():
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        policy.execute(always_failing)


def test_timeout_policy():
    """Test timeout policy."""
    policy = TimeoutPolicy(timeout_seconds=0.1)
    
    # Test successful execution within timeout
    def quick_fn():
        return "success"
    
    result = policy.execute(quick_fn)
    assert result == "success"
    
    # Test timeout
    def slow_fn():
        time.sleep(1.0)
        return "success"
    
    with pytest.raises(TimeoutError):
        policy.execute(slow_fn)


def test_circuit_breaker():
    """Test circuit breaker state transitions."""
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=0.1,
    )
    
    # Initially CLOSED
    assert breaker.state == CircuitState.CLOSED
    
    # Cause failures
    def failing_fn():
        raise ValueError("Failure")
    
    for _ in range(3):
        try:
            breaker.call(failing_fn)
        except ValueError:
            pass
    
    # Should be OPEN after threshold
    assert breaker.state == CircuitState.OPEN
    
    # Should reject calls when OPEN
    with pytest.raises(Exception, match="Circuit breaker is open"):
        breaker.call(lambda: "success")
    
    # Wait for recovery timeout
    time.sleep(0.2)
    
    # Should transition to HALF_OPEN
    # (This happens on next call attempt)
    try:
        breaker.call(lambda: "success")
    except:
        pass
    
    # After successful call, should be CLOSED
    assert breaker.state == CircuitState.CLOSED


def test_reliability_manager():
    """Test reliability manager with multiple mechanisms."""
    manager = ReliabilityManager()
    
    # Set retry policy
    retry_policy = RetryPolicy(max_retries=2, base_delay=0.01)
    manager.set_retry_policy("agent_1", retry_policy)
    
    # Execute with retry only (timeout can cause threading issues in tests)
    call_count = 0
    def flaky_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"
    
    result = manager.execute_with_retry("agent_1", flaky_fn)
    assert result == "success"
    assert call_count == 2


def test_permission_wildcard():
    """Test wildcard permission."""
    manager = PermissionManager()
    
    # Grant wildcard permission
    perm = Permission(
        resource="*",
        level=PermissionLevel.ADMIN,
    )
    manager.grant("agent_1", perm)
    
    # Should allow any resource
    assert manager.check("agent_1", "file:/any", "read")
    assert manager.check("agent_1", "api:any", "write")
    assert manager.check("agent_1", "db:any", "execute")


def test_multiple_guardrails():
    """Test multiple guardrails together."""
    manager = GuardrailManager()
    
    # Add multiple guardrails
    length_guardrail = manager.create_length_guardrail("max_length", 50, is_input=True)
    manager.add_input_guardrail(length_guardrail)
    
    blocked_guardrail = manager.create_blocked_words_guardrail(
        "no_bad_words",
        ["evil"],
        is_input=True,
    )
    manager.add_input_guardrail(blocked_guardrail)
    
    # Should pass both checks
    is_valid, errors = manager.check_input("Good input")
    assert is_valid
    assert len(errors) == 0
    
    # Should fail length check
    is_valid, errors = manager.check_input("x" * 51)
    assert not is_valid
    assert len(errors) == 1
    
    # Should fail blocked words check
    is_valid, errors = manager.check_input("This is evil")
    assert not is_valid
    assert len(errors) == 1
    
    # Should fail both checks
    is_valid, errors = manager.check_input("x" * 51 + " evil")
    assert not is_valid
    assert len(errors) == 2
