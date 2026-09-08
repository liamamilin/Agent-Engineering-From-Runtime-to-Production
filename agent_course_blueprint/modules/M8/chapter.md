# M8 — Planning, Workflows & Human Control

## Learning Objectives

By the end of this module, the learner can:

- 区分 reactive loop 和 explicit planning 两种控制架构
- 实现 plan 表示和执行，支持步骤依赖
- 实现 workflow/state machine 用于确定性控制流
- 实现 human approval checkpoint 用于高风险操作
- 理解何时使用 workflow 比 agentic freedom 更合适
- 实现 replanning 机制应对计划失败

## 1. Engineering Problem

Agent 需要决定如何执行复杂任务，但面临以下选择：

1. **Reactive vs Deliberative**：是逐步反应还是预先规划？
2. **Freedom vs Control**：是给 Agent 自由还是限制在预定义流程中？
3. **Automation vs Human-in-the-loop**：是全自动还是需要人类审批？
4. **Rigidity vs Flexibility**：是严格执行计划还是允许动态调整？

我们需要多种控制架构，根据任务特性选择合适的方案。

## 2. Mental Model

### 2.1 Two Control Architectures

```text
┌─────────────────────────────────────────────────────────────┐
│  Reactive Loop (M3 已实现)                                  │
│  - 每步动态决策                                             │
│  - 灵活但不可预测                                           │
│  - 适合探索性任务                                           │
├─────────────────────────────────────────────────────────────┤
│  Explicit Planning (本模块)                                 │
│  - 预先制定计划                                             │
│  - 可预测但可能僵化                                         │
│  - 适合结构化任务                                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Plan Representation

Plan 由有序步骤组成，支持依赖关系：

```text
Plan: "Research and write report"
├── Step 1: Search for information (no dependencies)
├── Step 2: Analyze findings (depends on Step 1)
├── Step 3: Write draft (depends on Step 2)
└── Step 4: Review and edit (depends on Step 3)
```

### 2.3 Workflow/State Machine

Workflow 是确定性的状态机，用于严格控制流程：

```text
States: initial → running → waiting_approval → completed
                          ↓
                        failed

Transitions:
- initial → running: start_task
- running → waiting_approval: request_approval
- waiting_approval → completed: execute_approved (if approved)
- waiting_approval → failed: handle_rejection (if rejected)
```

### 2.4 Human Approval Checkpoints

某些高风险操作需要人类审批：

```text
Agent wants to: delete_file("/important/data.txt")
    ↓
Create ApprovalCheckpoint
    ↓
Wait for human decision
    ↓
    ├─ Approved → Execute action
    └─ Rejected → Skip or alternative
```

### 2.5 When to Use Which Architecture

| 任务特性 | 推荐架构 | 原因 |
|----------|----------|------|
| 探索性、开放式 | Reactive Loop | 需要灵活性 |
| 结构化、可预测 | Explicit Planning | 需要可预测性 |
| 高风险操作 | Workflow + Approval | 需要严格控制 |
| 简单、快速 | Reactive Loop | 规划开销不值得 |
| 合规性要求 | Workflow | 需要审计轨迹 |

## 3. Runtime Walkthrough

### 3.1 Reactive Loop (Review)

```python
# M3 已实现的 reactive loop
while not done:
    observation = observe()
    context = build_context(state, observation)
    decision = policy.decide(context)  # 每步动态决策
    result = execute(decision)
    state = transition(state, decision, result)
```

### 3.2 Explicit Planning

```python
# 创建计划
planner = Planner()
plan = planner.create_plan(
    plan_id="plan1",
    goal="Research and write report",
    steps_spec=[
        {"id": "search", "description": "Search", "action": "search", "arguments": {...}},
        {"id": "analyze", "description": "Analyze", "action": "analyze", "dependencies": ["search"]},
        {"id": "write", "description": "Write", "action": "write", "dependencies": ["analyze"]},
    ],
)

# 执行计划
while not plan.is_completed():
    next_step = plan.get_next_step(plan.get_completed_steps())
    if next_step is None:
        break
    
    # 检查是否需要审批
    if next_step.requires_approval:
        checkpoint = approval_manager.request_approval(...)
        # 等待人类审批
        while checkpoint.is_pending():
            time.sleep(1)
        
        if checkpoint.is_rejected():
            next_step.mark_failed("Rejected by human")
            continue
    
    # 执行步骤
    next_step.mark_in_progress()
    result = execute_tool(next_step.action, next_step.arguments)
    next_step.mark_completed(result)
    
    # 检查是否需要 replan
    should_replan, trigger, reason = planner.should_replan(plan, results)
    if should_replan:
        plan = planner.replan(plan, trigger, reason, plan.get_completed_steps())
```

### 3.3 Workflow Execution

```python
# 创建带审批的 workflow
workflow = create_approval_workflow("wf1", "Data Processing")

