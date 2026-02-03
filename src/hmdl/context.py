"""MCP request context management for automatic session and user tracking.

This module provides utilities for capturing and propagating MCP HTTP request context
(headers, tokens) to be automatically used by decorators for session and user tracking.
"""

from __future__ import annotations

import base64
import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar

# Context variable to store the current MCP request context
_mcp_context: ContextVar[Optional["MCPRequestContext"]] = ContextVar(
    "mcp_context", default=None
)

# MCP Header names
MCP_SESSION_ID_HEADER = "Mcp-Session-Id"
AUTHORIZATION_HEADER = "Authorization"


@dataclass
class MCPRequestContext:
    """Context object containing MCP request information.
    
    This captures HTTP headers from an MCP request, allowing automatic
    extraction of session ID and user ID from headers and tokens.
    
    Attributes:
        session_id: The MCP session ID from the Mcp-Session-Id header
        user_id: The user ID extracted from the OAuth/JWT token
        headers: Raw headers dictionary for additional access
        token_claims: Decoded JWT claims (if Authorization header contained a JWT)
    """
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    token_claims: Dict[str, Any] = field(default_factory=dict)


def parse_jwt_claims(token: str) -> Dict[str, Any]:
    """Parse claims from a JWT token without verification.
    
    This extracts the payload claims from a JWT token. Note that this does NOT
    verify the token signature - that should be done by your authentication layer.
    
    Args:
        token: The JWT token string (with or without 'Bearer ' prefix)
        
    Returns:
        Dictionary of claims from the JWT payload, or empty dict if parsing fails
        
    Example:
        >>> claims = parse_jwt_claims("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.xxx")
        >>> claims.get("sub")
        'user-123'
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.lower().startswith("bearer "):
            token = token[7:]
        
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        
        # Decode the payload (middle part)
        payload = parts[1]
        
        # Add padding if needed (base64url encoding)
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        
        # Decode base64url
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from a JWT token.
    
    Looks for the 'sub' (subject) claim which is the standard JWT claim for user ID.
    Also checks for common alternative claims like 'user_id', 'userId', 'uid'.
    
    Args:
        token: The JWT token string (with or without 'Bearer ' prefix)
        
    Returns:
        The user ID string if found, None otherwise
    """
    claims = parse_jwt_claims(token)
    
    # Try standard 'sub' claim first, then common alternatives
    for claim_name in ("sub", "user_id", "userId", "uid", "user"):
        if claim_name in claims:
            value = claims[claim_name]
            if isinstance(value, str) and value:
                return value
    
    return None


def create_mcp_context(headers: Dict[str, str]) -> MCPRequestContext:
    """Create an MCPRequestContext from HTTP headers.
    
    This extracts the MCP session ID from the Mcp-Session-Id header and
    the user ID from the Authorization header (if it contains a JWT).
    
    Args:
        headers: Dictionary of HTTP headers (case-insensitive keys supported)
        
    Returns:
        MCPRequestContext with session_id and user_id populated
        
    Example:
        >>> headers = {
        ...     "Mcp-Session-Id": "session-abc123",
        ...     "Authorization": "Bearer eyJhbGciOi..."
        ... }
        >>> ctx = create_mcp_context(headers)
        >>> ctx.session_id
        'session-abc123'
    """
    # Normalize header keys to handle case-insensitivity
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    
    # Extract session ID
    session_id = (
        normalized_headers.get(MCP_SESSION_ID_HEADER.lower()) or
        normalized_headers.get("mcp-session-id") or
        headers.get(MCP_SESSION_ID_HEADER)
    )
    
    # Extract user ID from Authorization header
    user_id: Optional[str] = None
    token_claims: Dict[str, Any] = {}
    
    auth_header = (
        normalized_headers.get(AUTHORIZATION_HEADER.lower()) or
        normalized_headers.get("authorization") or
        headers.get(AUTHORIZATION_HEADER)
    )
    
    if auth_header:
        token_claims = parse_jwt_claims(auth_header)
        user_id = extract_user_id_from_token(auth_header)
    
    return MCPRequestContext(
        session_id=session_id,
        user_id=user_id,
        headers=headers,
        token_claims=token_claims,
    )


def set_mcp_context(ctx: Optional[MCPRequestContext]) -> None:
    """Set the current MCP request context.

    This stores the context in a context variable, making it available
    to all decorators in the current execution context.

    Args:
        ctx: The MCPRequestContext to set, or None to clear

    Example:
        >>> ctx = create_mcp_context(request.headers)
        >>> set_mcp_context(ctx)
        >>> # Now all @trace_mcp_tool decorated functions will use this context
    """
    _mcp_context.set(ctx)


def get_mcp_context() -> Optional[MCPRequestContext]:
    """Get the current MCP request context.

    Returns:
        The current MCPRequestContext if set, None otherwise
    """
    return _mcp_context.get()


def clear_mcp_context() -> None:
    """Clear the current MCP request context."""
    _mcp_context.set(None)


F = TypeVar("F", bound=Callable[..., Any])


class mcp_context:
    """Context manager and decorator for setting MCP request context.

    Can be used as a context manager or decorator to automatically set
    and clear the MCP context.

    Example as context manager:
        >>> with mcp_context(request.headers):
        ...     result = my_tool()  # Will have access to session/user from headers

    Example as decorator:
        >>> @mcp_context.from_headers(lambda: get_current_request().headers)
        ... def my_handler():
        ...     result = my_tool()  # Will have access to session/user from headers
    """

    def __init__(self, headers: Optional[Dict[str, str]] = None, ctx: Optional[MCPRequestContext] = None):
        """Initialize with headers or an existing context.

        Args:
            headers: HTTP headers dictionary to create context from
            ctx: An existing MCPRequestContext to use
        """
        if ctx is not None:
            self._ctx = ctx
        elif headers is not None:
            self._ctx = create_mcp_context(headers)
        else:
            self._ctx = None
        self._token = None

    def __enter__(self) -> Optional[MCPRequestContext]:
        """Enter the context, setting the MCP context."""
        self._token = _mcp_context.set(self._ctx)
        return self._ctx

    def __exit__(self, *args: Any) -> None:
        """Exit the context, restoring the previous MCP context."""
        if self._token is not None:
            _mcp_context.reset(self._token)

    @staticmethod
    def from_headers(headers_getter: Callable[[], Dict[str, str]]) -> Callable[[F], F]:
        """Create a decorator that extracts headers using a getter function.

        This is useful for frameworks where headers are available via a function call
        (like Flask's request object).

        Args:
            headers_getter: Function that returns the current request headers

        Returns:
            Decorator that wraps functions with MCP context

        Example:
            >>> @mcp_context.from_headers(lambda: dict(request.headers))
            ... def my_endpoint():
            ...     return my_tool()  # Will have MCP context set
        """
        import functools
        import inspect

        def decorator(func: F) -> F:
            if inspect.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    headers = headers_getter()
                    with mcp_context(headers=headers):
                        return await func(*args, **kwargs)
                return async_wrapper  # type: ignore
            else:
                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    headers = headers_getter()
                    with mcp_context(headers=headers):
                        return func(*args, **kwargs)
                return sync_wrapper  # type: ignore
        return decorator

