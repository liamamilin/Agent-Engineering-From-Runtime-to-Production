# M2 — Tools & Action Interfaces

## Learning Objectives

By the end of this module, the learner can:

- 定义 tool schema 并注册到 registry
- 实现参数验证（argument validation）
- 区分 read-only 和 side-effecting 工具
- 实现权限控制（permission controls）
- 理解工具结果如何成为 Observation
- 处理工具执行错误

## 1. Engineering Problem

Agent 需要与环境交互，但直接操作环境有以下问题：

1. **参数错误**：模型可能生成格式错误的参数
2. **权限问题**：某些操作需要人类授权
3. **副作用**：写操作可能不可逆
4. **错误处理**：工具可能失败，需要优雅处理

我们需要一个受控的工具接口层，在执行前验证参数，在执行后返回结果。

## 2. Mental Model

### 2.1 Tools as Environment Interfaces

Tools 是 Agent 读取或操作环境的**受控接口**：

```text
+----------------------------- AGENT RUNTIME -----------------------------+
|                                                                         |
|   Decision(kind="tool", name="search", arguments={...})                 |
|       |                                                                 |
|       v                                                                 |
|   +-------------+     +-------------+     +-------------+               |
|   |  Validator  | --> |  Executor   | --> | Environment |               |
|   |  (validate  |     |  (dispatch  |     | (files, DB, |               |
|   |   args)     |     |   to tool)  |     |  APIs, etc) |               |
|   +-------------+     +-------------+     +-------------+               |
|                           |                                             |
|                           v                                             |
|                     ToolResult                                          |
|                     -> Observation                                      |
|                                                                         |
+-------------------------------------------------------------------------+
```

### 2.2 Tool Schema

每个工具都有一个 schema，定义：
- 名称和描述
- 参数（名称、类型、是否必需、默认值）
- 是否需要权限
- 是否幂等

### 2.3 Read vs Write Actions

| 类型 | 特征 | 示例 | 权限要求 |
|------|------|------|----------|
| Read | 无副作用，幂等 | search, calculator | 无 |
| Write | 有副作用，可能不可逆 | write_file, send_email | 需要授权 |

**工程规则**：写操作必须显式请求权限。

## 3. Runtime Walkthrough

```python
# 1. 定义工具 schema
search_schema = ToolSchema(
    name="search",
    description="Search for information",
    parameters=[
        ToolParameter(name="query", type=ParameterType.STRING, required=True),
        ToolParameter(name="max_results", type=ParameterType.INTEGER, required=False, default=5),
    ],
    requires_permission=False,
)

# 2. 注册工具
registry = ToolRegistry()
registry.register(search_schema, search_handler)

# 3. 创建执行器
executor = ToolExecutor(registry)

# 4. 执行工具
result = executor.execute("search", {"query": "Python"})

# 5. 检查结果
if result.success:
    observation = Observation.from_tool("search", result.output)
else:
    observation = Observation.from_error(result.error)
```

## 4. Minimal Implementation

### 4.1 ToolSchema

```python
@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    parameters: list[ToolParameter]
    requires_permission: bool = False
    idempotent: bool = True
```

### 4.2 ToolRegistry

```python
class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._handlers = {}

    def register(self, schema: ToolSchema, handler):
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

    def get(self, name: str) -> ToolSchema:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]
```

### 4.3 ToolValidator

```python
class ToolValidator:
    def validate(self, schema: ToolSchema, arguments: dict) -> dict:
        validated = {}
        for param in schema.parameters:
            if param.name in arguments:
                validated[param.name] = self._validate_type(param, arguments[param.name])
            elif param.required:
                raise ValidationError(f"Missing required: {param.name}")
            elif param.default is not None:
                validated[param.name] = param.default
        return validated
```

### 4.4 ToolExecutor

```python
class ToolExecutor:
    def execute(self, tool_name: str, arguments: dict) -> ToolResult:
        schema = self._registry.get(tool_name)

        if schema.requires_permission and not self._permission_granted:
            return ToolResult.fail("Permission denied")

        validated = self._validator.validate(schema, arguments)
        handler = self._registry.get_handler(tool_name)
        output = handler(**validated)
        return ToolResult.ok(output)
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Action | 参数类型错误 | `count: "five"` 而不是 `count: 5` |
| Action | 缺少必需参数 | 调用 search 但没有 query |
| Action | 权限被拒绝 | 尝试写文件但没有授权 |
| Action | 工具不存在 | 模型幻觉了一个不存在的工具 |
| Action | 执行超时 | API 调用超过 30 秒 |
| Action | 副作用失败 | 磁盘空间不足，写入失败 |

**工程规则**：
1. 总是在执行前验证参数
2. 总是返回 ToolResult，不要抛出异常
3. 写操作需要显式权限
4. 记录执行历史以便调试

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加参数范围检查**：限制数值参数的范围
2. **添加工具超时**：防止无限等待
3. **添加工具重试**：处理临时错误
4. **添加沙箱边界**：限制文件路径范围
5. **添加工具版本控制**：支持 schema 演进

## 7. Lab

构建一个工具系统，包含：
- 三个内置工具（search, calculator, write_file）
- 参数验证
- 权限控制
- 执行历史

见 `lab/README.md`。

## 8. Evaluation

- 至少三个本地工具
- 无效参数在执行前失败
- 写工具需要显式权限
- 工具结果成为 Observation

## 9. What Changed in Our Agent?

本模块添加了 `tools/` 子包：

- `schema.py`: ToolSchema, ToolParameter
- `registry.py`: ToolRegistry
- `validator.py`: ToolValidator
- `executor.py`: ToolExecutor, ToolResult
- `builtin.py`: 三个内置工具

这些组件让 Agent 可以安全地与环境交互。

## 10. Summary

- Tools 是 Agent 与环境的受控接口
- 每个工具都有 schema 定义参数和权限
- 参数在执行前验证
- 读操作无需权限，写操作需要授权
- 工具结果成为 Observation，进入下一轮决策
- 执行历史用于调试和审计
