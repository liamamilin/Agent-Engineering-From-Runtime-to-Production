# Exercises — M1

## Exercise 1: Provider Adapter

设计一个 OpenAI provider adapter，实现 ModelAdapter 接口。

```python
class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        # 你的实现
        pass

    def _call(self, messages, tools, temperature, max_tokens):
        # 你的实现
        pass
```

**问题**：
1. 如何处理 API key？
2. 如何将 Message 转换为 OpenAI API 格式？
3. 如何处理工具调用响应？

---

## Exercise 2: Structured Output

给定以下模型响应，提取 JSON：

```
根据我的分析，答案是：

```json
{
    "answer": "42",
    "reasoning": "The answer to life, universe, and everything",
    "confidence": 0.85
}
```

希望这有帮助！
```

编写代码解析这个响应。

---

## Exercise 3: Retry Strategy

设计一个重试策略，处理以下情况：

1. 网络超时（503 Service Unavailable）
2. 速率限制（429 Too Many Requests）
3. 服务器错误（500 Internal Server Error）

**问题**：
1. 哪些错误应该重试？
2. 重试间隔应该如何设计？
3. 最大重试次数应该是多少？

---

## Exercise 4: Token Budget

实现一个函数，在发送请求前检查消息的 token 数量：

```python
def check_token_budget(messages: list[Message], max_tokens: int) -> bool:
    """Check if messages fit within token budget."""
    # 你的实现
    pass
```

**问题**：
1. 如何估算 token 数量？
2. 如果超出预算，应该如何处理？
