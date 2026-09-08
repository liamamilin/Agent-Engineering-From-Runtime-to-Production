# M4 — Evaluation, Tracing & Failure Analysis

## Learning Objectives

By the end of this module, the learner can:

- 设计分层评估指标（layered evaluation metrics）
- 创建 golden task 数据集
- 实现确定性评估器（deterministic evaluator）
- 使用 trace 重建决策过程
- 将故障分类到正确的层级
- 理解 LLM-as-judge 的局限性

## 1. Engineering Problem

在添加更多能力之前，我们需要知道 Agent 是否真的在工作。

问题：
- 如何判断 Agent 是否成功完成任务？
- 如何比较不同配置的性能？
- 如何检测回归（regression）？
- 如何诊断失败原因？

没有评估系统，改进 Agent 就像蒙眼射击。

## 2. Mental Model

### 2.1 Why Evaluation Comes First

工程原则：**在添加复杂性之前先测量**。

```text
1. 定义成功标准
2. 创建 golden tasks
3. 实现评估指标
4. 建立基线
5. 然后才能改进
```

### 2.2 Layered Evaluation

评估不是单一分数，而是多个维度：

| 层级 | 指标 | 问题 |
|------|------|------|
| Task | 任务成功率 | Agent 完成了任务吗？ |
| Action | 动作正确性 | 选择了正确的工具吗？ |
| Output | 输出正确性 | 答案正确吗？ |
| Cost | 成本效率 | 使用了多少 token？ |
| Latency | 延迟 | 响应快吗？ |
| Steps | 步数效率 | 用了多少步？ |

### 2.3 Golden Tasks

Golden tasks 是预定义的评估用例：

```python
EvalCase(
    id="calc_001",
    task_goal="Calculate 15 * 7",
    success_criteria=["Correct result: 105"],
    expected_output="105",
    expected_tool_calls=["calculator"],
    max_steps=5,
)
```

### 2.4 Failure Taxonomy

故障分类帮助诊断问题：

| 层级 | 故障类型 | 示例 |
|------|----------|------|
| Task | 规范失败 | 成功标准未定义 |
| Observation | 感知失败 | 工具输出解析错误 |
| Context | 上下文失败 | 相关证据被遗漏 |
| Policy | 决策失败 | 选择了错误的工具 |
| Action | 动作失败 | 工具执行错误 |
| Transition | 状态失败 | 结果未记录 |
| Control | 控制失败 | 死循环 |
| Resource | 资源失败 | 超出预算 |

## 3. Runtime Walkthrough

```python
# 1. 创建评估数据集
dataset = EvalDataset(name="test")
dataset.add_case(EvalCase(
    id="calc_001",
    task_goal="Calculate 15 * 7",
    success_criteria=["Result is 105"],
    expected_output="105",
    expected_tool_calls=["calculator"],
))

# 2. 创建评估器
evaluator = Evaluator(agent)

# 3. 运行评估
results = evaluator.evaluate_dataset(dataset)

# 4. 计算指标
summary = MetricCalculator.calculate_summary(results)
print(f"Success rate: {summary['task_success_rate']}")
print(f"Avg action correctness: {summary['avg_action_correctness']}")

# 5. 分类故障
classified = FailureClassifier.classify_batch(results)
for layer, failures in classified.items():
    print(f"{layer}: {len(failures)} failures")

# 6. 回放 trace
harness = ReplayHarness()
replay_result = harness.replay_from_trace(trace)
```

## 4. Minimal Implementation

### 4.1 EvalCase and EvalDataset

```python
@dataclass
class EvalCase:
    id: str
    task_goal: str
    success_criteria: list[str]
    expected_output: str | None = None
    expected_tool_calls: list[str] = field(default_factory=list)
    max_steps: int = 10

@dataclass
class EvalDataset:
    name: str
    cases: list[EvalCase] = field(default_factory=list)
```

### 4.2 Evaluator

```python
class Evaluator:
    def evaluate_case(self, case: EvalCase) -> EvalResult:
        task = TaskSpec(goal=case.task_goal, ...)
        result = self._agent.run(task)

        # Calculate metrics
        task_success = result.success
        action_correctness = self._compare_tool_calls(case, result)
        output_correctness = self._compare_output(case, result)

        return EvalResult(
            case_id=case.id,
            task_success=task_success,
            action_correctness=action_correctness,
            output_correctness=output_correctness,
            ...
        )
```

### 4.3 FailureClassifier

```python
class FailureClassifier:
    @staticmethod
    def classify(result: EvalResult) -> FailureLayer | None:
        if result.task_success:
            return None

        if "tool error" in result.errors:
            return FailureLayer.ACTION

        if result.action_correctness < 0.5:
            return FailureLayer.POLICY

        return FailureLayer.POLICY
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Evaluation | 指标错误 | 成功率计算错误 |
| Evaluation | 数据集偏差 | 测试用例太简单 |
| Evaluation | 过拟合 | 针对测试用例优化 |
| Reliability | 非确定性 | 相同输入不同输出 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 评估数据集要多样化
2. 指标要分层，不要只看成功率
3. 使用 trace 回放检测回归
4. 故障分类帮助定位问题

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加 LLM-as-judge**：使用模型评估开放性问题
2. **添加统计显著性**：多次运行取平均
3. **添加对比基线**：与简单方法比较
4. **添加可视化**：生成评估报告
5. **添加 CI 集成**：自动运行评估

## 7. Lab

构建一个评估系统，包含：
- 10+ golden tasks
- 分层指标计算
- 故障分类
- Trace 回放

见 `lab/README.md`。

## 8. Evaluation

- 至少 10 个评估用例
- Trace 可以重建决策/动作/状态变化
- 确定性指标在离线模式下运行
- 故障被分配到正确的层级

## 9. What Changed in Our Agent?

本模块添加了 `evals/` 子包：

- `dataset.py`: EvalCase, EvalDataset, JSONL 格式
- `evaluator.py`: Evaluator, EvalResult, MetricCalculator
- `replay.py`: ReplayHarness
- `metrics.py`: 各种指标计算器
- `failure_analysis.py`: FailureClassifier, FailureLayer

这些组件让我们可以系统地评估和改进 Agent。

## 10. Summary

- 在添加复杂性之前先评估
- 评估是多维度的：任务成功、动作正确、输出正确、成本、延迟
- Golden tasks 是预定义的评估用例
- 故障分类帮助诊断问题
- Trace 回放检测回归
- LLM-as-judge 有局限性，需要谨慎使用
