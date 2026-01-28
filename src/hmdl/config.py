"""Configuration for Heimdall SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class HeimdallConfig:
    """Configuration for the Heimdall observability client.
    
    Attributes:
        api_key: API key for authenticating with Heimdall platform.
        endpoint: The Heimdall platform endpoint URL.
        service_name: Name of the service being instrumented.
        environment: Deployment environment (e.g., 'production', 'staging').
        enabled: Whether tracing is enabled.
        debug: Enable debug logging.
        batch_size: Number of spans to batch before sending.
        flush_interval_ms: Interval in milliseconds to flush spans.
        max_queue_size: Maximum number of spans to queue.
        metadata: Additional metadata to attach to all spans.
    """
    
    api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("HEIMDALL_API_KEY")
    )
    endpoint: str = field(
        default_factory=lambda: os.environ.get(
            "HEIMDALL_ENDPOINT", "https://api.heimdall.dev"
        )
    )
    service_name: str = field(
        default_factory=lambda: os.environ.get("HEIMDALL_SERVICE_NAME", "mcp-server")
    )
    environment: str = field(
        default_factory=lambda: os.environ.get("HEIMDALL_ENVIRONMENT", "development")
    )
    enabled: bool = field(
        default_factory=lambda: os.environ.get("HEIMDALL_ENABLED", "true").lower() == "true"
    )
    debug: bool = field(
        default_factory=lambda: os.environ.get("HEIMDALL_DEBUG", "false").lower() == "true"
    )
    batch_size: int = field(
        default_factory=lambda: int(os.environ.get("HEIMDALL_BATCH_SIZE", "100"))
    )
    flush_interval_ms: int = field(
        default_factory=lambda: int(os.environ.get("HEIMDALL_FLUSH_INTERVAL_MS", "5000"))
    )
    max_queue_size: int = field(
        default_factory=lambda: int(os.environ.get("HEIMDALL_MAX_QUEUE_SIZE", "1000"))
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate the configuration."""
        # API key is optional for local development
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.flush_interval_ms < 100:
            raise ValueError("flush_interval_ms must be at least 100")
        if self.max_queue_size < self.batch_size:
            raise ValueError("max_queue_size must be at least batch_size")
    
    @classmethod
    def from_env(cls) -> "HeimdallConfig":
        """Create configuration from environment variables."""
        return cls()

