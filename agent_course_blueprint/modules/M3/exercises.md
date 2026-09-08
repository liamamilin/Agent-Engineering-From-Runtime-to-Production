# Exercises — M3

## Exercise 1: Custom Termination Policy

实现一个自定义终止策略，当任务满足特定条件时终止：

```python
from agent_course.core.termination import TerminationPolicy, TerminationReason

class CustomTermination(TerminationPolicy):
    def should_stop(self, task, state):
        # 你的实现：当找到特定关键词时终止
        pass
```

---

## Exercise 2: State Inspection

实现一个函数，从 State 中提取所有工具结果：

```python
def extract_tool_results(state: AgentState) -> list[dict]:
    """Extract all tool results from state."""
    # 你的实现
    pass
```

---

## Exercise 3: Loop Detection

实现一个机制，检测 Agent 是否陷入死循环（重复调用同一工具）：

```python
class LoopDetector:
    def __init__(self, threshold: int = 3):
        self._history = []
        self._threshold = threshold

    def check(self, decision: Decision) -> bool:
        """Returns True if loop detected."""
        # 你的实现
        pass
```

---

## Exercise 4: Budget Tracking

实现一个 budget tracker，跟踪 token 使用和成本：

```python
class BudgetTracker:
    def __init__(self, max_tokens: int, max_cost_usd: float):
        self._tokens_used = 0
        self._cost_usd = 0.0

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        # 你的实现
        pass

    def is_exceeded(self) -> bool:
        # 你的实现
        pass
```