# 执行 workflow
while not workflow.is_completed():
    if workflow.is_waiting_approval():
        # 等待人类审批
        approval = wait_for_approval()
        workflow.update_context("approved", approval)
    
    available = workflow.get_available_transitions()
    if not available:
        break
    
    # 执行转换
    transition_result = workflow.execute_transition(0)
    action = transition_result["action"]
    
    # 执行对应的工具
    result = execute_tool(action, transition_result["arguments"])
```

## 4. Minimal Implementation

### 4.1 Plan and PlanStep

```python
@dataclass
class PlanStep:
    id: str
    description: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    status: PlanStatus = PlanStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    requires_approval: bool = False
    
    def is_ready(self, completed_steps: set[str]) -> bool:
        return (self.status == PlanStatus.PENDING and
                all(dep in completed_steps for dep in self.dependencies))

@dataclass
class Plan:
    id: str
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    
    def get_next_step(self, completed_steps: set[str]) -> PlanStep | None:
        for step in self.steps:
            if step.is_ready(completed_steps):
                return step
        return None
```

### 4.2 Planner

```python
class Planner:
    def create_plan(self, plan_id: str, goal: str, steps_spec: list[dict]) -> Plan:
        plan = Plan(id=plan_id, goal=goal)
        for spec in steps_spec:
            step = PlanStep(
                id=spec["id"],
                description=spec["description"],
                action=spec["action"],
                arguments=spec.get("arguments", {}),
                dependencies=spec.get("dependencies", []),
            )
            plan.add_step(step)
        return plan
    
    def replan(self, original: Plan, trigger: ReplanningTrigger, 
               reason: str, completed: set[str]) -> Plan:
        # 保留已完成的步骤，移除失败的步骤
        new_plan = Plan(id=f"{original.id}_replan", goal=original.goal)
        for step in original.steps:
            if step.id in completed:
                new_plan.add_step(copy_completed_step(step))
            elif step.status != PlanStatus.FAILED:
                new_plan.add_step(copy_pending_step(step))
        return new_plan
```

### 4.3 Workflow

```python
@dataclass
class Workflow:
    id: str
    current_state: str
    transitions: list[WorkflowTransition] = field(default_factory=list)
    
    def execute_transition(self, transition_id: int) -> dict[str, Any]:
        available = self.get_available_transitions()
        transition = available[transition_id]
        self.current_state = transition.to_state
        return {"action": transition.action, "new_state": self.current_state}

@dataclass
class WorkflowTransition:
    from_state: str
    to_state: str
    action: str
    condition: Callable[[dict], bool] | None = None
```

### 4.4 ApprovalCheckpoint

```python
@dataclass
class ApprovalCheckpoint:
    id: str
    action: str
    arguments: dict[str, Any]
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    def approve(self, approved_by: str) -> None:
        self.status = ApprovalStatus.APPROVED
    
    def reject(self, rejected_by: str) -> None:
        self.status = ApprovalStatus.REJECTED
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Control | 计划不可行 | 步骤依赖循环 |
| Control | 计划僵化 | 无法应对意外情况 |
| Control | 死锁 | 没有可用的转换 |
| Transition | 状态不一致 | 转换条件判断错误 |
| Control | 审批超时 | 人类未及时响应 |
| Control | 审批滥用 | 过多操作需要审批 |
| Control | 无限 replan | 每次 replan 都失败 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 计划应该有明确的完成条件
2. Workflow 应该有超时机制
3. 审批请求应该有清晰的理由
4. Replanning 应该有最大次数限制
5. 记录执行轨迹用于审计

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加并行步骤**：支持无依赖步骤并行执行
2. **添加条件分支**：根据执行结果选择不同路径
3. **添加审批超时**：自动处理未响应的审批
4. **添加计划模板**：预定义常见任务的计划
5. **添加可视化**：图形化展示计划和执行状态

## 7. Lab

构建一个支持两种控制架构的 Agent，演示：
- 同一任务在 reactive loop 和 explicit planning 下的执行
- Workflow 带审批 checkpoint
- Replanning 应对步骤失败

见 `lab/README.md`。

## 8. Evaluation

- 同一 benchmark 任务在两种架构下运行
- Trace 显示控制差异
- Human approval 可以暂停和恢复
- Replanning 有明确的触发条件

## 9. What Changed in Our Agent?

本模块添加了 `planning/` 子包：

- `plan.py`: Plan, PlanStep, PlanStatus
- `planner.py`: Planner, ReplanningTrigger
- `workflow.py`: Workflow, WorkflowState, WorkflowTransition
- `approval.py`: ApprovalCheckpoint, ApprovalStatus, HumanApprovalPolicy, ApprovalManager

这些组件让 Agent 可以选择不同的控制架构，支持显式规划和人类审批。

## 10. Summary

- Reactive loop 灵活但不可预测
- Explicit planning 可预测但可能僵化
- Workflow 提供确定性控制流
- Human approval 用于高风险操作
- Replanning 应对计划失败
- 根据任务特性选择合适的架构
- 记录执行轨迹用于审计和调试
