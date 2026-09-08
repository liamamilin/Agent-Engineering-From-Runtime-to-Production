# M7 — Memory & Persistence

## Learning Objectives

By the end of this module, the learner can:

- 区分 transient state、session state 和 durable memory
- 实现 checkpoint 机制支持中断恢复
- 设计 memory write policy 控制什么应该被记住
- 实现 memory read policy 控制如何检索记忆
- 实现 forgetting policy 管理记忆的生命周期
- 理解 episodic、semantic 和 user memory 的区别

## 1. Engineering Problem

Agent 需要跨运行保持知识，但面临以下挑战：

1. **状态丢失**：程序崩溃或重启后，之前的工作状态全部丢失
2. **记忆爆炸**：如果记住所有东西，存储和检索成本会爆炸
3. **过时信息**：旧的记忆可能不再准确或相关
4. **隐私边界**：某些信息不应该被持久化

我们需要一个分层的记忆系统，支持：
- 短期状态（transient state）：当前运行的上下文
- 会话状态（session state）：跨步骤的信息
- 持久记忆（durable memory）：跨运行的知识

## 2. Mental Model

### 2.1 Three Layers of State

```text
┌─────────────────────────────────────────┐
│  Durable Memory (跨运行)                │
│  - 用户偏好、学到的事实、经验教训       │
│  - 需要 write/read/forget policies      │
├─────────────────────────────────────────┤
│  Session State (跨步骤)                 │
│  - 当前任务的进度、收集的证据           │
│  - 任务结束后可能丢失                   │
├─────────────────────────────────────────┤
│  Transient State (单步骤)               │
│  - 当前步骤的临时数据                   │
│  - 步骤结束后立即丢弃                   │
└─────────────────────────────────────────┘
```

### 2.2 Memory Types

| 类型 | 内容 | 示例 |
|------|------|------|
| Episodic | 事件和经历 | "用户在 2024-01-15 询问了 Python 教程" |
| Semantic | 事实和知识 | "Python 是一种编程语言" |
| User | 用户偏好 | "用户喜欢简洁的代码风格" |

### 2.3 Checkpoint & Resume

Checkpoint 是运行状态的快照，用于：
- 中断恢复：程序崩溃后从上次状态继续
- 长时运行：跨越多个会话的任务
- 调试：回溯到特定状态

```text
Run Start -> Step 1 -> Step 2 -> [Checkpoint] -> Step 3 -> [Crash]
                                                         ↓
                                              [Resume from Checkpoint]
                                                         ↓
                                              Step 3 -> Step 4 -> ...
```

### 2.4 Memory Policies

记忆不是自动的，需要策略控制：

**Write Policy**：决定什么应该被记住
- 重要性阈值：只记住重要的信息
- 类型过滤：自动记住用户偏好，但不自动记住所有事件
- 标签要求：必须有特定标签才存储

**Read Policy**：决定如何检索记忆
- 相关性排序：根据当前任务选择相关记忆
- 重要性加权：重要记忆优先
- 数量限制：避免上下文过长

**Forgetting Policy**：决定何时遗忘
- 时间衰减：旧记忆逐渐遗忘
- 重要性保留：重要记忆长期保留
- 冲突解决：新信息覆盖旧信息

## 3. Runtime Walkthrough

```python
# 1. 创建 checkpoint store
checkpoint_store = CheckpointStore(storage_path="./checkpoints")

# 2. 创建 memory store
memory_store = MemoryStore(storage_path="./memories")

# 3. 配置 policies
write_policy = MemoryWritePolicy(
    min_importance=0.5,
    auto_store_user=True,
    auto_store_episodes=False,
)
read_policy = MemoryReadPolicy(
    max_memories=10,
    min_importance=0.3,
    prefer_recent=True,
)
forgetting_policy = ForgettingPolicy(
    max_age_days=30,
    low_importance_threshold=0.2,
)

# 4. Agent 运行时
def run_with_memory(task):
    # 检查是否有 checkpoint
    checkpoint = checkpoint_store.load(task.run_id)
    if checkpoint:
        state = restore_state(checkpoint)
    else:
        state = initial_state(task)
    
    # 检索相关记忆
    relevant_memories = memory_store.search(task.goal)
    memories = read_policy.filter_and_rank(relevant_memories)
    
    # 运行 agent
    while not done(state):
        # 将记忆加入上下文
        context = build_context(state, memories)
        
        # 执行步骤
        step_result = execute_step(context)
        update_state(state, step_result)
        
        # 定期保存 checkpoint
        if should_checkpoint(state):
            checkpoint = create_checkpoint(state)
            checkpoint_store.save(checkpoint)
        
        # 决定是否存储新记忆
        for candidate in extract_memories(step_result):
            if write_policy.should_store(candidate):
                memory_store.add(candidate)
    
    # 应用遗忘策略
    all_memories = memory_store.list_all()
    to_forget = forgetting_policy.apply_forgetting(all_memories)
    for mem_id in to_forget:
        memory_store.invalidate(mem_id)
```

