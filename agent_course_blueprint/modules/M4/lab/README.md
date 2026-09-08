# Lab — M4 Evaluation System

## Objective

构建一个完整的评估系统，包含 golden tasks、指标计算和故障分析。

## Starting State

`reference_agent/src/agent_course/evals/` 已有基础实现。

## Task

1. 创建包含 10+ 用例的评估数据集
2. 运行评估并计算指标
3. 分析故障分布
4. 使用 trace 回放检测回归

## Required API / Interfaces

```python
from agent_course.evals import (
    EvalCase, EvalDataset, Evaluator,
    MetricCalculator, FailureClassifier, ReplayHarness
)
```

## Step-by-Step Requirements

1. 使用 create_sample_dataset() 创建数据集
2. 创建 Agent 和 Evaluator
3. 运行评估
4. 计算汇总指标
5. 分类故障
6. 回放一个 trace

## Tests to Pass

```bash
pytest modules/M4/lab/tests/
```

## Expected Failure Cases

1. 某些用例应该失败（如 nonexistent_tool）
2. 故障应该被正确分类

## Reflection Questions

1. 为什么需要分层评估而不是单一分数？
2. 如何判断评估数据集是否有代表性？
3. Trace 回放如何帮助检测回归？
