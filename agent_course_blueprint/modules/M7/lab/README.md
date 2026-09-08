# Lab — M7 Memory & Persistence

## Objective

构建一个带记忆和 checkpoint 的 Agent，支持中断恢复和记忆管理。

## Starting State

`reference_agent/src/agent_course/memory/` 已有基础实现。

## Task

1. 创建一个 Agent，配置 checkpoint store 和 memory store
2. 运行任务，定期保存 checkpoint
3. 模拟中断，从 checkpoint 恢复
4. 提取并存储记忆
5. 应用遗忘策略

## Required API / Interfaces

```python
from agent_course.memory import (
    CheckpointStore, Checkpoint,
    MemoryStore, MemoryRecord,
    MemoryWritePolicy, MemoryReadPolicy, ForgettingPolicy,
)
from agent_course.memory.store import MemoryType
```

## Step-by-Step Requirements

1. 创建 CheckpointStore 和 MemoryStore
2. 配置 write/read/forgetting policies
3. 运行 Agent 任务，每 3 步保存 checkpoint
4. 模拟中断（停止运行）
5. 从 checkpoint 恢复运行
6. 验证恢复后的状态正确
7. 提取运行中的记忆并存储
8. 检索相关记忆
9. 应用遗忘策略

## Tests to Pass

```bash
pytest modules/M7/lab/tests/
```

## Expected Failure Cases

1. Checkpoint 不存在时应该返回 None
2. 记忆被失效后不应该被检索到
3. 低重要性记忆不应该被存储

## Reflection Questions

1. Checkpoint 应该包含哪些信息？
2. 如何判断什么信息值得记住？
3. 遗忘策略如何平衡保留重要信息和清理过时信息？
