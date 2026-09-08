# Lab — M8 Planning, Workflows & Human Control

## Objective

构建一个支持两种控制架构的 Agent，演示 reactive loop、explicit planning 和 workflow 的执行差异。

## Starting State

`reference_agent/src/agent_course/planning/` 已有基础实现。

## Task

1. 创建一个任务，分别用 reactive loop 和 explicit planning 执行
2. 比较两种架构的执行轨迹
3. 创建一个带审批的 workflow
4. 演示人类审批暂停和恢复执行
5. 演示 replanning 应对步骤失败

## Required API / Interfaces

```python
from agent_course.planning import (
    Plan, PlanStep, PlanStatus,
    Planner, ReplanningTrigger,
    Workflow, WorkflowState,
    ApprovalCheckpoint, ApprovalStatus,
    HumanApprovalPolicy,
)
from agent_course.planning.workflow import create_simple_workflow, create_approval_workflow
from agent_course.planning.approval import ApprovalManager
```

## Step-by-Step Requirements

1. 创建一个简单的任务（如"搜索并总结"）
2. 使用 Planner 创建 explicit plan
3. 执行 plan，记录每个步骤
4. 使用 reactive loop 执行相同任务
5. 比较两种执行方式的轨迹差异
6. 创建带审批的 workflow
7. 执行到审批点，暂停
8. 模拟人类审批，继续执行
9. 模拟步骤失败，触发 replanning

## Tests to Pass

```bash
pytest modules/M8/lab/tests/
```

## Expected Failure Cases

1. 计划步骤失败时应该触发 replanning
2. 未获审批时 workflow 应该暂停
3. 拒绝审批时 workflow 应该失败

## Reflection Questions

1. 在你的实验中，哪种架构更适合这个任务？为什么？
2. 如何决定一个操作是否需要人类审批？
3. Replanning 的开销和收益如何平衡？
