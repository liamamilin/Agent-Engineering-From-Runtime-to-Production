"""Tests for safety module (M10)."""

import pytest
import time

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


class TestPermission:
    """Tests for Permission."""
    
    def test_create_permission(self):
        """Test creating a permission."""
        perm = Permission(
            resource="file:/tmp",
            level=PermissionLevel.READ,
        )
        assert perm.resource == "file:/tmp"
        assert perm.level == PermissionLevel.READ
    
    def test_permission_level_includes(self):
        """Test permission level hierarchy."""
        assert PermissionLevel.ADMIN.includes(PermissionLevel.READ)
        assert PermissionLevel.ADMIN.includes(PermissionLevel.WRITE)
        assert PermissionLevel.ADMIN.includes(PermissionLevel.EXECUTE)
        assert PermissionLevel.WRITE.includes(PermissionLevel.READ)
        assert not PermissionLevel.READ.includes(PermissionLevel.WRITE)
    
    def test_permission_allows(self):
        """Test permission allows action."""
        perm = Permission(
            resource="file:/tmp",
            level=PermissionLevel.WRITE,
        )
        assert perm.allows("read")
        assert perm.allows("write")
        assert not perm.allows("execute")
    
    def test_permission_with_conditions(self):
        """Test permission with conditions."""
        perm = Permission(
            resource="api:external",
            level=PermissionLevel.READ,
            conditions={"environment": "production"},
        )
        assert perm.allows("read", {"environment": "production"})
        assert not perm.allows("read", {"environment": "development"})
        assert not perm.allows("read", {})


class TestPermissionManager:
    """Tests for PermissionManager."""
    
    def test_grant_permission(self):
        """Test granting permission."""
        manager = PermissionManager()
        perm = Permission(resource="file:/tmp", level=PermissionLevel.READ)
        manager.grant("agent_1", perm)
        
        assert manager.check("agent_1", "file:/tmp", "read")
        assert not manager.check("agent_1", "file:/tmp", "write")
    
    def test_revoke_permission(self):
        """Test revoking permission."""
        manager = PermissionManager()
        perm = Permission(resource="file:/tmp", level=PermissionLevel.READ)
        manager.grant("agent_1", perm)
        
        assert manager.check("agent_1", "file:/tmp", "read")
        
        manager.revoke("agent_1", "file:/tmp")
        assert not manager.check("agent_1", "file:/tmp", "read")
    
    def test_wildcard_permission(self):
        """Test wildcard permission."""
        manager = PermissionManager()
        perm = Permission(resource="*", level=PermissionLevel.ADMIN)
        manager.grant("agent_1", perm)
        
        assert manager.check("agent_1", "file:/tmp", "read")
        assert manager.check("agent_1", "api:external", "write")
    
    def test_create_permission_helpers(self):
        """Test permission creation helpers."""
        manager = PermissionManager()
        
        read_perm = manager.create_read_permission("file:/tmp")
        assert read_perm.level == PermissionLevel.READ
        
        write_perm = manager.create_write_permission("file:/tmp")
        assert write_perm.level == PermissionLevel.WRITE
        
        exec_perm = manager.create_execute_permission("file:/tmp")
        assert exec_perm.level == PermissionLevel.EXECUTE
        
        admin_perm = manager.create_admin_permission("file:/tmp")
        assert admin_perm.level == PermissionLevel.ADMIN


class TestGuardrail:
    """Tests for Guardrail."""
    
    def test_create_guardrail(self):
        """Test creating a guardrail."""
        def check_length(value):
            if len(value) > 100:
                return False, "Too long"
            return True, ""
        
        guardrail = Guardrail(
            name="length_check",
            description="Maximum 100 characters",
            check_fn=check_length,
        )
        
        is_valid, error = guardrail.check("short text")
        assert is_valid
        
        is_valid, error = guardrail.check("x" * 101)
        assert not is_valid
        assert "Too long" in error


