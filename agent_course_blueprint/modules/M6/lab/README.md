# Lab — M6 Retrieval & Grounding

## Objective

构建一个检索和 grounding 系统，支持 evidence 追踪和 claim 检查。

## Starting State

`reference_agent/src/agent_course/retrieval/` 已有基础实现。

## Task

1. 创建 sample corpus
2. 搜索相关信息
3. 存储 evidence
4. 创建 claims 并检查 grounding
5. 计算 grounding rate

## Required API / Interfaces

```python
from agent_course.retrieval import (
    Corpus, SearchEngine, EvidenceStore,
    GroundingChecker, Claim
)
from agent_course.retrieval.corpus import create_sample_corpus
```

## Step-by-Step Requirements

1. 使用 create_sample_corpus() 创建 corpus
2. 创建 SearchEngine
3. 搜索 "Python programming"
4. 将结果存入 EvidenceStore
5. 创建 2-3 个 claims
6. 使用 GroundingChecker 检查 claims
7. 计算 grounding rate

## Tests to Pass

```bash
pytest modules/M6/lab/tests/
```

## Expected Failure Cases

1. 某些 claims 可能没有 evidence 支持
2. 检索可能返回不相关的结果

## Reflection Questions

1. 为什么需要追踪 evidence 来源？
2. 如何判断检索质量？
3. RAG 和 Agent 的关系是什么？
