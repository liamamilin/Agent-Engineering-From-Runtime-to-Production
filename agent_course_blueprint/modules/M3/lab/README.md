# Lab — M3 Agent Runtime

## Objective

构建一个完整的 Agent，使用 FakeModel 和内置工具执行任务。

## Starting State

`reference_agent/` 已包含 core、llm、tools、runtime 模块。

## Task

1. 创建一个 Agent，配置 FakeModel 和内置工具
2. 运行一个需要工具调用的任务
3. 检查 trace 和终止原因
4. 测试不同的终止条件

## Required API / Interfaces

```python
from agent_course.core import TaskSpec, Observation
from agent_course.llm import FakeModel, ModelResponse
from agent_course.tools import create_builtin_tools
from agent_course.runtime import Agent
```

## Step-by-Step Requirements

1. 创建 FakeModel，配置工具调用和最终答案
2. 创建工具注册表
3. 创建 Agent
4. 运行任务
5. 检查 result.success、result.output、result.termination_reason
6. 检查 result.trace

## Tests to Pass

```bash
pytest modules/M3/lab/tests/
```

## Expected Failure Cases

1. 达到 max_steps 应该终止
2. 模型返回空响应应该失败
3. 工具执行错误应该被记录

## Reflection Questions

1. 在你的 Agent 中，哪些组件是确定性的，哪些是概率性的？
2. 如果模型幻觉了一个不存在的工具，会发生什么？
3. 如何从 trace 中重建整个运行过程？
