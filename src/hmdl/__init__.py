"""
Heimdall Observability SDK for MCP Servers.

A Python SDK for instrumenting MCP (Model Context Protocol) servers with
OpenTelemetry-based observability tracking.
"""

from hmdl.client import HeimdallClient
from hmdl.decorators import trace_mcp_tool, UserExtractor, SessionExtractor
from hmdl.config import HeimdallConfig
from hmdl.types import SpanKind, SpanStatus
from hmdl.context import (
    MCPRequestContext,
    mcp_context,
    create_mcp_context,
    set_mcp_context,
    get_mcp_context,
    clear_mcp_context,
    parse_jwt_claims,
    extract_user_id_from_token,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "HeimdallClient",
    # Decorators
    "trace_mcp_tool",
    "UserExtractor",
    "SessionExtractor",
    # Configuration
    "HeimdallConfig",
    # Types
    "SpanKind",
    "SpanStatus",
    # MCP Context
    "MCPRequestContext",
    "mcp_context",
    "create_mcp_context",
    "set_mcp_context",
    "get_mcp_context",
    "clear_mcp_context",
    "parse_jwt_claims",
    "extract_user_id_from_token",
    # Version
    "__version__",
]

