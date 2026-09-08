# Lab — M1 Model Adapter

## Objective

实现一个 ModelAdapter，支持消息、工具调用、结构化输出和重试。

## Starting State

`reference_agent/src/agent_course/llm/` 已有基础实现。

## Task

1. 扩展 FakeModel 支持模式匹配
2. 实现结构化输出解析
3. 实现重试策略
4. 编写测试

## Required API / Interfaces

```python
from agent_course.llm import (
    ModelAdapter, ModelResponse, Message,
    FakeModel, StructuredOutput, SchemaValidator,
    RetryPolicy, RetryableError
)
```

## Step-by-Step Requirements

1. 创建 FakeModel 实例，配置预定义响应
2. 发送包含工具的消息，验证工具调用被正确返回
3. 解析包含 JSON 的模型响应
4. 验证结构化输出符合 schema
5. 测试重试逻辑处理临时错误

## Tests to Pass

```bash
pytest modules/M1/lab/tests/
```

## Expected Failure Cases

1. 无效 JSON 应该抛出 ValueError
2. 缺少必需字段应该验证失败
3. 超过重试次数应该抛出异常

## Reflection Questions

1. 为什么 ModelAdapter 是一个抽象接口而不是具体类？
2. 为什么需要 FakeModel？它解决了什么问题？
3. 重试策略如何影响 Agent 的总延迟？