class TestGuardrailManager:
    """Tests for GuardrailManager."""
    
    def test_add_input_guardrail(self):
        """Test adding input guardrail."""
        manager = GuardrailManager()
        guardrail = InputGuardrail(
            name="test",
            description="Test guardrail",
            check_fn=lambda x: (True, ""),
        )
        manager.add_input_guardrail(guardrail)
        
        is_valid, errors = manager.check_input("test")
        assert is_valid
    
    def test_create_length_guardrail(self):
        """Test creating length guardrail."""
        manager = GuardrailManager()
        guardrail = manager.create_length_guardrail("max_length", 10, is_input=True)
        manager.add_input_guardrail(guardrail)
        
        is_valid, errors = manager.check_input("short")
        assert is_valid
        
        is_valid, errors = manager.check_input("x" * 11)
        assert not is_valid
    
    def test_create_blocked_words_guardrail(self):
        """Test creating blocked words guardrail."""
        manager = GuardrailManager()
        guardrail = manager.create_blocked_words_guardrail(
            "no_bad_words",
            ["bad", "evil"],
            is_input=True,
        )
        manager.add_input_guardrail(guardrail)
        
        is_valid, errors = manager.check_input("good text")
        assert is_valid
        
        is_valid, errors = manager.check_input("this is bad")
        assert not is_valid
    
    def test_multiple_guardrails(self):
        """Test multiple guardrails."""
        manager = GuardrailManager()
        
        length_guardrail = manager.create_length_guardrail("max_length", 10, is_input=True)
        manager.add_input_guardrail(length_guardrail)
        
        blocked_guardrail = manager.create_blocked_words_guardrail(
            "no_bad_words",
            ["bad"],
            is_input=True,
        )
        manager.add_input_guardrail(blocked_guardrail)
        
        is_valid, errors = manager.check_input("good")
        assert is_valid
        assert len(errors) == 0
        
        is_valid, errors = manager.check_input("x" * 11)
        assert not is_valid
        assert len(errors) == 1
        
        is_valid, errors = manager.check_input("bad text that is very long indeed")
        assert not is_valid
        assert len(errors) == 2


