# Exercises — M10

## Exercise 1: Permission System

实现一个权限系统，支持条件权限：

```python
class ConditionalPermissionManager(PermissionManager):
    def check_with_conditions(
        self,
        agent_id: str,
        resource: str,
        action: str,
        context: dict[str, Any],
    ) -> bool:
        """Check permission with context conditions.
        
        Requirements:
        - Support time-based conditions (e.g., only during business hours)
        - Support location-based conditions (e.g., only from specific IP)
        - Support role-based conditions (e.g., only for admin users)
        """
        # 你的实现
        pass
```

**问题**：
1. 如何评估复杂的条件组合？
2. 如何处理条件冲突？
3. 如何审计权限检查？

---

## Exercise 2: Advanced Guardrails

实现一个高级 guardrail，支持上下文感知：

```python
class ContextAwareGuardrail(Guardrail):
    def __init__(self, name: str, context_rules: list[dict]):
        """Initialize with context-aware rules.
        
        Args:
            name: Guardrail name.
            context_rules: List of rules with conditions.
        """
        # 你的实现
        pass
    
    def check(self, value: Any, context: dict[str, Any] | None = None) -> tuple[bool, str]:
        """Check value with context awareness."""
        # 你的实现
        pass
```

**问题**：
1. 如何根据上下文动态调整规则？
2. 如何处理上下文缺失的情况？
3. 如何测试上下文感知的 guardrails？

---

## Exercise 3: Budget Prediction

实现一个预算预测系统：

```python
class BudgetPredictor:
    def predict_token_usage(self, task: TaskSpec, history: list[dict]) -> int:
        """Predict token usage for a task.
        
        Requirements:
        - Use historical data to predict
        - Consider task complexity
        - Provide confidence interval
        """
        # 你的实现
        pass
    
    def should_proceed(self, task: TaskSpec, budget: Budget) -> tuple[bool, str]:
        """Check if task should proceed given budget."""
        # 你的实现
        pass
```

**问题**：
1. 如何从历史数据中学习？
2. 如何处理新类型的任务？
3. 如何平衡预测准确性和保守性？

---

## Exercise 4: Smart Retry

实现一个智能重试策略：

```python
class SmartRetryPolicy(RetryPolicy):
    def __init__(self, error_strategies: dict[type[Exception], dict]):
        """Initialize with error-specific strategies.
        
        Args:
            error_strategies: Map of exception type to retry strategy.
        """
        # 你的实现
        pass
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if should retry based on exception type."""
        # 你的实现
        pass
    
    def get_delay(self, exception: Exception, attempt: int) -> float:
        """Get delay based on exception type."""
        # 你的实现
        pass
```

**问题**：
1. 如何区分可重试和不可重试的错误？
2. 如何为不同类型的错误设置不同的退避策略？
3. 如何防止重试风暴？
