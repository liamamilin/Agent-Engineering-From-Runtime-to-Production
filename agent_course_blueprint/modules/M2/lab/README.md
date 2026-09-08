# Lab — M2 Tool System

## Objective

实现一个工具系统，支持 schema 定义、参数验证、权限控制和执行。

## Starting State

`reference_agent/src/agent_course/tools/` 已有基础实现。

## Task

1. 使用 create_builtin_tools 创建工具注册表
2. 执行 search 工具，验证结果
3. 执行 calculator 工具，验证计算
4. 尝试执行 write_file 工具，验证权限控制
5. 尝试无效参数，验证错误处理

## Required API / Interfaces

```python
from agent_course.tools import (
    ToolRegistry, ToolExecutor, ToolResult,
    create_builtin_tools
)
```

## Step-by-Step Requirements

1. 创建工具注册表
2. 列出所有可用工具
3. 执行 search 工具
4. 执行 calculator 工具
5. 尝试无权限执行 write_file
6. 授予权限后再次执行 write_file
7. 尝试无效参数

## Tests to Pass

```bash
pytest modules/M2/lab/tests/
```

## Expected Failure Cases

1. 缺少必需参数应该返回错误
2. 参数类型错误应该返回错误
3. 无权限执行写操作应该返回错误

## Reflection Questions

1. 为什么写操作需要显式权限？
2. 工具结果如何成为 Observation？
3. 如果模型幻觉了一个不存在的工具，会发生什么？
