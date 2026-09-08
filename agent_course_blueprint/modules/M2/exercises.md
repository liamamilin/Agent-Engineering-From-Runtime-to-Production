# Exercises — M2

## Exercise 1: Custom Tool

实现一个自定义工具 `weather`，返回给定城市的天气（fake 实现）。

```python
from agent_course.tools import ToolSchema, ToolParameter, ParameterType

weather_schema = ToolSchema(
    name="weather",
    description="Get weather for a city",
    parameters=[
        # 你的实现
    ],
    requires_permission=False,
)

def weather_handler(city: str) -> dict:
    # 你的实现
    pass
```

**问题**：
1. 这个工具是幂等的吗？
2. 需要权限吗？
3. 如何处理无效的城市名？

---

## Exercise 2: Permission System

设计一个权限系统，支持：
- 工具级别的权限
- 参数级别的限制（例如，只能写入特定目录）

```python
class PermissionManager:
    def check_permission(self, tool_name: str, arguments: dict) -> bool:
        # 你的实现
        pass
```

---

## Exercise 3: Tool Retry

实现一个工具执行重试机制：

```python
class RetryingToolExecutor(ToolExecutor):
    def execute(self, tool_name: str, arguments: dict, max_retries: int = 3) -> ToolResult:
        # 你的实现
        pass
```

**问题**：
1. 哪些工具错误应该重试？
2. 哪些不应该重试？

---

## Exercise 4: Tool Composition

实现一个复合工具 `search_and_summarize`，内部调用 search 工具并总结结果。

**问题**：
1. 复合工具应该有自己的 schema 吗？
2. 如何处理内部工具的失败？
