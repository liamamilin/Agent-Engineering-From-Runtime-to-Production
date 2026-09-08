# M0 — Agent System Mental Model

## Learning Objectives

By the end of this module, the learner can:

- 区分 LLM 调用、workflow、tool-using workflow 和 Agent
- 正确画出系统边界（system boundary）
- 定义 TaskSpec、Observation、State、Context、Policy、Decision、Action、Transition、Termination、Environment
- 解释 Model 和 Tools 在系统中的位置，而不将它们等同于整个 Agent
- 按照层级分类常见故障

## 1. Engineering Problem

当我们说"构建一个 Agent"时，我们到底在构建什么？

很多初学者会把 Agent 等同于"调用 LLM API"或者"使用某个框架的 Agent 类"。这种理解会导致：

- 无法调试：当系统出错时，不知道问题出在哪个环节
- 无法评估：无法判断系统是"真的在工作"还是"看起来在工作"
- 无法设计：无法根据需求选择合适的架构

我们需要一个精确的心智模型（mental model），能够解释 Agent 运行时（runtime）到底在做什么。

## 2. Mental Model

### 2.1 Canonical Definition

本课程使用以下定义：

> **Agent** 是一个有状态的运行时控制器（stateful runtime controller），它通过反复观察环境（environment）、构建决策上下文（context）、通过策略（policy，通常由模型支持）选择动作（action）、更新状态（state），并根据明确的成功、失败或预算条件终止（terminate），来追求任务规范（TaskSpec）。

这个定义是**实现无关的**（implementation-independent）。它不依赖于任何框架，也不依赖于特定的 LLM 提供商。

### 2.2 System Boundary

Agent 不是它与世界交互的全部。系统边界将"Agent 内部"和"环境"分开：

```text
Task / User
    |
    v
+----------------------------- AGENT RUNTIME -----------------------------+
| TaskSpec -> State -> Context -> Policy/Model -> Decision -> Action      |
|                 ^                                      |                |
|                 |                                      v                |
|             Transition <-------- Observation <---- Tool Result           |
|                                                                    |    |
|                    Control + Termination + Budgets                  |    |
+--------------------------------------------------------------------|----+
                                                                     v
                                                              Environment
```

**Environment** 在 Agent 边界之外。文件、数据库、浏览器、API、shell、用户、其他 Agent 都可能属于环境。

**Tools** 是运行时读取或操作环境的受控接口。

### 2.3 Autonomy Spectrum

Agent 不是二元的"是/否"概念，而是一个自主性（autonomy）谱：

| 类型 | 特征 | 示例 |
|------|------|------|
| LLM 调用 | 单次请求-响应，无状态，无循环 | `chat.completions.create()` |
| Workflow | 预定义流程，确定性控制流 | 固定步骤的审批流程 |
| Tool-using Workflow | 调用工具，但流程预定义 | ReAct 的固定模板版本 |
| Agent | 动态决策，状态驱动，显式终止 | 本课程构建的系统 |

关键区别在于：**谁决定下一步做什么？**

- Workflow：开发者预先编写
- Agent：运行时根据当前状态和观察动态决定

### 2.4 Deterministic vs Probabilistic Components

Agent 运行时包含两类组件：

**确定性组件（Deterministic）**：
- State 管理
- Transition 函数
- Termination 检查
- Tool 执行（给定相同输入，产生相同输出）
- Budget 计数

**概率性组件（Probabilistic）**：
- Model（LLM）
- Policy（当由 LLM 实现时）

工程原则：**用确定性控制器包裹概率性策略**。这样，即使 Model 的行为不确定，整个系统的行为也是可审计、可调试、可控制的。

## 3. Runtime Walkthrough

让我们追踪一个完整的 Agent 步骤：

```python
# Step t 的完整流程

# 1. Observe: 获取新的观察
O_t = observe(environment, previous_action)
# 例如：用户输入 "搜索 Python 教程"

# 2. Build Context: 构建决策上下文
C_t = build_context(task, state_t, O_t, capabilities)
# 例如：组合 TaskSpec + 当前 State + 新观察 + 可用工具描述

# 3. Policy/Model: 产生决策
D_t = policy(model, C_t)
# 例如：Model 返回 Decision(kind="tool", name="search", arguments={"query": "Python 教程"})

# 4. Validate and Execute: 验证并执行动作
R_t = validate_and_execute(D_t, tools, permissions)
# 例如：验证参数合法 -> 执行搜索 -> 返回结果

# 5. Transition: 更新状态
S_t+1 = transition(S_t, O_t, D_t, R_t)
# 例如：将搜索结果加入 State，step_count += 1

# 6. Termination: 检查是否停止
STOP = termination(task, S_t+1, budgets)
# 例如：检查是否达到 max_steps，是否满足 success_criteria

if STOP:
    return final_output
else:
    # 进入下一步
    t = t + 1
```

## 4. Core Runtime Objects

让我们精确定义每个核心对象：

### TaskSpec
定义运行要完成的任务。

```python
@dataclass
class TaskSpec:
    goal: str                    # 目标描述
    success_criteria: list[str]  # 成功标准
    constraints: list[str]       # 约束条件
    max_steps: int               # 最大步数
    max_cost_usd: float | None   # 预算上限
```

### Observation
运行时在特定步骤获得的新信息。

来源：用户输入、工具输出、环境事件、人类审批/拒绝、错误。

