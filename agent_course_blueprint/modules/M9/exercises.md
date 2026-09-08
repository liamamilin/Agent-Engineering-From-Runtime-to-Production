# Exercises — M9

## Exercise 1: Agent-as-Tool Implementation

实现一个 AgentAsTool，将一个 research agent 包装成工具：

```python
def create_research_agent_tool(model: ModelAdapter) -> AgentAsTool:
    """Create a research agent wrapped as a tool.
    
    Requirements:
    - Agent should be able to search and summarize
    - Tool schema should include query parameter
    - Execute should return structured result
    """
    # 你的实现
    pass
```

**问题**：
1. 如何定义 input/output schema？
2. 如何处理 agent 执行失败？
3. 如何限制 agent 的执行步数？

---

## Exercise 2: Handoff Policy

实现一个 handoff policy，根据任务类型决定何时 handoff：

```python
class TaskBasedHandoffPolicy(HandoffPolicy):
    def __init__(self, task_type_thresholds: dict[str, int]):
        """Initialize with task type specific thresholds.
        
        Args:
            task_type_thresholds: Map of task type to max steps.
        """
        # 你的实现
        pass
    
    def should_handoff(
        self,
        current_agent: str,
        state: AgentState,
        available_agents: list[str],
    ) -> HandoffDecision:
        """Determine if should handoff based on task type."""
        # 你的实现
        pass
```

**问题**：
1. 如何识别任务类型？
2. 如何选择合适的目标 agent？
3. 如何传递上下文？

---

## Exercise 3: Supervisor Task Decomposition

实现一个 supervisor，能够分解复杂任务：

```python
class AdvancedSupervisor(Supervisor):
    def decompose_task(self, task: TaskSpec) -> list[dict[str, Any]]:
        """Decompose complex task into subtasks.
        
        Requirements:
        - Identify research, analysis, and writing needs
        - Create dependencies between subtasks
        - Assign appropriate workers
        """
        # 你的实现
        pass
```

**问题**：
1. 如何识别任务中的不同需求？
2. 如何确定子任务之间的依赖关系？
3. 如何聚合多个 worker 的结果？

---

## Exercise 4: Context Isolation

实现一个 context 隔离机制，防止 agent 内部状态泄漏：

```python
class ContextIsolator:
    def extract_shared_context(self, agent_state: AgentState) -> dict[str, Any]:
        """Extract only the context that should be shared.
        
        Requirements:
        - Include task information
        - Include relevant evidence
        - Exclude internal state
        - Exclude agent-specific history
        """
        # 你的实现
        pass
    
    def create_isolated_state(
        self,
        shared_context: dict[str, Any],
        receiving_agent: Agent,
    ) -> AgentState:
        """Create a new state for receiving agent."""
        # 你的实现
        pass
```

**问题**：
1. 哪些信息应该共享？
2. 哪些信息应该隔离？
3. 如何平衡信息共享和隔离？
