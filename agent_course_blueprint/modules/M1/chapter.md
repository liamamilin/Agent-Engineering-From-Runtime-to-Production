# M1 — Model Runtime & Structured Interaction

## Learning Objectives

By the end of this module, the learner can:

- 实现一个 provider-independent 的 Model 接口
- 理解 request/response 生命周期
- 处理消息角色（roles）和指令层
- 解析和验证结构化输出（structured output）
- 实现重试（retry）和超时（timeout）策略
- 解释为什么 Model 是运行时依赖，而不是 Agent 本身

## 1. Engineering Problem

Agent 需要与 LLM 交互，但 LLM API 有以下问题：

1. **Provider 差异**：OpenAI、Anthropic、本地模型各有不同的 API 格式
2. **不可靠性**：网络超时、速率限制、临时错误
3. **输出不确定性**：模型可能返回非结构化或格式错误的内容
4. **成本**：token 消耗需要跟踪和控制

我们需要一个抽象层，将这些复杂性封装起来，让 Agent 的其他部分可以专注于决策逻辑。

## 2. Mental Model

### 2.1 Model as Runtime Dependency

Model 是 Agent 运行时的一个**组件**，不是 Agent 本身。

```text
+----------------------------- AGENT RUNTIME -----------------------------+
|                                                                         |
|   +-------------+                                                       |
|   |   Context   | -> messages -> +-------------+ -> response -> Decision|
|   |   Builder   |                | ModelAdapter|                        |
|   +-------------+                +-------------+                        |
|                                       |                                 |
|                                       v                                 |
|                                 +-------------+                         |
|                                 |   Provider  |  <-- 在边界外            |
|                                 |  (OpenAI,   |                         |
|                                 |  Anthropic, |                         |
|                                 |  Local)     |                         |
|                                 +-------------+                         |
|                                                                         |
+-------------------------------------------------------------------------+
```

关键洞察：
- ModelAdapter 是边界内的接口
- Provider（OpenAI API 等）是边界外的环境
- Agent 不直接依赖任何特定 provider

### 2.2 Request/Response Lifecycle

一次模型调用包含以下阶段：

```text
1. Build Messages     # 构建消息列表
       |
       v
2. Serialize          # 转换为 provider 格式
       |
       v
3. Send Request       # HTTP 请求
       |
       v
4. Handle Response    # 解析响应
       |
       v
5. Extract Content    # 提取文本和工具调用
       |
       v
6. Track Usage        # 记录 token 使用
```

### 2.3 Message Roles

消息有四种角色：

| Role | 用途 | 示例 |
|------|------|------|
| `system` | 设置 Agent 行为和约束 | "你是一个研究助手" |
| `user` | 用户输入或任务描述 | "搜索关于 X 的信息" |
| `assistant` | 模型之前的响应 | "我将搜索 X" |
| `tool` | 工具执行结果 | "搜索结果：..." |

## 3. Runtime Walkthrough

```python
# 1. 构建消息
messages = [
    Message.system("你是一个有帮助的助手。"),
    Message.user("搜索 Python 教程"),
]

# 2. 定义可用工具
tools = [
    {
        "name": "search",
        "description": "搜索网络",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
]

# 3. 调用模型
response = model.complete(messages, tools=tools)

# 4. 检查响应类型
if response.has_tool_calls:
    # 模型决定调用工具
    tool_call = response.tool_calls[0]
    tool_name = tool_call["name"]
    tool_args = tool_call["arguments"]
else:
    # 模型直接回复
    content = response.content

# 5. 跟踪使用量
print(f"Tokens: {response.total_tokens}")
```

## 4. Minimal Implementation

### 4.1 ModelAdapter Interface

```python
class ModelAdapter:
    """Provider-independent model interface."""

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> ModelResponse:
        """Generate a completion."""
        return self._call(messages, tools, temperature, max_tokens)

    def _call(self, messages, tools, temperature, max_tokens) -> ModelResponse:
        raise NotImplementedError
```

### 4.2 FakeModel for Testing

```python
class FakeModel(ModelAdapter):
    """Deterministic fake model for offline tests."""

    def __init__(self, responses: list[ModelResponse] | None = None):
        self._responses = list(responses) if responses else []
        self._call_count = 0

    def _call(self, messages, tools, temperature, max_tokens) -> ModelResponse:
        if self._call_count < len(self._responses):
            response = self._responses[self._call_count]
        else:
            response = ModelResponse(content="I don't know.")
        self._call_count += 1
        return response
```

### 4.3 Structured Output

```python
class StructuredOutput:
    @staticmethod
    def parse_json(content: str) -> dict:
        """Extract JSON from model response."""
        import json
        import re

        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from code block
        match = re.search(r"```json?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        raise ValueError(f"Could not parse JSON: {content[:100]}...")
```

### 4.4 Retry Policy

```python
class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func: Callable) -> ModelResponse:
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except RetryableError as e:
                if attempt == self.max_retries:
                    raise
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Reliability | 网络超时 | API 请求超过 30 秒 |
| Reliability | 速率限制 | 429 Too Many Requests |
| Policy | 格式错误 | 模型返回非 JSON 的结构化输出 |
| Policy | 幻觉工具 | 模型调用不存在的工具 |
| Resource | Token 超限 | 上下文太长，超出模型限制 |
| Action | 参数错误 | 工具参数类型不匹配 |

**工程规则**：
1. 总是实现重试逻辑
2. 总是验证结构化输出
3. 总是跟踪 token 使用
4. 使用 FakeModel 进行离线测试

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加超时**：防止无限等待
2. **添加指数退避**：避免速率限制
3. **添加 token 计数**：在发送前检查上下文长度
4. **添加响应缓存**：减少重复调用
5. **添加 provider 路由**：自动切换到备用 provider

## 7. Lab

构建一个 ModelAdapter 实现，支持：
- 消息角色
- 工具调用
- 结构化输出解析
- 重试逻辑

见 `lab/README.md`。

## 8. Evaluation

- FakeModel 通过离线测试
- 结构化输出可以解析和验证
- 重试逻辑处理临时错误
- 故障被显式报告

## 9. What Changed in Our Agent?

本模块添加了 `llm/` 子包：

- `base.py`: ModelAdapter 接口、Message、ModelResponse
- `fake.py`: FakeModel 用于离线测试
- `structured.py`: 结构化输出解析和验证
- `retry.py`: 重试策略

这些组件让 Agent 可以与 LLM 交互，同时保持可测试性和 provider 独立性。

## 10. Summary

- Model 是 Agent 的组件，不是 Agent 本身
- ModelAdapter 封装 provider 差异
- 消息有四种角色：system、user、assistant、tool
- 结构化输出需要解析和验证
- 重试逻辑处理临时错误
- 使用 FakeModel 进行离线测试
- 跟踪 token 使用以控制成本
