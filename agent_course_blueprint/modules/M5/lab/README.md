# Lab — M5 Context Engineering

## Objective

构建一个 budget-aware context builder，支持优先级选择和压缩。

## Starting State

`reference_agent/src/agent_course/context/` 已有基础实现。

## Task

1. 创建 BudgetContextBuilder
2. 构建包含多个来源的上下文
3. 检查选择日志
4. 测试 budget 溢出行为

## Required API / Interfaces

```python
from agent_course.context import (
    BudgetContextBuilder, ContextItem, ContextPriority,
    TokenBudget, PrioritySelector, TruncationCompactor
)
```

## Step-by-Step Requirements

1. 创建 builder，设置 max_tokens=1000
2. 创建 task 和 state
3. 添加多个 tool results 到 state
4. 构建上下文
5. 检查 selection_log
6. 验证 CRITICAL 项总是被选中

## Tests to Pass

```bash
pytest modules/M5/lab/tests/
```

## Expected Failure Cases

1. 超过 budget 应该触发压缩或丢弃
2. CRITICAL 项不应该被丢弃

## Reflection Questions

1. 为什么 Context 不等于 State？
2. 如何判断哪些信息应该被包含在上下文中？
3. 压缩策略如何影响 Agent 性能？
