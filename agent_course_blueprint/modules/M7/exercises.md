# Exercises — M7

## Exercise 1: Checkpoint Recovery

实现一个函数，从 checkpoint 恢复 Agent 运行：

```python
def resume_from_checkpoint(
    checkpoint_store: CheckpointStore,
    run_id: str,
    agent: Agent,
) -> AgentRunResult:
    """Resume an agent run from a checkpoint.
    
    Args:
        checkpoint_store: The checkpoint storage.
        run_id: The ID of the run to resume.
        agent: The agent to continue running.
        
    Returns:
        The result of the resumed run.
    """
    # 你的实现
    pass
```

**问题**：
1. 如何验证 checkpoint 的完整性？
2. 如果 checkpoint 损坏，应该如何处理？
3. 恢复后，step_count 应该从哪里开始？

---

## Exercise 2: Memory Extraction

实现一个函数，从 Agent 运行结果中提取值得记忆的信息：

```python
def extract_memories_from_run(
    result: AgentRunResult,
) -> list[MemoryRecord]:
    """Extract memorable information from an agent run.
    
    Args:
        result: The result of an agent run.
        
    Returns:
        List of memory records to potentially store.
    """
    # 你的实现：提取用户偏好、学到的事实、重要事件
    pass
```

**问题**：
1. 如何判断什么信息值得记住？
2. 如何为提取的记忆分配 importance？
3. 应该提取哪些类型的记忆？

---

## Exercise 3: Memory-Aware Context

实现一个函数，将相关记忆注入到 Agent 上下文中：

```python
def build_context_with_memories(
    task: TaskSpec,
    state: AgentState,
    memory_store: MemoryStore,
    read_policy: MemoryReadPolicy,
) -> list[Message]:
    """Build context including relevant memories.
    
    Args:
        task: The current task.
        state: The current state.
        memory_store: The memory storage.
        read_policy: Policy for retrieving memories.
        
    Returns:
        List of messages including memories.
    """
    # 你的实现
    pass
```

**问题**：
1. 如何判断记忆与当前任务相关？
2. 记忆应该放在上下文的哪个位置？
3. 如何避免记忆过多导致上下文过长？

---

## Exercise 4: Forgetting Scheduler

实现一个定期执行遗忘的策略调度器：

```python
class ForgettingScheduler:
    def __init__(
        self,
        memory_store: MemoryStore,
        forgetting_policy: ForgettingPolicy,
        interval_steps: int = 10,
    ):
        self._store = memory_store
        self._policy = forgetting_policy
        self._interval = interval_steps
        self._step_count = 0
    
    def on_step(self) -> None:
        """Called after each agent step."""
        # 你的实现：定期应用遗忘策略
        pass
```

**问题**：
1. 遗忘应该多频繁执行？
2. 遗忘是硬删除还是软删除？
3. 如何避免遗忘重要记忆？