class TestBudget:
    """Tests for Budget."""
    
    def test_create_budget(self):
        """Test creating a budget."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=1000)
        assert budget.limit == 1000
        assert budget.used == 0.0
        assert budget.remaining == 1000
    
    def test_consume_budget(self):
        """Test consuming budget."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=1000)
        budget.consume(500)
        assert budget.used == 500
        assert budget.remaining == 500
    
    def test_budget_exceeded(self):
        """Test budget exceeded error."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=100)
        with pytest.raises(BudgetExceededError):
            budget.consume(101)
    
    def test_try_consume(self):
        """Test try_consume without exception."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=100)
        assert budget.try_consume(50)
        assert budget.used == 50
        assert not budget.try_consume(51)
        assert budget.used == 50  # Not consumed
    
    def test_budget_utilization(self):
        """Test budget utilization."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=100)
        budget.consume(50)
        assert budget.utilization == 0.5
    
    def test_budget_reset(self):
        """Test budget reset."""
        budget = Budget(budget_type=BudgetType.TOKENS, limit=100)
        budget.consume(50)
        budget.reset()
        assert budget.used == 0.0


class TestBudgetManager:
    """Tests for BudgetManager."""
    
    def test_create_budget(self):
        """Test creating budget."""
        manager = BudgetManager()
        budget = manager.create_budget("agent_1", BudgetType.TOKENS, 1000)
        assert budget.limit == 1000
    
    def test_consume_budget(self):
        """Test consuming budget."""
        manager = BudgetManager()
        manager.create_budget("agent_1", BudgetType.TOKENS, 1000)
        manager.consume("agent_1", BudgetType.TOKENS, 500)
        
        budget = manager.get_budget("agent_1", BudgetType.TOKENS)
        assert budget.used == 500
    
    def test_check_budget(self):
        """Test checking budget."""
        manager = BudgetManager()
        manager.create_budget("agent_1", BudgetType.TOKENS, 100)
        
        # Initially, budget is valid
        assert manager.check_budget("agent_1", BudgetType.TOKENS)
        
        # Consume some budget
        manager.consume("agent_1", BudgetType.TOKENS, 50)
        assert manager.check_budget("agent_1", BudgetType.TOKENS)
        
        # Consume more, up to the limit
        manager.consume("agent_1", BudgetType.TOKENS, 50)
        # Budget is at limit, but not exceeded (used == limit, not > limit)
        assert manager.check_budget("agent_1", BudgetType.TOKENS)
        
        # Try to consume more than remaining (should fail)
        success = manager.try_consume("agent_1", BudgetType.TOKENS, 1)
        assert not success
        
        # Budget is still at limit, not exceeded
        assert manager.check_budget("agent_1", BudgetType.TOKENS)
    
    def test_create_budget_helpers(self):
        """Test budget creation helpers."""
        manager = BudgetManager()
        
        token_budget = manager.create_token_budget("agent_1", 1000)
        assert token_budget.budget_type == BudgetType.TOKENS
        
        step_budget = manager.create_step_budget("agent_1", 10)
        assert step_budget.budget_type == BudgetType.STEPS
        
        time_budget = manager.create_time_budget("agent_1", 60.0)
        assert time_budget.budget_type == BudgetType.TIME
        
        cost_budget = manager.create_cost_budget("agent_1", 10.0)
        assert cost_budget.budget_type == BudgetType.COST


class TestRetryPolicy:
    """Tests for RetryPolicy."""
    
    def test_successful_execution(self):
        """Test successful execution without retry."""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        result = policy.execute(lambda: "success")
        assert result == "success"
    
    def test_retry_on_failure(self):
        """Test retry on failure."""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        
        call_count = 0
        def failing_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Failed")
            return "success"
        
        result = policy.execute(failing_fn)
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test max retries exceeded."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        
        def always_failing():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            policy.execute(always_failing)


class TestTimeoutPolicy:
    """Tests for TimeoutPolicy."""
    
    def test_successful_execution(self):
        """Test successful execution within timeout."""
        policy = TimeoutPolicy(timeout_seconds=1.0)
        result = policy.execute(lambda: "success")
        assert result == "success"
    
    def test_timeout_exceeded(self):
        """Test timeout exceeded."""
        policy = TimeoutPolicy(timeout_seconds=0.1)
        
        def slow_fn():
            time.sleep(1.0)
            return "success"
        
        with pytest.raises(TimeoutError):
            policy.execute(slow_fn)


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
        
        result = breaker.call(lambda: "success")
        assert result == "success"
    
    def test_open_after_failures(self):
        """Test circuit opens after failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_fn():
            raise ValueError("Failed")
        
        for _ in range(3):
            try:
                breaker.call(failing_fn)
            except ValueError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        with pytest.raises(Exception, match="Circuit breaker is open"):
            breaker.call(lambda: "success")
    
    def test_reset(self):
        """Test circuit breaker reset."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_fn():
            raise ValueError("Failed")
        
        for _ in range(3):
            try:
                breaker.call(failing_fn)
            except ValueError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED


class TestReliabilityManager:
    """Tests for ReliabilityManager."""
    
    def test_execute_with_retry(self):
        """Test execute with retry."""
        manager = ReliabilityManager()
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        manager.set_retry_policy("agent_1", policy)
        
        call_count = 0
        def failing_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Failed")
            return "success"
        
        result = manager.execute_with_retry("agent_1", failing_fn)
        assert result == "success"
    
    def test_execute_without_policy(self):
        """Test execute without policy."""
        manager = ReliabilityManager()
        result = manager.execute_with_retry("agent_1", lambda: "success")
        assert result == "success"
