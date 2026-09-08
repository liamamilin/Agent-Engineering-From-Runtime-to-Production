# M6 — Retrieval, Grounding & Evidence

## Learning Objectives

By the end of this module, the learner can:

- 理解检索是信息获取，不是记忆本身
- 实现关键词检索和简单的语义检索
- 理解 chunking 和 indexing
- 实现 evidence 和 provenance 追踪
- 检查 claim-evidence 对齐
- 理解 RAG 是 Agent 的一个组件

## 1. Engineering Problem

Agent 需要访问外部知识，但模型的知识是有限的。

问题：
- 如何从大量文档中找到相关信息？
- 如何追踪信息的来源？
- 如何判断答案是否有证据支持？
- 如何处理检索不到的情况？

我们需要一个检索和 grounding 系统，让 Agent 可以基于证据回答问题。

## 2. Mental Model

### 2.1 Retrieval as Information Acquisition

检索是**获取信息**，不是记忆：

```text
Query -> Search -> Retrieve -> Evidence -> Context -> Model -> Answer
```

- Retrieval：从外部获取信息
- Memory：Agent 内部的状态持久化

### 2.2 Evidence with Provenance

每个检索结果都应该有来源追踪：

```python
Evidence(
    id="evidence_1",
    content="Python is a programming language",
    source="doc_1",
    document_id="doc_1",
    chunk_id="doc_1_chunk_0",
    score=0.95,
)
```

### 2.3 Claim-Evidence Alignment

答案中的每个 claim 都应该有证据支持：

```python
Claim(
    text="Python was created by Guido",
    evidence_ids=["evidence_1", "evidence_2"],
    supported=True,
    confidence=0.9,
)
```

### 2.4 RAG as Agent Component

RAG 不是 Agent，而是 Agent 的一个**组件**：

```text
Agent
├── TaskSpec
├── State
├── Context Builder
├── Policy (Model)
├── Tools
│   ├── Search Tool  <-- RAG
│   ├── Calculator
│   └── ...
└── Termination
```

## 3. Runtime Walkthrough

```python
# 1. 创建 corpus
corpus = create_sample_corpus()

# 2. 创建搜索引擎
engine = SearchEngine(corpus)

# 3. 检索
results = engine.search("Python programming", top_k=3)

# 4. 存储 evidence
store = EvidenceStore()
for result in results:
    store.add(result.evidence)

# 5. 创建 claims
claims = [
    Claim(text="Python is a programming language", evidence_ids=["evidence_1"]),
]

# 6. 检查 grounding
checker = GroundingChecker(store)
checked_claims = checker.check_claims(claims)

# 7. 生成摘要
summary = checker.summary(checked_claims)
print(f"Grounding rate: {summary['grounding_rate']:.1%}")
```

## 4. Minimal Implementation

### 4.1 Evidence

```python
@dataclass
class Evidence:
    id: str
    content: str
    source: str
    document_id: str | None = None
    chunk_id: str | None = None
    score: float = 1.0
```

### 4.2 SearchEngine

```python
class SearchEngine:
    def __init__(self, corpus: Corpus):
        self._corpus = corpus
        self._index = {}
        self._build_index()

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        # Tokenize query
        # Score chunks
        # Return top results
        pass
```

### 4.3 GroundingChecker

```python
class GroundingChecker:
    def check_claim(self, claim: Claim) -> Claim:
        # Check if evidence supports claim
        # Update claim.supported and claim.confidence
        pass
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Knowledge | 检索失败 | 相关文档没有被检索到 |
| Knowledge | 幻觉 | 答案没有证据支持 |
| Knowledge | 错误 grounding | 证据不支持但被标记为支持 |
| Context | 信息过载 | 检索太多无关信息 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 总是追踪 evidence 来源
2. 检查 claim-evidence 对齐
3. 报告 grounding rate
4. 处理检索不到的情况

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加 embedding-based 检索**：使用向量相似度
2. **添加 reranking**：使用交叉编码器
3. **添加 query transformation**：重写查询
4. **添加 hybrid search**：结合关键词和语义
5. **添加 evaluation**：测量检索质量

## 7. Lab

构建一个检索和 grounding 系统，包含：
- 本地 corpus
- 搜索引擎
- Evidence 存储
- Grounding 检查

见 `lab/README.md`。

## 8. Evaluation

- 本地 corpus fixtures
- 检索结果保留来源身份
- 重要 claims 可以附加 evidence IDs
- 存在 unsupported-claim 测试
- 检索质量在小 golden set 上测量

## 9. What Changed in Our Agent?

本模块添加了 `retrieval/` 子包：

- `evidence.py`: Evidence, EvidenceStore
- `corpus.py`: Corpus, Document, Chunk
- `search.py`: SearchEngine, SearchResult
- `grounding.py`: GroundingChecker, Claim

这些组件让 Agent 可以基于证据回答问题。

## 10. Summary

- 检索是信息获取，不是记忆
- Evidence 需要追踪来源（provenance）
- Claims 需要检查是否有证据支持
- RAG 是 Agent 的一个组件，不是 Agent 本身
- Grounding rate 是重要指标
- 处理检索不到的情况
