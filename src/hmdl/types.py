"""Type definitions for Heimdall SDK."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime


class SpanKind(str, Enum):
    """Kind of span being recorded."""
    
    MCP_TOOL = "mcp.tool"
    MCP_RESOURCE = "mcp.resource"
    MCP_PROMPT = "mcp.prompt"
    MCP_REQUEST = "mcp.request"
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"


class SpanStatus(str, Enum):
    """Status of a span."""
    
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class MCPToolCall:
    """Represents an MCP tool call."""
    
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MCPResourceAccess:
    """Represents an MCP resource access."""
    
    uri: str
    method: str = "read"
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MCPPromptCall:
    """Represents an MCP prompt call."""
    
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TraceContext:
    """Context for a trace."""
    
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


# Attribute keys for OpenTelemetry spans
class HeimdallAttributes:
    """Standard attribute keys for Heimdall spans."""
    
    # MCP specific attributes
    MCP_TOOL_NAME = "mcp.tool.name"
    MCP_TOOL_ARGUMENTS = "mcp.tool.arguments"
    MCP_TOOL_RESULT = "mcp.tool.result"
    
    MCP_RESOURCE_URI = "mcp.resource.uri"
    MCP_RESOURCE_METHOD = "mcp.resource.method"
    MCP_RESOURCE_CONTENT_TYPE = "mcp.resource.content_type"
    MCP_RESOURCE_CONTENT_LENGTH = "mcp.resource.content_length"
    
    MCP_PROMPT_NAME = "mcp.prompt.name"
    MCP_PROMPT_ARGUMENTS = "mcp.prompt.arguments"
    MCP_PROMPT_MESSAGES = "mcp.prompt.messages"
    
    # Heimdall specific attributes
    HEIMDALL_SESSION_ID = "heimdall.session_id"
    HEIMDALL_USER_ID = "heimdall.user_id"
    HEIMDALL_ENVIRONMENT = "heimdall.environment"
    HEIMDALL_SERVICE_NAME = "heimdall.service_name"
    HEIMDALL_PROJECT_ID = "heimdall.project_id"
    
    # Status and error attributes
    STATUS = "heimdall.status"
    ERROR_MESSAGE = "heimdall.error.message"
    ERROR_TYPE = "heimdall.error.type"
    
    # Timing attributes
    DURATION_MS = "heimdall.duration_ms"

