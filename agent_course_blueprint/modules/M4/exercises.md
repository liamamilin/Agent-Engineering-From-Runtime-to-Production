# Exercises — M4

## Exercise 1: Custom Eval Case

设计一个评估用例，测试 Agent 的多步推理能力：

```python
case = EvalCase(
    id="multi_step_001",
    task_goal="...",
    success_criteria=[...],
    expected_tool_calls=[...],
)
```

**问题**：
1. 成功标准如何定义？
2. 期望的工具调用顺序重要吗？

---

## Exercise 2: Custom Metric

实现一个"工具效率"指标，衡量工具调用的有效性：

```python
class ToolEfficiencyMetric:
    @staticmethod
    def calculate(results: list[EvalResult]) -> float:
        """Calculate tool efficiency score."""
        # 你的实现
        pass
```

---

## Exercise 3: LLM-as-Judge

实现一个简单的 LLM-as-judge 评估器：

```python
class LLMJudge:
    def __init__(self, model: ModelAdapter):
        self._model = model

    def judge(self, task: str, response: str, criteria: list[str]) -> float:
        """Use LLM to judge response quality."""
        # 你的实现
        pass
```

**问题**：
1. LLM-as-judge 的局限性是什么？
2. 如何验证 judge 本身的准确性？

---

## Exercise 4: Regression Detection

实现一个回归检测系统，比较两次运行的结果：

```python
class RegressionDetector:
    def compare(self, baseline: list[EvalResult], current: list[EvalResult]) -> dict:
        """Detect regressions between runs."""
        # 你的实现
        pass
```
