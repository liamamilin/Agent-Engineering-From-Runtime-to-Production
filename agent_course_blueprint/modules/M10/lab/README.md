# Lab — M10 Safety, Reliability & Resource Control

## Objective

构建一个安全和可靠性框架，演示权限控制、guardrails、预算管理和可靠性机制。

## Starting State

`reference_agent/src/agent_course/safety/` 已有基础实现。

## Task

1. 实现权限系统，控制 agent 对资源的访问
2. 实现 guardrails，验证和过滤输入输出
3. 实现预算管理，控制资源消耗
4. 实现可靠性机制，包括重试、超时和断路器
5. 测试安全和可靠性功能

## Required API / Interfaces

```python
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
```

## Step-by-Step Requirements

1. 创建权限管理器，授予和检查权限
2. 测试不同权限级别（READ, WRITE, EXECUTE, ADMIN）
3. 测试条件权限
4. 创建 guardrail 管理器，添加输入和输出 guardrails
5. 测试长度限制、敏感词过滤等 guardrails
6. 创建预算管理器，设置 token、step、time 预算
7. 测试预算消耗和超限
8. 创建可靠性管理器，设置重试、超时和断路器策略
9. 测试重试机制、超时处理和断路器状态转换

## Tests to Pass

```bash
pytest modules/M10/lab/tests/
```

## Expected Failure Cases

1. 权限不足时应该拒绝操作
2. Guardrail 检查失败时应该拒绝输入/输出
3. 预算超限时应该抛出 BudgetExceededError
4. 断路器打开时应该拒绝请求
5. 超时应该抛出 TimeoutError

## Reflection Questions

1. 如何平衡安全性和可用性？
2. 如何设计有效的 guardrails？
3. 如何预测和防止预算超限？
4. 如何选择合适的重试策略？
5. 如何监控和告警安全和可靠性问题？