### State
从一个步骤传递到下一个步骤的显式信息。

State 比聊天历史（chat history）更广泛。它可能包含：
- 任务进度
- 工具结果
- 计划
- 证据
- 开放问题
- 预算使用情况
- 状态标记
- 中间产物

### Context
为一次模型调用选择的表示。

Context 是从其他信息构建的**视图（view）**，不是所有 State 的同义词。

### Model
被一个或多个运行时组件使用的概率计算引擎。

Model 不等于整个 Agent。它可以用于实现 policy、planning、summarization、classification、evaluation 等子程序。

### Policy
将当前运行时情况映射到下一个决策的规则。

```
Decision_t = Policy(TaskSpec, State_t, Observation_t, Context_t)
```

Policy 可以是：
- 确定性代码
- LLM
- 由确定性代码约束的 LLM
- 路由器或集成器

### Decision
由 policy 产生的类型化运行时选择。

类型：
- `tool`: 调用工具 X，参数 Y
- `ask_user`: 向用户提问
- `final`: 发出最终答案
- `fail`: 以失败状态停止

### Action
对环境执行的经过验证的副作用或信息获取操作。

### Tool
运行时可用的命名、schema 定义的动作适配器。

Tool 本身不是 agentic 的。Agentic 行为来自运行时关于是否、何时、如何调用动作的决策。

### Transition
从当前状态到下一个状态的确定性或受控更新。

```
State_(t+1) = Transition(State_t, Observation_t, Decision_t, ActionResult_t)
```

### Termination
决定运行何时必须停止的策略。

终止条件：
- 成功标准满足
- 显式最终决策
- 达到最大步数
- Token/cost/time 预算耗尽
- 不可恢复的错误
- 人类停止

## 5. Failure Modes

Agent 系统可能在多个层级失败。本课程使用统一的故障分类法（failure taxonomy）：

| 层级 | 故障类别 | 示例 |
|------|----------|------|
| Task | 规范失败 | 成功标准未定义 |
| Observation | 感知/输入失败 | 工具输出不完整或解析错误 |
| Context | 上下文构建失败 | 相关证据被遗漏；注入被包含 |
| Policy | 决策失败 | 选择了错误的下一步动作 |
| Action | 工具/动作失败 | 参数无效；权限被拒绝；副作用失败 |
| Transition | 状态更新失败 | 成功结果未被记录 |
| Control | 编排失败 | 循环重复、死锁或过早停止 |
| Knowledge | 基础失败 | 无支持的声明或检索质量差 |
| Memory | 持久化失败 | 重用陈旧/错误的记忆 |
| Composition | 委托失败 | 错误的工作者、重复工作、上下文泄漏 |
| Safety | 边界失败 | 不安全的工具执行或数据泄露 |
| Reliability | 基础设施失败 | 超时、速率限制、提供商中断 |
| Resource | 预算失败 | 过多的 token、步骤、延迟或成本 |
| Evaluation | 测量失败 | 指标奖励错误行为 |

**调试规则**：每个实验都应该先将观察到的故障映射到一个或多个层级，然后再提出修复方案。

## 6. Important Non-Equivalences

以下概念**不等同**：

- **LLM != Agent**：LLM 是组件，Agent 是系统
- **Prompt != Context**：Prompt 是文本，Context 是构建的视图
- **Chat history != State**：历史是序列，State 是结构化信息
- **State != Memory**：State 是当前运行，Memory 是跨运行的持久化
- **Retrieval != Memory**：检索是获取，Memory 是存储
- **RAG != Agent**：RAG 是信息获取模式，Agent 是运行时控制器
- **Tool calling != Agent**：工具调用是动作，Agent 是决策循环
- **Workflow != Agent**：Workflow 是预定义流程，Agent 是动态决策（虽然 Workflow 可能包含 agentic 节点）
- **Multi-agent != automatically better agent**：多 Agent 不自动意味着更好
- **MCP != multi-agent protocol**：MCP 是工具/上下文集成协议
- **A2A != tool protocol**：A2A 是 Agent 间互操作协议
- **Successful execution != correct execution**：成功运行不等于正确运行

## 7. Lab

本模块的实验是概念性的：给定三个系统，分类每个系统是 LLM 调用、workflow 还是 Agent，并画出运行时对象和边界。

见 `exercises.md`。

## 8. Evaluation

学习者能够使用规范运行时方程（canonical runtime equation）叙述一次运行，而不使用框架术语。

## 9. What Changed in Our Agent?

本模块建立了整个课程的概念基础。在 `reference_agent/` 中，我们已经定义了核心类型：

- `TaskSpec`: 任务规范
- `Observation`: 观察
- `AgentState`: 状态
- `Decision`: 决策
- `Transition`: 状态转移
- `TerminationPolicy`: 终止策略

这些类型将在后续模块中逐步扩展和连接。

## 10. Summary

- Agent 是有状态的运行时控制器，不是 LLM 调用
- 系统边界将 Agent 内部与环境分开
- 核心对象：TaskSpec、Observation、State、Context、Policy、Decision、Action、Transition、Termination
- Model 是组件，不是整个 Agent
- Tool 是接口，不是 Agent 行为本身
- 用确定性控制器包裹概率性策略
- 故障可以在多个层级发生，需要分类诊断
- 成功执行不等于正确执行
