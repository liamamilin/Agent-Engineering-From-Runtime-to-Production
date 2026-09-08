"""Configuration management for agent systems."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Configuration for an agent system."""
    
    # Model configuration
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    model_api_key: str = ""
    model_base_url: str = ""
    
    # Agent configuration
    max_steps: int = 20
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Safety configuration
    require_permissions: bool = True
    enable_guardrails: bool = True
    budget_tokens: int = 10000
    budget_steps: int = 50
    
    # Service configuration
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    service_workers: int = 1
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: str = ""
    
    # Additional settings
    settings: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "model_api_key": self.model_api_key,
            "model_base_url": self.model_base_url,
            "max_steps": self.max_steps,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "require_permissions": self.require_permissions,
            "enable_guardrails": self.enable_guardrails,
            "budget_tokens": self.budget_tokens,
            "budget_steps": self.budget_steps,
            "service_host": self.service_host,
            "service_port": self.service_port,
            "service_workers": self.service_workers,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "settings": self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from dictionary."""
        return cls(**data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.settings[key] = value


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize config manager.
        
        Args:
            config_path: Path to configuration file.
        """
        self._config_path = Path(config_path) if config_path else None
        self._config: Config | None = None
    
    def load(self) -> Config:
        """Load configuration from file.
        
        Returns:
            Loaded configuration.
        """
        if self._config_path and self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = Config.from_dict(data)
        else:
            self._config = Config()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        return self._config
    
    def save(self, config: Config) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save.
        """
        if self._config_path:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
    
    def get_config(self) -> Config:
        """Get current configuration.
        
        Returns:
            Current configuration.
        """
        if self._config is None:
            return self.load()
        return self._config
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if self._config is None:
            return
        
        env_mappings = {
            "AGENT_MODEL_PROVIDER": "model_provider",
            "AGENT_MODEL_NAME": "model_name",
            "AGENT_MODEL_API_KEY": "model_api_key",
            "AGENT_MODEL_BASE_URL": "model_base_url",
            "AGENT_MAX_STEPS": ("max_steps", int),
            "AGENT_MAX_TOKENS": ("max_tokens", int),
            "AGENT_TEMPERATURE": ("temperature", float),
            "AGENT_SERVICE_HOST": "service_host",
            "AGENT_SERVICE_PORT": ("service_port", int),
            "AGENT_LOG_LEVEL": "log_level",
        }
        
        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(mapping, tuple):
                    key, converter = mapping
                    self._config.set(key, converter(value))
                else:
                    self._config.set(mapping, value)
