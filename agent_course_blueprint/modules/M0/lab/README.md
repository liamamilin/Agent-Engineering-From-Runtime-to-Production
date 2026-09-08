# Lab — M0 Runtime Trace

## Objective

使用 `reference_agent` 中的核心类型，手动追踪一次完整的 Agent 运行。

## Starting State

`reference_agent/` 已安装，核心类型可用：

```python
from agent_course.core import TaskSpec, Observation, AgentState, Decision, Transition, TerminationPolicy
```

## Task

模拟一次 Agent 运行，手动执行每个步骤，记录 Trace。

## Step-by-Step Requirements

1. 创建一个 TaskSpec
2. 初始化 AgentState
3. 模拟三步运行：
   - Step 1: 用户输入观察 -> 决策调用工具 -> 工具结果 -> 状态更新
   - Step 2: 工具结果观察 -> 决策调用另一个工具 -> 工具结果 -> 状态更新
   - Step 3: 最终观察 -> 最终答案决策 -> 状态更新
4. 检查终止条件
5. 记录每步的 Trace

## Tests to Pass

```bash
pytest modules/M0/lab/tests/
```

## Reflection Questions

1. 在你的追踪中，哪些组件是确定性的，哪些是概率性的？
2. 如果 Model 返回了错误的工具名称，故障发生在哪个层级？
3. 如果达到 max_steps 但任务未完成，Termination 应该返回什么？
