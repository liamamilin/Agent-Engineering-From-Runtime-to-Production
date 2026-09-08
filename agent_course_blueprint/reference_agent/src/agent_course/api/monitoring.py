"""Monitoring and observability for agent systems."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class MetricsCollector:
    """Collects metrics for agent systems."""
    
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    custom_metrics: dict[str, float] = field(default_factory=dict)
    
    def record_request(self, latency_ms: float, tokens: int = 0, success: bool = True) -> None:
        """Record a request.
        
        Args:
            latency_ms: Request latency in milliseconds.
            tokens: Number of tokens used.
            success: Whether the request was successful.
        """
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        
        if not success:
            self.error_count += 1
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a custom metric.
        
        Args:
            name: Metric name.
            value: Metric value.
        """
        if name not in self.custom_metrics:
            self.custom_metrics[name] = 0.0
        self.custom_metrics[name] += value
    
    def get_average_latency(self) -> float:
        """Get average latency.
        
        Returns:
            Average latency in milliseconds.
        """
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count
    
    def get_error_rate(self) -> float:
        """Get error rate.
        
        Returns:
            Error rate (0.0 to 1.0).
        """
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary.
        
        Returns:
            Summary dictionary.
        """
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.get_error_rate(),
            "average_latency_ms": self.get_average_latency(),
            "total_tokens": self.total_tokens,
            "custom_metrics": self.custom_metrics.copy(),
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.request_count = 0
        self.error_count = 0
        self.total_latency_ms = 0.0
        self.total_tokens = 0
        self.custom_metrics.clear()


@dataclass
class HealthChecker:
    """Checks health of agent systems."""
    
    checks: dict[str, Callable[[], bool]] = field(default_factory=dict)
    last_check_time: float = 0.0
    last_check_result: dict[str, bool] = field(default_factory=dict)
    
    def add_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Add a health check.
        
        Args:
            name: Check name.
            check_fn: Check function that returns True if healthy.
        """
        self.checks[name] = check_fn
    
    def run_checks(self) -> dict[str, bool]:
        """Run all health checks.
        
        Returns:
            Dictionary of check name to result.
        """
        results = {}
        
        for name, check_fn in self.checks.items():
            try:
                results[name] = check_fn()
            except Exception:
                results[name] = False
        
        self.last_check_time = time.time()
        self.last_check_result = results
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if system is healthy.
        
        Returns:
            True if all checks pass, False otherwise.
        """
        if not self.last_check_result:
            self.run_checks()
        
        return all(self.last_check_result.values())
    
    def get_status(self) -> dict[str, Any]:
        """Get health status.
        
        Returns:
            Status dictionary.
        """
        if not self.last_check_result:
            self.run_checks()
        
        return {
            "healthy": self.is_healthy(),
            "checks": self.last_check_result.copy(),
            "last_check_time": self.last_check_time,
        }
