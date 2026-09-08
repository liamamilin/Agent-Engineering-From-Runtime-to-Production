# Exercises — M11

## Exercise 1: Advanced Configuration

实现一个高级配置系统，支持配置继承和验证：

```python
class AdvancedConfig(Config):
    def validate(self) -> list[str]:
        """Validate configuration.
        
        Returns:
            List of validation errors.
        """
        # 你的实现：验证必填字段、值范围等
        pass
    
    def merge(self, other: Config) -> Config:
        """Merge with another config.
        
        Args:
            other: Config to merge with.
            
        Returns:
            Merged config.
        """
        # 你的实现：other 的值覆盖 self 的值
        pass
```

**问题**：
1. 如何处理配置冲突？
2. 如何验证配置的有效性？
3. 如何支持配置的版本控制？

---

## Exercise 2: Persistent Session Storage

实现一个持久化的会话存储：

```python
class PersistentSessionManager(SessionManager):
    def __init__(self, storage_path: str | Path):
        """Initialize with storage path.
        
        Args:
            storage_path: Path to store sessions.
        """
        # 你的实现
        pass
    
    def save_session(self, session: Session) -> None:
        """Save session to storage."""
        # 你的实现
        pass
    
    def load_session(self, session_id: str) -> Session | None:
        """Load session from storage."""
        # 你的实现
        pass
```

**问题**：
1. 如何选择存储格式（JSON、SQLite、Redis）？
2. 如何处理并发访问？
3. 如何实现会话过期和清理？

---

## Exercise 3: REST API Service

实现一个 REST API 服务：

```python
class RESTAgentService(AgentService):
    def __init__(self, agent: Agent, host: str = "0.0.0.0", port: int = 8000):
        # 你的实现
        pass
    
    def start(self) -> None:
        """Start the REST API server."""
        # 你的实现：使用 FastAPI 或 Flask
        pass
    
    def stop(self) -> None:
        """Stop the server."""
        # 你的实现
        pass
```

**问题**：
1. 如何设计 API 端点？
2. 如何处理认证和授权？
3. 如何实现速率限制？

---

## Exercise 4: Distributed Metrics

实现一个分布式指标收集器：

```python
class DistributedMetricsCollector(MetricsCollector):
    def __init__(self, service_name: str, export_interval: int = 60):
        """Initialize distributed metrics collector.
        
        Args:
            service_name: Name of the service.
            export_interval: Interval to export metrics in seconds.
        """
        # 你的实现
        pass
    
    def export_metrics(self) -> dict[str, Any]:
        """Export metrics to external system."""
        # 你的实现：导出到 Prometheus、Datadog 等
        pass
```

**问题**：
1. 如何聚合多个实例的指标？
2. 如何处理指标丢失？
3. 如何设置告警阈值？
