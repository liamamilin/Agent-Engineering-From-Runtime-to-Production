# M3 — State, Control Loop & Termination

## Learning Objectives

By the end of this module, the learner can:

- 实现显式的 Agent 控制循环（control loop）
- 理解 State 与消息历史的区别
- 实现多种终止条件（termination conditions）
- 跟踪每次状态转移（state transition）
- 处理重试和回退（retry/fallback）
- 解释为什么需要确定性控制器包裹概率性策略

## 1. Engineering Problem

有了 Model 和 Tools，我们还需要一个**控制器**来协调它们。这个控制器需要：

1. **维护状态**：跟踪任务进度、工具结果、预算使用
2. **驱动循环**：反复执行 observe -> decide -> act -> transition
3. **判断终止**：何时停止运行
4. **处理异常**：错误、超时、预算耗尽

没有显式控制器，Agent 行为会变得不可预测、不可调试。

## 2. Mental Model

### 2.1 The Control Loop

Agent 的核心是一个显式的控制循环：

```text
                    +------------------+
                    |     TaskSpec     |
                    +--------+---------+
                             |
                             v
+------------+       +-------+--------+       +-------------+
| Observation|------>| Context Builder |<----->|    State    |
+------------+       +-------+--------+       +------+------+
                              |                       ^
                              v                       |
                       +------+--------+              |
                       |    Policy     |              |
                       |   (Model)     |              |
                       +------+--------+              |
                              | Decision              |
                              v                       |
                       +------+--------+              |
                       | Tool Executor |--------------+
                       +------+--------+  Transition
                              |
                              v
                        Environment
```

### 2.2 State vs Messages

| 概念 | 定义 | 特征 |
|------|------|------|
| Messages | 对话历史 | 序列化的、面向模型的 |
| State | 运行时信息 | 结构化的、面向任务的 |

State 包含：
- 任务进度
- 工具结果
- 计划
- 证据
- 预算使用情况
- 状态标记

Messages 只是 State 的一种视图，用于与模型交互。

### 2.3 Termination as First-Class Output

终止原因（termination reason）是 Agent 运行的一等输出：

- `success`: 任务成功完成
- `failed`: 任务失败
- `max_steps`: 达到最大步数
- `budget_exceeded`: 预算耗尽
- `final_decision`: 模型决定结束
- `human_stop`: 人类停止

## 3. Runtime Walkthrough

```python
# Agent 控制循环的完整流程

def run(task: TaskSpec) -> AgentRunResult:
    state = AgentState(task=task)
    trace = Trace()
    observation = None

    while True:
        # 1. Build context
        messages = context_builder.build(task, state, observation)

        # 2. Decide
        decision = policy.decide(messages)

        # 3. Execute action
        if decision.kind == "tool":
            result = executor.execute(decision.name, decision.arguments)
            observation = Observation.from_tool(decision.name, result)
        else:
            observation = None

        # 4. Transition
        state = transition(state, observation, decision, result)

        # 5. Record trace
        trace.add_step(...)

        # 6. Check termination
        should_stop, reason = termination.should_stop(task, state)
        if should_stop:
            return AgentRunResult(
                success=reason == "success",
                output=state.final_output,
                termination_reason=reason,
                trace=trace,
            )
```

## 4. Minimal Implementation

### 4.1 ContextBuilder

```python
class ContextBuilder:
    def build(self, task, state, observation, tools) -> list[Message]:
        messages = [Message.system(self._system_prompt)]
        messages.append(Message.user(f"Task: {task.goal}"))
        # Add relevant state and observation
        return messages
```

### 4.2 ModelPolicy

```python
class ModelPolicy:
    def decide(self, task, state, observation, tools) -> Decision:
        messages = self._context_builder.build(task, state, observation, tools)
        response = self._model.complete(messages, tools=tools)
        return self._parse_response(response)
```

### 4.3 Agent

```python
class Agent:
    def run(self, task: TaskSpec) -> AgentRunResult:
        state = AgentState(task=task)
        trace = Trace()
        observation = None

        while True:
            decision = self._policy.decide(task, state, observation, self._tools)

            if decision.kind == "tool":
                result = self._executor.execute(decision.name, decision.arguments)
                observation = Observation.from_tool(decision.name, result.output)
            else:
                observation = None

            state = Transition.apply(state, observation, decision, result)
            trace.add_step(...)

            should_stop, reason = self._termination.should_stop(task, state)
            if should_stop:
                return AgentRunResult(...)
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Control | 死循环 | Agent 反复调用同一工具 |
| Control | 过早终止 | 达到 max_steps 但任务未完成 |
| Control | 状态丢失 | 工具结果没有正确记录到 State |
| Transition | 状态更新错误 | 成功结果被忽略 |
| Termination | 条件不明确 | 无法判断任务是否成功 |

**工程规则**：
1. 总是记录 trace
2. 总是暴露终止原因
3. 用确定性代码包裹概率性决策
4. State 是单一事实来源

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加 context 压缩**：当历史太长时压缩
2. **添加 budget 跟踪**：跟踪 token、时间、成本
3. **添加 human checkpoint**：在关键步骤请求人类确认
4. **添加 resume**：从 checkpoint 恢复运行
5. **添加 parallel execution**：并行执行独立的工具调用

## 7. Lab

构建一个完整的 Agent，支持：
- 工具调用循环
- 状态跟踪
- 多种终止条件
- Trace 记录

见 `lab/README.md`。

## 8. Evaluation

- 完整的工具使用运行在离线模式下执行
- Trace 显示每次状态转移
- 最大步数终止被测试
- 成功终止被测试
- 失败终止被测试

## 9. What Changed in Our Agent?

本模块添加了 `runtime/` 子包：

- `context_builder.py`: ContextBuilder
- `policy.py`: ModelPolicy
- `agent.py`: Agent, AgentRunResult

这些组件将 Model、Tools、State、Termination 连接成一个完整的 Agent 运行时。

## 10. Summary

- Agent 的核心是显式的控制循环
- State 是结构化的运行时信息，不是消息历史
- Termination 是一等输出，必须显式暴露
- 用确定性控制器包裹概率性策略
- Trace 用于调试和评估
- 每个步骤都可以回答：观察了什么、决定什么、执行了什么、状态如何变化
