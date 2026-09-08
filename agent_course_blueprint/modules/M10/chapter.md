# M10 — Safety, Reliability & Resource Control

## Learning Objectives

By the end of this module, the learner can:

- 实现权限系统，控制 agent 对资源的操作
- 实现 guardrails，验证和过滤输入输出
- 实现预算管理，控制资源消耗
- 实现可靠性机制，包括重试、超时和断路器
- 理解安全、可靠性和资源控制的重要性

## 1. Engineering Problem

Agent 系统在生产环境中面临以下挑战：

1. **权限控制**：Agent 可能访问敏感资源或执行危险操作
2. **输入输出安全**：Agent 可能接收恶意输入或产生有害输出
3. **资源消耗**：Agent 可能消耗过多 token、时间或成本
4. **故障处理**：Agent 可能遇到网络错误、超时或其他故障

我们需要一个完整的安全和可靠性框架来保护系统。

## 2. Mental Model

### 2.1 Permission System

权限系统控制 Agent 对资源的访问：

```text
Permission Levels:
- NONE: 无权限
- READ: 只读访问
- WRITE: 写入访问（包括读取）
- EXECUTE: 执行访问（包括读取和写入）
- ADMIN: 完全访问

Permission = (resource, level, conditions)
```

### 2.2 Guardrails

Guardrails 验证和过滤输入输出：

```text
Input Guardrails:
- 长度限制
- 模式匹配
- 敏感词过滤
- 格式验证

Output Guardrails:
- 内容安全
- 格式验证
- 敏感信息过滤
```

### 2.3 Budget Management

预算管理控制资源消耗：

```text
Budget Types:
- TOKENS: Token 消耗
- STEPS: 执行步数
- TIME: 执行时间
- COST: 成本（USD）
- API_CALLS: API 调用次数

Budget = (type, limit, used)
```

### 2.4 Reliability Mechanisms

可靠性机制处理故障：

```text
Retry Policy:
- 最大重试次数
- 退避策略（指数退避）
- 可重试异常

Timeout Policy:
- 超时时间
- 超时处理

Circuit Breaker:
- 失败阈值
- 恢复超时
- 状态机（CLOSED -> OPEN -> HALF_OPEN）
```

## 3. Runtime Walkthrough

### 3.1 Permission Check

```python
# 1. 创建权限管理器
perm_manager = PermissionManager()

# 2. 授予权限
perm = Permission(
    resource="file:/tmp",
    level=PermissionLevel.WRITE,
)
perm_manager.grant("agent_1", perm)

# 3. 检查权限
if perm_manager.check("agent_1", "file:/tmp", "write"):
    # 执行操作
    pass
else:
    # 拒绝操作
    pass
```

### 3.2 Guardrail Check

```python
# 1. 创建 guardrail 管理器
guardrail_manager = GuardrailManager()

# 2. 添加 guardrails
length_guardrail = guardrail_manager.create_length_guardrail(
    "max_length", 1000, is_input=True
)
guardrail_manager.add_input_guardrail(length_guardrail)

blocked_guardrail = guardrail_manager.create_blocked_words_guardrail(
    "no_bad_words", ["evil", "hack"], is_input=True
)
guardrail_manager.add_input_guardrail(blocked_guardrail)

# 3. 检查输入
is_valid, errors = guardrail_manager.check_input(user_input)
if not is_valid:
    # 拒绝输入
    pass
```

### 3.3 Budget Check

```python
# 1. 创建预算管理器
budget_manager = BudgetManager()

# 2. 创建预算
budget_manager.create_token_budget("agent_1", limit=10000)
budget_manager.create_step_budget("agent_1", limit=50)

# 3. 消耗预算
try:
    budget_manager.consume("agent_1", BudgetType.TOKENS, 100)
except BudgetExceededError:
    # 预算超限
    pass

# 4. 检查预算
if budget_manager.check_budget("agent_1", BudgetType.TOKENS):
    # 预算充足
    pass
```

### 3.4 Reliability Execution

```python
# 1. 创建可靠性管理器
reliability_manager = ReliabilityManager()

# 2. 设置重试策略
retry_policy = RetryPolicy(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
)
reliability_manager.set_retry_policy("agent_1", retry_policy)

# 3. 设置超时策略
timeout_policy = TimeoutPolicy(timeout_seconds=30.0)
reliability_manager.set_timeout_policy("agent_1", timeout_policy)

# 4. 设置断路器
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
)
reliability_manager.set_circuit_breaker("agent_1", circuit_breaker)

# 5. 执行操作
result = reliability_manager.execute_with_all("agent_1", risky_operation)
```

## 4. Minimal Implementation

### 4.1 Permission

```python
@dataclass
class Permission:
    resource: str
    level: PermissionLevel
    conditions: dict[str, Any] = field(default_factory=dict)
    
    def allows(self, action: str, context: dict[str, Any] | None = None) -> bool:
        """Check if permission allows action."""
        action_levels = {
            "read": PermissionLevel.READ,
            "write": PermissionLevel.WRITE,
            "execute": PermissionLevel.EXECUTE,
        }
        required_level = action_levels.get(action, PermissionLevel.NONE)
        
        if not self.level.includes(required_level):
            return False
        
        if self.conditions:
            context = context or {}
            for key, value in self.conditions.items():
                if key not in context or context[key] != value:
                    return False
        
        return True

class PermissionManager:
    def __init__(self):
        self._permissions: dict[str, list[Permission]] = {}
    
    def grant(self, agent_id: str, permission: Permission) -> None:
        if agent_id not in self._permissions:
            self._permissions[agent_id] = []
        self._permissions[agent_id].append(permission)
    
    def check(self, agent_id: str, resource: str, action: str, 
              context: dict[str, Any] | None = None) -> bool:
        if agent_id not in self._permissions:
            return False
        
        for permission in self._permissions[agent_id]:
            if permission.resource == resource or permission.resource == "*":
                if permission.allows(action, context):
                    return True
        
        return False
```

