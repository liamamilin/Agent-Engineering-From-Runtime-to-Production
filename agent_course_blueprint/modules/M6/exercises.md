# Exercises — M6

## Exercise 1: Custom Corpus

创建一个自定义 corpus，包含你选择的主题：

```python
corpus = Corpus(name="my_corpus")
# 添加 3-5 个文档
```

---

## Exercise 2: Improved Search

实现一个改进的搜索引擎，支持：
- 词干提取（stemming）
- 停用词过滤
- TF-IDF 评分

```python
class ImprovedSearchEngine(SearchEngine):
    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        # 你的实现
        pass
```

---

## Exercise 3: Query Transformation

实现一个查询转换模块，将用户查询转换为更适合检索的形式：

```python
class QueryTransformer:
    def transform(self, query: str) -> str:
        """Transform query for better retrieval."""
        # 你的实现：扩展同义词、移除停用词等
        pass
```

---

## Exercise 4: Retrieval Evaluation

实现一个检索质量评估器：

```python
class RetrievalEvaluator:
    def __init__(self, golden_set: list[dict]):
        self._golden_set = golden_set

    def evaluate(self, engine: SearchEngine) -> dict:
        """Calculate recall and precision."""
        # 你的实现
        pass
```
