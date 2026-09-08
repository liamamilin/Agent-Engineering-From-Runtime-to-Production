# M9 — Delegation, Multi-Agent & Protocols

## Learning Objectives

By the end of this module, the learner can:

- 理解 composition before multi-agent 原则
- 实现 agent-as-tool 模式，将一个 Agent 作为另一个 Agent 的工具
- 实现 handoff 模式，在 Agent 之间转移控制权
- 实现 supervisor/worker 模式，协调多个专业 Agent
- 理解 shared vs isolated context 的权衡
- 评估 multi-agent 系统相比 single-agent 的优劣

## 1. Engineering Problem

单个 Agent 的能力有限，面对复杂任务时可能需要：

1. **专业化分工**：不同 Agent 擅长不同任务
2. **并行处理**：多个 Agent 同时处理不同子任务
3. **权限分离**：不同 Agent 有不同权限级别
4. **故障隔离**：一个 Agent 失败不影响其他 Agent

但 multi-agent 系统也带来挑战：
- 通信开销
- 协调复杂性
- 上下文泄漏风险
- 成本增加

## 2. Mental Model

### 2.1 Composition Before Multi-Agent

在引入多个 Agent 之前，先考虑是否可以通过 composition 解决：

```text
Single Agent with Tools (preferred if possible)
    ↓
Single Agent with Agent-as-Tool (composition)
    ↓
Multi-Agent System (only when necessary)
```

**原则**：如果单个 Agent 加上工具就能解决问题，就不要引入 multi-agent。

### 2.2 Agent-as-Tool Pattern

将一个 Agent 包装成工具，供另一个 Agent 调用：

```text
Coordinator Agent
    ↓ (calls as tool)
Specialized Agent
    ↓ (executes task)
Returns result to Coordinator
```

**优点**：
- Coordinator 保持控制权
- Specialized Agent 可以专注自己的领域
- 接口简单，易于理解

### 2.3 Handoff Pattern

Agent 之间转移控制权：

```text
Agent A (handling task)
    ↓ (determines Agent B is better suited)
Handoff to Agent B
    ↓
Agent B (continues task)
```

**适用场景**：
- 任务需要不同专业知识
- Agent 达到能力边界
- 需要不同权限级别

### 2.4 Supervisor/Worker Pattern

Supervisor 协调多个 Worker：

```text
Supervisor Agent
    ↓ (decomposes task)
    ├→ Worker 1 (research)
    ├→ Worker 2 (analysis)
    └→ Worker 3 (writing)
    ↓ (aggregates results)
Final result
```

**优点**：
- 清晰的责任分离
- 可以并行执行
- 易于扩展

### 2.5 Communication Patterns

Agent 之间如何通信：

| 模式 | 特征 | 适用场景 |
|------|------|----------|
| Direct Call | 同步，阻塞 | Agent-as-tool |
| Message Passing | 异步，非阻塞 | Handoff, Supervisor/Worker |
| Shared State | 共享内存 | 紧密协作 |
| Event Bus | 发布/订阅 | 松耦合系统 |

### 2.6 Context Isolation

Multi-agent 系统中的重要问题：

```text
Agent A Context          Agent B Context
┌─────────────┐          ┌─────────────┐
│ Task Info   │          │ Task Info   │
│ History     │  ──→     │ History     │
│ Evidence    │  handoff │ Evidence    │
│ Internal    │          │ Internal    │
│ State       │          │ State       │
└─────────────┘          └─────────────┘
     ↑                        ↑
     └──────── Shared ────────┘
         Context (minimal)
```

**原则**：只传递必要的上下文，避免内部状态泄漏。

## 3. Runtime Walkthrough

### 3.1 Agent-as-Tool Execution

```python
# 1. 创建 specialized agent
specialized_model = FakeModel(responses=[...])
specialized_agent = Agent(model=specialized_model)

# 2. 包装为 tool
agent_tool = AgentAsTool(
    agent=specialized_agent,
    name="research_agent",
    description="Research agent",
    input_schema={"query": {"type": "string"}},
)

# 3. Coordinator 调用
result = agent_tool.execute(query="AI trends")
# result = {"result": "...", "success": True, ...}
```

### 3.2 Handoff Execution

```python
# 1. 创建 agents
agent_a = Agent(model=model_a)
agent_b = Agent(model=model_b)

# 2. 创建 handoff manager
agents = {"agent_a": agent_a, "agent_b": agent_b}
manager = HandoffManager(agents, policy=HandoffPolicy())

# 3. 执行任务
result = manager.execute_with_handoff(
    initial_agent_id="agent_a",
    task=task,
)
# 如果 agent_a 达到 max_steps，自动 handoff 到 agent_b
```

### 3.3 Supervisor/Worker Execution

```python
# 1. 创建 workers
worker1 = Worker("researcher", agent1, ["research"])
worker2 = Worker("writer", agent2, ["writing"])

# 2. 创建 supervisor
supervisor = Supervisor(
    supervisor_agent=supervisor_agent,
    workers=[worker1, worker2],
)

# 3. 执行任务
result = supervisor.execute_with_workers(task)
# Supervisor 分解任务，分配给 workers，聚合结果
```

