"""
Heimdall Observability SDK for MCP Servers.

A Python SDK for instrumenting MCP (Model Context Protocol) servers with
OpenTelemetry-based observability tracking.
"""

from hmdl.client import HeimdallClient
from hmdl.decorators import trace_mcp_tool
from hmdl.config import HeimdallConfig
from hmdl.types import SpanKind, SpanStatus

__version__ = "0.1.0"

__all__ = [
    # Client
    "HeimdallClient",
    # Decorators
    "trace_mcp_tool",
    # Configuration
    "HeimdallConfig",
    # Types
    "SpanKind",
    "SpanStatus",
    # Version
    "__version__",
]

