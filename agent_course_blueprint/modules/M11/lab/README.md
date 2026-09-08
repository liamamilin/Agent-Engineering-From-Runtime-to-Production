# Lab — M11 Production Delivery & Operations

## Objective

构建一个生产级的 Agent 服务，演示配置管理、会话管理、服务化部署、CLI 操作和监控。

## Starting State

`reference_agent/src/agent_course/api/` 已有基础实现。

## Task

1. 实现配置管理，支持加载和保存配置
2. 实现会话管理，创建和跟踪会话
3. 实现 Agent 服务，提供任务执行接口
4. 实现 CLI 工具，支持命令行操作
5. 实现监控，收集指标和健康检查

## Required API / Interfaces

```python
from agent_course.api import (
    Config,
    ConfigManager,
    Session,
    SessionManager,
    AgentService,
    ServiceConfig,
    CLI,
    CLICommand,
    MetricsCollector,
    HealthChecker,
)
from agent_course.core import TaskSpec
from agent_course.llm import FakeModel, ModelResponse
from agent_course.runtime import Agent
```

## Step-by-Step Requirements

1. 创建配置管理器，加载和保存配置
2. 创建会话管理器，创建和跟踪会话
3. 创建 Agent 和服务
4. 运行任务，验证会话管理
5. 创建指标收集器，记录请求
6. 创建健康检查器，添加健康检查
7. 验证所有组件协同工作

## Tests to Pass

```bash
pytest modules/M11/lab/tests/
```

## Expected Failure Cases

1. 配置加载失败时应该使用默认配置
2. 会话不存在时应该返回错误
3. 服务异常时应该记录错误

## Reflection Questions

1. 如何设计一个可扩展的配置系统？
2. 如何确保会话的安全性和隐私性？
3. 如何实现高可用的 Agent 服务？
4. 如何设计有效的监控指标？
5. 如何处理生产环境中的异常和故障？