## 4. Minimal Implementation

### 4.1 AgentAsTool

```python
@dataclass
class AgentAsTool:
    agent: Agent
    name: str
    description: str
    input_schema: dict[str, Any]
    
    def get_tool_schema(self) -> ToolSchema:
        """Convert agent to tool schema."""
        parameters = []
        for param_name, param_info in self.input_schema.items():
            param = ToolParameter(
                name=param_name,
                type=ParameterType(param_info.get("type", "string")),
                description=param_info.get("description", ""),
            )
            parameters.append(param)
        
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters,
        )
    
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent."""
        task = TaskSpec(goal=kwargs.get("query", str(kwargs)))
        result = self.agent.run(task)
        return {
            "result": result.output,
            "success": result.success,
        }
```

### 4.2 Handoff

```python
@dataclass
class Handoff:
    from_agent: str
    to_agent: str
    reason: str
    context: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "reason": self.reason,
            "context": self.context,
        }

class HandoffPolicy:
    def should_handoff(
        self,
        current_agent: str,
        state: AgentState,
        available_agents: list[str],
    ) -> HandoffDecision:
        """Determine if should handoff."""
        if state.status == "completed":
            return HandoffDecision.COMPLETE
        
        if state.step_count >= self.max_steps_per_agent:
            return HandoffDecision.HANDOFF
        
        return HandoffDecision.CONTINUE
```

### 4.3 Supervisor/Worker

```python
@dataclass
class Worker:
    worker_id: str
    agent: Agent
    capabilities: list[str]
    
    def can_handle(self, task_description: str) -> bool:
        """Check if worker can handle task."""
        task_lower = task_description.lower()
        for capability in self.capabilities:
            if capability.lower() in task_lower:
                return True
        return False
    
    def execute_task(self, task: TaskSpec) -> dict[str, Any]:
        """Execute task."""
        result = self.agent.run(task)
        return {
            "worker_id": self.worker_id,
            "result": result.output,
            "success": result.success,
        }

class Supervisor:
    def __init__(self, supervisor_agent: Agent, workers: list[Worker]):
        self.supervisor_agent = supervisor_agent
        self.workers = {w.worker_id: w for w in workers}
    
    def decompose_task(self, task: TaskSpec) -> list[dict[str, Any]]:
        """Decompose task into subtasks."""
        subtasks = []
        if "research" in task.goal.lower():
            subtasks.append({
                "task_id": "research_1",
                "description": f"Research: {task.goal}",
                "required_capability": "research",
            })
        return subtasks
    
    def assign_worker(self, subtask: dict[str, Any]) -> str | None:
        """Assign worker to subtask."""
        required = subtask.get("required_capability")
        for worker_id, worker in self.workers.items():
            if required is None or required in worker.capabilities:
                return worker_id
        return None
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Composition | 无限委托 | Agent A 委托给 B，B 又委托给 A |
| Composition | 上下文泄漏 | Agent 内部状态暴露给其他 Agent |
| Composition | 重复工作 | 多个 Agent 执行相同任务 |
| Reliability | 消息丢失 | 消息未到达目标 Agent |
| Control | 死锁 | Agent 互相等待消息 |
| Control | 结果冲突 | 不同 Agent 返回矛盾结果 |
| Resource | 成本爆炸 | Multi-agent 开销远超 single-agent |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 优先使用 single-agent + tools
2. 明确定义通信协议
3. 限制委托深度
4. 隔离 Agent 上下文
5. 监控 multi-agent 开销

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加消息持久化**：防止消息丢失
2. **添加超时机制**：防止无限等待
3. **添加负载均衡**：动态分配任务给 workers
4. **添加故障恢复**：Worker 失败时重新分配
5. **添加监控仪表板**：可视化 Agent 协作

## 7. Lab

构建一个 multi-agent 系统，演示：
- Agent-as-tool 模式
- Handoff 模式
- Supervisor/Worker 模式
- 与 single-agent baseline 的比较

见 `lab/README.md`。

## 8. Evaluation

- Composed system is evaluated against single-agent baseline
- Communication payload is typed/structured
- Context leakage boundary is demonstrated
- Multi-agent is rejected for at least one case where it adds no value

## 9. What Changed in Our Agent?

本模块添加了 `composition/` 子包：

- `message.py`: AgentMessage, MessageBus
- `agent_tool.py`: AgentAsTool
- `handoff.py`: Handoff, HandoffPolicy, HandoffManager
- `supervisor.py`: Worker, Supervisor, TaskDelegation

这些组件让 Agent 可以组合和协作，形成 multi-agent 系统。

## 10. Summary

- Composition before multi-agent
- Agent-as-tool: 将一个 Agent 作为另一个 Agent 的工具
- Handoff: 在 Agent 之间转移控制权
- Supervisor/Worker: 协调多个专业 Agent
- 明确定义通信协议和上下文边界
- 监控 multi-agent 开销，避免不必要的复杂性
- Multi-agent 不是银弹，只在必要时使用
