# M5 — Context Engineering & Working State

## Learning Objectives

By the end of this module, the learner can:

- 理解 Context 是为每次模型调用构建的选择性视图
- 区分 instructions、task、state、observation、memory、retrieved data、tool descriptions
- 实现 budget-aware 的上下文构建
- 使用优先级策略选择上下文项
- 实现压缩（compaction）策略
- 理解 prompt injection 边界

## 1. Engineering Problem

模型的上下文窗口是有限的。随着对话变长，我们面临：

1. **Token 限制**：无法放入所有信息
2. **信息过载**：太多信息降低模型性能
3. **成本问题**：更多 token = 更高成本
4. **安全风险**：不可信内容可能注入指令

我们需要一个智能的上下文构建系统，在有限预算内选择最有价值的信息。

## 2. Mental Model

### 2.1 Context as Per-Call View

Context 不是 State 的同义词。Context 是为每次模型调用**构建的视图**：

```text
State (all information)
    |
    v
+------------------+
| Context Builder  |  <-- 选择、排序、压缩
+------------------+
    |
    v
Context (selected view for this call)
    |
    v
Model
```

### 2.2 Context Sources

Context 可以来自多个来源：

| 来源 | 优先级 | 示例 |
|------|--------|------|
| Instructions | CRITICAL | System prompt |
| Task | CRITICAL | Goal, success criteria |
| Current Observation | HIGH | Latest user input |
| Recent Tool Results | MEDIUM | Last 5 tool outputs |
| Tool Descriptions | LOW | Available tools |
| Memory | MEDIUM | Retrieved facts |
| Retrieved Data | MEDIUM | Search results |

### 2.3 Budget Allocation

Token 预算需要分配：

```text
Total Budget: 4000 tokens
├── System Prompt: 200 (CRITICAL)
├── Task: 100 (CRITICAL)
├── Current Observation: 200 (HIGH)
├── Recent Tool Results: 1000 (MEDIUM)
├── Tool Descriptions: 500 (LOW)
└── Available for Memory/Retrieval: 2000
```

### 2.4 Selection Strategies

| 策略 | 特征 | 适用场景 |
|------|------|----------|
| Priority | 按优先级选择 | 通用场景 |
| Recency | 选择最近的 | 对话场景 |
| Relevance | 按相关性选择 | 需要检索时 |

### 2.5 Compaction Strategies

当上下文太长时：

1. **Truncation**：截断长内容
2. **Summarization**：总结旧内容
3. **Sliding Window**：保留最近 N 项

## 3. Runtime Walkthrough

```python
# 1. 创建 budget-aware context builder
builder = BudgetContextBuilder(
    system_prompt="You are helpful",
    max_tokens=4000,
    selector=PrioritySelector(),
    compactor=TruncationCompactor(),
)

# 2. 构建上下文
messages = builder.build(task, state, observation, tools)

# 3. 检查选择日志
for entry in builder.selection_log:
    print(f"{entry['source']}: selected={entry['selected']}")

# 4. 检查 budget 使用
print(f"Budget utilization: {builder.budget.utilization:.1%}")
```

## 4. Minimal Implementation

### 4.1 TokenBudget

```python
class TokenBudget:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.used_tokens = 0

    def allocate(self, tokens: int):
        if tokens > self.available:
            raise BudgetExceededError()
        self.used_tokens += tokens

    @property
    def available(self) -> int:
        return self.max_tokens - self.used_tokens
```

### 4.2 ContextItem

```python
class ContextItem:
    content: str
    priority: ContextPriority
    source: str
    token_count: int
```

### 4.3 PrioritySelector

```python
class PrioritySelector:
    def select(self, items, budget_tokens):
        sorted_items = sorted(items, key=lambda x: x.priority)
        selected = []
        total = 0
        for item in sorted_items:
            if total + item.token_count <= budget_tokens:
                selected.append(item)
                total += item.token_count
        return selected
```

### 4.4 BudgetContextBuilder

```python
class BudgetContextBuilder:
    def build(self, task, state, observation, tools):
        items = self._collect_items(task, state, observation, tools)
        items = self._compactor.compact(items)
        selected = self._selector.select(items, self._budget.max_tokens)
        return self._build_messages(selected)
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Context | 预算溢出 | 上下文超过模型限制 |
| Context | 关键信息丢失 | 重要工具结果被丢弃 |
| Context | Prompt injection | 不可信内容包含指令 |
| Context | 信息过载 | 太多信息降低性能 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 总是设置 token 预算
2. CRITICAL 项必须包含
3. 记录选择日志以便调试
4. 分离可信和不可信内容

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加 embedding-based 选择**：使用语义相似度
2. **添加动态预算**：根据任务调整
3. **添加 context cache**：缓存常用上下文
4. **添加 injection 检测**：过滤恶意内容
5. **添加 cost tracking**：跟踪每次调用的成本

## 7. Lab

构建一个 budget-aware context builder，支持：
- 优先级选择
- 压缩策略
- 选择日志
- Budget 跟踪

见 `lab/README.md`。

## 8. Evaluation

- 上下文选择在离线测试模式下是确定性的
- Budget 溢出行为被测试
- 选择/丢弃的项可追踪
- 恶意检索文本与可信指令分离

## 9. What Changed in Our Agent?

本模块添加了 `context/` 子包：

- `budget.py`: TokenBudget
- `selection.py`: ContextItem, ContextPriority, SelectionPolicy
- `compaction.py`: Compactor, TruncationCompactor, SummaryCompactor
- `builder.py`: BudgetContextBuilder

这些组件让 Agent 可以智能地管理上下文。

## 10. Summary

- Context 是为每次模型调用构建的选择性视图
- 不同来源有不同的优先级
- Token 预算需要合理分配
- 选择策略：优先级、最近、相关性
- 压缩策略：截断、总结、滑动窗口
- 分离可信和不可信内容
- 记录选择日志以便调试
