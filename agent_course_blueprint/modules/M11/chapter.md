# M11 — Production Delivery & Operations

## Learning Objectives

By the end of this module, the learner can:

- 实现配置管理系统，支持多环境配置
- 实现会话管理，跟踪用户交互
- 实现 Agent 服务，提供 API 接口
- 实现 CLI 工具，支持命令行操作
- 实现监控和可观测性，收集指标和健康检查

## 1. Engineering Problem

将 Agent 系统部署到生产环境面临以下挑战：

1. **配置管理**：不同环境（开发、测试、生产）需要不同配置
2. **会话管理**：需要跟踪用户交互状态
3. **服务化**：需要将 Agent 包装为可访问的服务
4. **命令行工具**：需要提供便捷的 CLI 操作
5. **监控和可观测性**：需要收集指标、健康检查、日志

我们需要一个完整的生产交付框架来支持这些需求。

## 2. Mental Model

### 2.1 Configuration Management

配置管理系统支持多环境配置：

```text
Config = {
    model_provider: str
    model_name: str
    model_api_key: str
    max_steps: int
    max_tokens: int
    temperature: float
    ...
}

ConfigManager:
- load() -> Config
- save(config)
- get_config() -> Config
- apply_env_overrides()
```

### 2.2 Session Management

会话管理跟踪用户交互：

```text
Session = {
    id: str
    agent_id: str
    created_at: str
    updated_at: str
    state: dict
    metadata: dict
    is_active: bool
}

SessionManager:
- create_session(agent_id) -> Session
- get_session(session_id) -> Session
- close_session(session_id)
- list_sessions() -> list[Session]
- cleanup_expired()
```

### 2.3 Agent Service

Agent 服务提供 API 接口：

```text
AgentService:
- run_task(task, session_id) -> dict
- get_status() -> dict
- get_session(session_id) -> dict
- list_sessions() -> list[dict]
- close_session(session_id)
- start()
- stop()
```

### 2.4 CLI Interface

CLI 提供命令行操作：

```text
CLI:
- add_command(command)
- set_agent(agent)
- set_service(service)
- run(args) -> int

Commands:
- run: 运行任务
- serve: 启动服务
- status: 查看状态
```

### 2.5 Monitoring & Observability

监控和可观测性收集指标：

```text
MetricsCollector:
- record_request(latency_ms, tokens, success)
- record_metric(name, value)
- get_average_latency() -> float
- get_error_rate() -> float
- get_summary() -> dict
- reset()

HealthChecker:
- add_check(name, check_fn)
- run_checks() -> dict
- is_healthy() -> bool
- get_status() -> dict
```

## 3. Runtime Walkthrough

### 3.1 Configuration Loading

```python
# 1. 创建配置管理器
config_manager = ConfigManager("config.json")

# 2. 加载配置
config = config_manager.load()

# 3. 使用配置
print(f"Model: {config.model_name}")
print(f"Max steps: {config.max_steps}")
```

### 3.2 Session Management

```python
# 1. 创建会话管理器
session_manager = SessionManager()

# 2. 创建会话
session = session_manager.create_session("agent_1")

# 3. 更新会话状态
session.update_state("last_task", "Research AI")

# 4. 获取会话
retrieved = session_manager.get_session(session.id)

# 5. 关闭会话
session_manager.close_session(session.id)
```

### 3.3 Agent Service

```python
# 1. 创建 Agent
model = FakeModel()
agent = Agent(model=model)

# 2. 创建服务
service = AgentService(agent)

# 3. 运行任务
task = TaskSpec(goal="Research AI trends")
result = service.run_task(task)

# 4. 获取状态
status = service.get_status()
print(f"Requests: {status['request_count']}")
```

### 3.4 CLI Usage

```python
# 1. 创建 CLI
cli = CLI.create_default_cli()
cli.set_agent(agent)
cli.set_service(service)

# 2. 运行命令
cli.run(["run", "--task", "Research AI"])
cli.run(["status"])
```

### 3.5 Monitoring

```python
# 1. 创建指标收集器
metrics = MetricsCollector()

# 2. 记录请求
metrics.record_request(latency_ms=100.0, tokens=50, success=True)

# 3. 获取摘要
summary = metrics.get_summary()
print(f"Average latency: {summary['average_latency_ms']}ms")
print(f"Error rate: {summary['error_rate']}")

# 4. 创建健康检查器
health = HealthChecker()
health.add_check("agent_alive", lambda: agent is not None)

# 5. 运行检查
if health.is_healthy():
    print("System is healthy")
```

## 4. Minimal Implementation

### 4.1 Config

