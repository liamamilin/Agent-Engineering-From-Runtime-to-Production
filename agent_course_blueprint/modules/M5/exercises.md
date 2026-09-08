# Exercises — M5

## Exercise 1: Custom Selection Policy

实现一个基于相关性的选择策略：

```python
class RelevanceSelector(SelectionPolicy):
    def __init__(self, query: str):
        self._query = query

    def select(self, items: list[ContextItem], budget_tokens: int) -> list[ContextItem]:
        """Select items most relevant to query."""
        # 你的实现：使用简单的关键词匹配或 embedding 相似度
        pass
```

---

## Exercise 2: Budget Allocation

实现一个函数，为不同来源分配 token 预算：

```python
def allocate_budget(
    total_budget: int,
    has_retrieval: bool,
    has_memory: bool,
) -> dict[str, int]:
    """Allocate budget to different sources."""
    # 你的实现
    pass
```

---

## Exercise 3: Injection Detection

实现一个简单的 prompt injection 检测器：

```python
class InjectionDetector:
    def detect(self, content: str) -> bool:
        """Detect potential prompt injection."""
        # 你的实现：检查可疑模式
        pass
```

---

## Exercise 4: Context Cache

实现一个 context cache，缓存常用的上下文片段：

```python
class ContextCache:
    def __init__(self, max_size: int = 100):
        self._cache = {}

    def get(self, key: str) -> ContextItem | None:
        # 你的实现
        pass

    def put(self, key: str, item: ContextItem):
        # 你的实现
        pass
```
