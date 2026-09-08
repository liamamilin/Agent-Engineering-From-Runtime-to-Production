# Exercises — M8

## Exercise 1: Plan Creation

实现一个函数，根据任务描述创建计划：

```python
def create_research_plan(task_description: str) -> Plan:
    """Create a plan for a research task.
    
    Args:
        task_description: Description of the research task.
    
    Returns:
        A Plan object with appropriate steps.
    """
    # 你的实现：分析任务，创建步骤
    pass
```

**问题**：
1. 如何确定步骤之间的依赖关系？
2. 哪些步骤可能需要人类审批？
3. 如何处理步骤失败的情况？

---

## Exercise 2: Workflow Design

设计一个 workflow，用于数据处理管道：

```python
def create_data_processing_workflow() -> Workflow:
    """Create a workflow for data processing.
    
    States: initial → validating → processing → reviewing → completed
    
    Requirements:
    - Validation step is automatic
    - Processing requires approval
    - Review can reject and go back to processing
    """
    # 你的实现
    pass
```

**问题**：
1. 如何处理拒绝后的重新处理？
2. 如何记录每次状态转换？
3. 如何处理超时？

---

## Exercise 3: Replanning Strategy

实现一个 replanning 策略，当步骤失败时调整计划：

```python
def replan_after_failure(
    plan: Plan,
    failed_step_id: str,
    failure_reason: str,
) -> Plan:
    """Replan after a step fails.
    
    Strategy:
    - Keep completed steps
    - Remove failed step
    - Add alternative steps if possible
    - Update dependencies
    """
    # 你的实现
    pass
```

**问题**：
1. 如何判断是否应该 replan 还是直接失败？
2. 如何生成替代步骤？
3. 如何避免无限 replan？

---

## Exercise 4: Approval Policy

实现一个审批策略，根据操作风险决定是否需要审批：

```python
class RiskBasedApprovalPolicy(HumanApprovalPolicy):
    def requires_approval(self, action: str, arguments: dict) -> bool:
        """Determine if action requires approval based on risk.
        
        Risk levels:
        - Low: read-only operations (no approval)
        - Medium: modifications within safe boundaries (no approval)
        - High: destructive or external operations (approval required)
        """
        # 你的实现：评估操作风险
        pass
```

**问题**：
1. 如何评估操作的风险级别？
2. 如何处理边界情况？
3. 如何平衡安全性和用户体验？