## 4. Minimal Implementation

### 4.1 Checkpoint

```python
@dataclass
class Checkpoint:
    run_id: str
    step_count: int
    state_snapshot: dict[str, Any]
    task: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

### 4.2 CheckpointStore

```python
class CheckpointStore:
    def save(self, checkpoint: Checkpoint) -> None:
        # 序列化并存储
        pass
    
    def load(self, run_id: str) -> Checkpoint | None:
        # 加载并反序列化
        pass
    
    def delete(self, run_id: str) -> bool:
        # 删除 checkpoint
        pass
```

### 4.3 MemoryRecord

```python
@dataclass
class MemoryRecord:
    id: str
    memory_type: MemoryType  # EPISODIC, SEMANTIC, USER
    content: str
    source: str
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    access_count: int = 0
    invalidated: bool = False
```

### 4.4 MemoryStore

```python
class MemoryStore:
    def add(self, memory: MemoryRecord) -> None:
        # 存储记忆
        pass
    
    def search(self, query: str) -> list[MemoryRecord]:
        # 搜索相关记忆
        pass
    
    def invalidate(self, memory_id: str) -> bool:
        # 软删除记忆
        pass
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Memory | 记忆丢失 | 程序崩溃，未保存 checkpoint |
| Memory | 记忆污染 | 错误信息被存储为事实 |
| Memory | 记忆过时 | 旧信息未更新导致错误决策 |
| Memory | 记忆爆炸 | 存储过多无用信息，检索变慢 |
| Memory | 隐私泄露 | 敏感信息被持久化 |
| Control | 恢复失败 | Checkpoint 损坏，无法恢复 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 定期保存 checkpoint，不要依赖最后保存
2. 记忆写入需要策略控制，不是所有信息都值得记住
3. 实现遗忘机制，避免记忆爆炸
4. 敏感信息不应该被持久化
5. Checkpoint 应该包含足够的元数据用于调试

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加向量化检索**：使用 embedding 进行语义搜索
2. **添加记忆压缩**：合并相似记忆，减少冗余
3. **添加记忆版本控制**：跟踪记忆的更新历史
4. **添加隐私过滤**：自动检测和脱敏敏感信息
5. **添加分布式存储**：支持多节点共享记忆

## 7. Lab

构建一个带记忆和 checkpoint 的 Agent，支持：
- 中断后从 checkpoint 恢复
- 根据策略存储和检索记忆
- 应用遗忘策略清理过时记忆

见 `lab/README.md`。

## 8. Evaluation

- 中断的运行可以从 checkpoint 恢复
- 记忆写入不是自动的，需要策略控制
- 过时记忆可以被失效
- 记忆检索在 trace 中可观察

## 9. What Changed in Our Agent?

本模块添加了 `memory/` 子包：

- `checkpoint.py`: Checkpoint, CheckpointStore
- `store.py`: MemoryRecord, MemoryStore, MemoryType
- `policy.py`: MemoryWritePolicy, MemoryReadPolicy, ForgettingPolicy

这些组件让 Agent 可以跨运行保持知识，支持长时间任务的恢复。

## 10. Summary

- 状态分三层：transient、session、durable
- 记忆分三类：episodic、semantic、user
- Checkpoint 支持中断恢复
- 记忆写入需要策略控制，不是自动的
- 记忆检索需要排序和过滤
- 遗忘策略避免记忆爆炸
- 敏感信息不应该被持久化