```python
@dataclass
class Config:
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    max_steps: int = 20
    max_tokens: int = 4000
    temperature: float = 0.7
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "max_steps": self.max_steps,
            ...
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        return cls(**data)

class ConfigManager:
    def __init__(self, config_path: str | Path | None = None):
        self._config_path = Path(config_path) if config_path else None
        self._config: Config | None = None
    
    def load(self) -> Config:
        if self._config_path and self._config_path.exists():
            with open(self._config_path, "r") as f:
                data = json.load(f)
            self._config = Config.from_dict(data)
        else:
            self._config = Config()
        self._apply_env_overrides()
        return self._config
    
    def save(self, config: Config) -> None:
        if self._config_path:
            with open(self._config_path, "w") as f:
                json.dump(config.to_dict(), f, indent=2)
```

### 4.2 Session

```python
@dataclass
class Session:
    id: str
    agent_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    state: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def update_state(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def close(self) -> None:
        self.is_active = False

class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
    
    def create_session(self, agent_id: str) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(id=session_id, agent_id=agent_id)
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.close()
            return True
        return False
```

### 4.3 AgentService

```python
class AgentService:
    def __init__(self, agent: Agent, config: Config | None = None):
        self._agent = agent
        self._config = config or Config()
        self._session_manager = SessionManager()
        self._request_count = 0
        self._error_count = 0
    
    def run_task(self, task: TaskSpec, session_id: str | None = None) -> dict[str, Any]:
        self._request_count += 1
        
        if session_id:
            session = self._session_manager.get_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
        else:
            session = self._session_manager.create_session("agent")
            session_id = session.id
        
        try:
            result = self._agent.run(task)
            session.update_state("last_result", result.output)
            return {
                "success": result.success,
                "output": result.output,
                "session_id": session_id,
            }
        except Exception as e:
            self._error_count += 1
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> dict[str, Any]:
        return {
            "status": "running",
            "request_count": self._request_count,
            "error_count": self._error_count,
        }
```

### 4.4 MetricsCollector

```python
@dataclass
class MetricsCollector:
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    
    def record_request(self, latency_ms: float, tokens: int = 0, success: bool = True):
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        if not success:
            self.error_count += 1
    
    def get_average_latency(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count
    
    def get_error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
```

## 5. Failure Modes

| 层级 | 故障 | 示例 |
|------|------|------|
| Reliability | 配置加载失败 | 配置文件不存在或格式错误 |
| Reliability | 环境变量覆盖失败 | 环境变量格式不正确 |
| Memory | 会话丢失 | 会话管理器重启后会话丢失 |
| Resource | 会话泄漏 | 未关闭的会话积累 |
| Reliability | 服务崩溃 | 未捕获的异常导致服务停止 |
| Control | 并发问题 | 多个请求同时修改状态 |
| Evaluation | 指标丢失 | 指标收集器重启后指标丢失 |
| Evaluation | 健康检查误报 | 健康检查返回错误结果 |

**调试规则**：在提出修复方案之前，先将观察到的故障映射到规范分类法的层级（Task, Observation, Context, Policy, Action, Transition, Control, Knowledge, Memory, Composition, Safety, Reliability, Resource, Evaluation）。

**工程规则**：
1. 配置应该可以从环境变量覆盖
2. 会话应该有超时和清理机制
3. 服务应该优雅处理异常
4. 指标应该持久化或定期导出
5. 健康检查应该覆盖关键组件

## 6. Engineering Upgrade

从最小实现到生产级：

1. **添加配置验证**：使用 Pydantic 验证配置
2. **添加会话持久化**：将会话存储到数据库
3. **添加 API 网关**：使用 FastAPI/Flask 提供 REST API
4. **添加认证和授权**：保护 API 端点
5. **添加日志聚合**：使用 ELK/Loki 收集日志
6. **添加分布式追踪**：使用 Jaeger/Zipkin 追踪请求
7. **添加自动扩缩容**：根据负载调整实例数

## 7. Lab

构建一个生产级的 Agent 服务，演示：
- 配置管理
- 会话管理
- 服务化部署
- CLI 操作
- 监控和健康检查

见 `lab/README.md`。

## 8. Evaluation

- Service starts without external credentials in mock mode
- Request has run ID and version metadata
- Concurrent-run state is isolated
- Trace/replay path is documented

## 9. What Changed in Our Agent?

本模块添加了 `api/` 子包：

- `config.py`: Config, ConfigManager
- `session.py`: Session, SessionManager
- `service.py`: AgentService, ServiceConfig
- `cli.py`: CLI, CLICommand
- `monitoring.py`: MetricsCollector, HealthChecker

这些组件让 Agent 可以部署到生产环境，提供服务接口，并被监控和管理。

## 10. Summary

- 配置管理支持多环境配置和环境变量覆盖
- 会话管理跟踪用户交互状态
- Agent 服务提供 API 接口
- CLI 提供命令行操作
- 监控收集指标和健康检查
- 生产部署需要考虑安全性、可靠性、可观测性
- 优雅处理异常，提供错误信息
- 日志和追踪用于调试和分析
