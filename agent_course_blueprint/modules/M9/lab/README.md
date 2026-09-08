# Lab — M9 Multi-Agent Composition

## Objective

构建一个 multi-agent 系统，演示 agent-as-tool、handoff 和 supervisor/worker 模式，并与 single-agent baseline 进行比较。

## Starting State

`reference_agent/src/agent_course/composition/` 已有基础实现。

## Task

1. 创建一个 single-agent baseline 来完成复杂任务
2. 使用 agent-as-tool 模式实现相同任务
3. 使用 supervisor/worker 模式实现相同任务
4. 比较三种方式的性能和质量
5. 演示 context 隔离

## Required API / Interfaces

```python
from agent_course.composition import (
    AgentAsTool,
    Handoff,
    HandoffDecision,
    Supervisor,
    Worker,
    TaskDelegation,
    AgentMessage,
    MessageBus,
)
from agent_course.composition.handoff import HandoffPolicy, HandoffManager
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.runtime import Agent
```

## Step-by-Step Requirements

1. 创建一个 complex task（如"研究 AI 趋势并撰写报告"）
2. 使用 single agent 完成任务，记录执行时间和结果
3. 创建 research agent 和 writer agent
4. 使用 agent-as-tool 模式，让 coordinator 调用 research agent 和 writer agent
5. 使用 supervisor/worker 模式，让 supervisor 分解任务并分配给 workers
6. 比较三种方式的：
   - 执行步数
   - 结果质量
   - 执行时间
7. 演示 context 隔离：证明 worker 的内部状态不会泄漏到 supervisor

## Tests to Pass

```bash
pytest modules/M9/lab/tests/
```

## Expected Failure Cases

1. Worker 无法处理的任务应该返回失败
2. Handoff 达到最大次数应该终止
3. Context 隔离应该阻止内部状态泄漏

## Reflection Questions

1. 在你的实验中，哪种方式最适合这个任务？为什么？
2. Multi-agent 系统的开销是否值得？
3. 如何避免 context 泄漏？
4. 什么情况下 single-agent 比 multi-agent 更好？