### 4.2 Guardrail

```python
@dataclass
class Guardrail:
    name: str
    description: str
    check_fn: Callable[[Any], tuple[bool, str]]
    
    def check(self, value: Any) -> tuple[bool, str]:
        return self.check_fn(value)

class GuardrailManager:
    def __init__(self):
        self._input_guardrails: list[Guardrail] = []
        self._output_guardrails: list[Guardrail] = []
    
    def add_input_guardrail(self, guardrail: Guardrail) -> None:
        self._input_guardrails.append(guardrail)
    
    def check_input(self, value: Any) -> tuple[bool, list[str]]:
        errors = []
        for guardrail in self._input_guardrails:
            is_valid, error_msg = guardrail.check(value)
            if not is_valid:
                errors.append(f"{guardrail.name}: {error_msg}")
        return len(errors) == 0, errors
    
    def create_length_guardrail(self, name: str, max_length: int, 
                                is_input: bool = True) -> Guardrail:
        def check_length(value: Any) -> tuple[bool, str]:
            if isinstance(value, str) and len(value) > max_length:
                return False, f"Length {len(value)} exceeds maximum {max_length}"
            return True, ""
        
        return Guardrail(
            name=name,
            description=f"Maximum length: {max_length}",
            check_fn=check_length,
        )
```

### 4.3 Budget

```python
@dataclass
class Budget:
    budget_type: BudgetType
    limit: float
    used: float = 0.0
    
    @property
    def is_exceeded(self) -> bool:
        return self.used > self.limit
    
    def consume(self, amount: float) -> None:
        if self.used + amount > self.limit:
            raise BudgetExceededError(
                f"Budget exceeded: {self.budget_type.value} "
                f"(used={self.used}, limit={self.limit}, requested={amount})"
            )
        self.used += amount
    
    def try_consume(self, amount: float) -> bool:
        if self.used + amount > self.limit:
            return False
        self.used += amount
        return True

class BudgetManager:
    def __init__(self):
        self._budgets: dict[str, dict[BudgetType, Budget]] = {}
    
    def create_budget(self, agent_id: str, budget_type: BudgetType, 
                      limit: float) -> Budget:
        if agent_id not in self._budgets:
            self._budgets[agent_id] = {}
        budget = Budget(budget_type=budget_type, limit=limit)
        self._budgets[agent_id][budget_type] = budget
        return budget
    
    def consume(self, agent_id: str, budget_type: BudgetType, 
                amount: float) -> None:
        budget = self.get_budget(agent_id, budget_type)
        if budget:
            budget.consume(amount)
    
    def check_budget(self, agent_id: str, budget_type: BudgetType) -> bool:
        budget = self.get_budget(agent_id, budget_type)
        if budget is None:
            return True
        return not budget.is_exceeded
```

### 4.4 Reliability

```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    
    def execute(self, fn: Callable[[], Any]) -> Any:
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    time.sleep(delay)
        raise last_exception

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    
    def call(self, fn: Callable[[], Any]) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = fn()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Safety | 权限不足 | Agent 尝试访问未授权资源 |
| Safety | 权限过宽 | Agent 拥有过多权限，造成安全风险 |
| Safety | 绕过检查 | 恶意输入绕过 guardrail 检查 |
| Safety | 误报 | 正常输入被 guardrail 拒绝 |
| Resource | 预算超限 | Agent 消耗超过预算限制 |
| Resource | 预算不足 | 预算设置过低，Agent 无法完成任务 |
| Reliability | 重试风暴 | 大量重试导致系统过载 |
| Reliability | 断路器误触发 | 断路器在正常故障时打开 |
| Reliability | 超时设置不当 | 超时时间过短或过长 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 最小权限原则：只授予必要的权限
2. 深度防御：多层 guardrails 保护
3. 预算优先：在任务开始前检查预算
4. 优雅降级：故障时优雅处理，不崩溃
5. 监控和告警：实时监控安全和可靠性指标

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加权限审计**：记录所有权限检查
2. **添加动态 guardrails**：根据上下文动态调整
3. **添加预算预测**：预测任务所需预算
4. **添加智能重试**：根据错误类型选择重试策略
5. **添加分布式断路器**：跨服务共享断路器状态

## 7. Lab

构建一个安全和可靠性框架，演示：
- 权限检查和授权
- Guardrail 验证和过滤
- 预算管理和控制
- 重试、超时和断路器

见 `lab/README.md`。

## 8. Evaluation

- Unsafe side effect is blocked in test
- Budget exhaustion terminates cleanly
- Retryable vs non-retryable errors are distinguished
- Guardrail decisions appear in traces

## 9. What Changed in Our Agent?

本模块添加了 `safety/` 子包：

- `permissions.py`: Permission, PermissionLevel, PermissionManager
- `guardrails.py`: Guardrail, InputGuardrail, OutputGuardrail, GuardrailManager
- `budgets.py`: Budget, BudgetManager, BudgetExceededError
- `reliability.py`: RetryPolicy, TimeoutPolicy, CircuitBreaker, ReliabilityManager

这些组件让 Agent 可以安全、可靠地运行，并控制资源消耗。

## 10. Summary

- 权限系统控制 Agent 对资源的访问
- Guardrails 验证和过滤输入输出
- 预算管理控制资源消耗
- 可靠性机制处理故障
- 最小权限原则：只授予必要的权限
- 深度防御：多层保护
- 优雅降级：故障时优雅处理
- 监控和告警：实时监控指标
