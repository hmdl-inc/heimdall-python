"""Tests for MCP context management and JWT parsing."""

import asyncio
import base64
import json
import pytest

from hmdl.context import (
    MCPRequestContext,
    parse_jwt_claims,
    extract_user_id_from_token,
    create_mcp_context,
    set_mcp_context,
    get_mcp_context,
    clear_mcp_context,
    mcp_context,
    MCP_SESSION_ID_HEADER,
    AUTHORIZATION_HEADER,
)


def create_jwt_token(claims: dict) -> str:
    """Helper to create a JWT token for testing (without signature verification)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).rstrip(b"=").decode()
    signature = "test_signature"
    return f"{header}.{payload}.{signature}"


class TestParseJwtClaims:
    """Tests for parse_jwt_claims function."""

    def test_parse_valid_jwt(self):
        """Test parsing a valid JWT token."""
        token = create_jwt_token({"sub": "user-123", "name": "Test User"})
        claims = parse_jwt_claims(token)
        assert claims["sub"] == "user-123"
        assert claims["name"] == "Test User"

    def test_parse_jwt_with_bearer_prefix(self):
        """Test parsing JWT with Bearer prefix."""
        token = create_jwt_token({"sub": "user-456"})
        claims = parse_jwt_claims(f"Bearer {token}")
        assert claims["sub"] == "user-456"

    def test_parse_jwt_with_lowercase_bearer(self):
        """Test parsing JWT with lowercase bearer prefix."""
        token = create_jwt_token({"sub": "user-789"})
        claims = parse_jwt_claims(f"bearer {token}")
        assert claims["sub"] == "user-789"

    def test_parse_invalid_jwt_returns_empty(self):
        """Test parsing invalid JWT returns empty dict."""
        assert parse_jwt_claims("not-a-jwt") == {}
        assert parse_jwt_claims("only.two.parts.here.extra") == {}
        assert parse_jwt_claims("") == {}

    def test_parse_jwt_with_invalid_base64(self):
        """Test parsing JWT with invalid base64 returns empty dict."""
        assert parse_jwt_claims("header.!!!invalid!!!.signature") == {}


class TestExtractUserIdFromToken:
    """Tests for extract_user_id_from_token function."""

    def test_extract_sub_claim(self):
        """Test extracting user ID from 'sub' claim."""
        token = create_jwt_token({"sub": "user-123"})
        assert extract_user_id_from_token(token) == "user-123"

    def test_extract_user_id_claim(self):
        """Test extracting user ID from 'user_id' claim."""
        token = create_jwt_token({"user_id": "user-456"})
        assert extract_user_id_from_token(token) == "user-456"

    def test_extract_userId_claim(self):
        """Test extracting user ID from 'userId' claim."""
        token = create_jwt_token({"userId": "user-789"})
        assert extract_user_id_from_token(token) == "user-789"

    def test_extract_uid_claim(self):
        """Test extracting user ID from 'uid' claim."""
        token = create_jwt_token({"uid": "user-abc"})
        assert extract_user_id_from_token(token) == "user-abc"

    def test_sub_takes_precedence(self):
        """Test that 'sub' claim takes precedence over others."""
        token = create_jwt_token({"sub": "primary", "user_id": "secondary"})
        assert extract_user_id_from_token(token) == "primary"

    def test_returns_none_for_missing_claims(self):
        """Test returns None when no user ID claims present."""
        token = create_jwt_token({"name": "Test", "email": "test@example.com"})
        assert extract_user_id_from_token(token) is None

    def test_returns_none_for_invalid_token(self):
        """Test returns None for invalid token."""
        assert extract_user_id_from_token("invalid-token") is None


class TestCreateMCPContext:
    """Tests for create_mcp_context function."""

    def test_extract_session_id(self):
        """Test extracting session ID from headers."""
        headers = {MCP_SESSION_ID_HEADER: "session-abc123"}
        ctx = create_mcp_context(headers)
        assert ctx.session_id == "session-abc123"

    def test_extract_session_id_case_insensitive(self):
        """Test session ID extraction is case-insensitive."""
        headers = {"mcp-session-id": "session-xyz"}
        ctx = create_mcp_context(headers)
        assert ctx.session_id == "session-xyz"

    def test_extract_user_id_from_auth_header(self):
        """Test extracting user ID from Authorization header."""
        token = create_jwt_token({"sub": "user-123"})
        headers = {AUTHORIZATION_HEADER: f"Bearer {token}"}
        ctx = create_mcp_context(headers)
        assert ctx.user_id == "user-123"

    def test_extract_both_session_and_user(self):
        """Test extracting both session ID and user ID."""
        token = create_jwt_token({"sub": "user-456"})
        headers = {
            MCP_SESSION_ID_HEADER: "session-789",
            AUTHORIZATION_HEADER: f"Bearer {token}",
        }
        ctx = create_mcp_context(headers)
        assert ctx.session_id == "session-789"
        assert ctx.user_id == "user-456"

    def test_stores_raw_headers(self):
        """Test that raw headers are stored in context."""
        headers = {"X-Custom-Header": "custom-value", MCP_SESSION_ID_HEADER: "sess"}
        ctx = create_mcp_context(headers)
        assert ctx.headers == headers

    def test_stores_token_claims(self):
        """Test that token claims are stored in context."""
        token = create_jwt_token({"sub": "user", "role": "admin"})
        headers = {AUTHORIZATION_HEADER: f"Bearer {token}"}
        ctx = create_mcp_context(headers)
        assert ctx.token_claims["sub"] == "user"
        assert ctx.token_claims["role"] == "admin"

    def test_empty_headers(self):
        """Test with empty headers."""
        ctx = create_mcp_context({})
        assert ctx.session_id is None
        assert ctx.user_id is None


class TestMCPContextManagement:
    """Tests for context management functions."""

    def test_set_and_get_context(self):
        """Test setting and getting MCP context."""
        ctx = MCPRequestContext(session_id="sess-1", user_id="user-1")
        set_mcp_context(ctx)

        retrieved = get_mcp_context()
        assert retrieved is not None
        assert retrieved.session_id == "sess-1"
        assert retrieved.user_id == "user-1"

        clear_mcp_context()

    def test_clear_context(self):
        """Test clearing MCP context."""
        ctx = MCPRequestContext(session_id="sess-2")
        set_mcp_context(ctx)
        clear_mcp_context()

        assert get_mcp_context() is None

    def test_context_manager_with_headers(self):
        """Test mcp_context as context manager with headers."""
        headers = {MCP_SESSION_ID_HEADER: "session-cm"}

        with mcp_context(headers=headers) as ctx:
            assert ctx is not None
            assert ctx.session_id == "session-cm"

            # Context should be available via get_mcp_context
            current = get_mcp_context()
            assert current is not None
            assert current.session_id == "session-cm"

        # Context should be cleared after exiting
        assert get_mcp_context() is None

    def test_context_manager_with_existing_context(self):
        """Test mcp_context with pre-created context."""
        ctx = MCPRequestContext(session_id="pre-created", user_id="user-pre")

        with mcp_context(ctx=ctx) as entered_ctx:
            assert entered_ctx.session_id == "pre-created"
            assert entered_ctx.user_id == "user-pre"

    def test_nested_context_managers(self):
        """Test nested context managers restore previous context."""
        outer_headers = {MCP_SESSION_ID_HEADER: "outer-session"}
        inner_headers = {MCP_SESSION_ID_HEADER: "inner-session"}

        with mcp_context(headers=outer_headers):
            assert get_mcp_context().session_id == "outer-session"

            with mcp_context(headers=inner_headers):
                assert get_mcp_context().session_id == "inner-session"

            # Should restore outer context
            assert get_mcp_context().session_id == "outer-session"

    def test_context_manager_with_jwt(self):
        """Test context manager extracts user from JWT."""
        token = create_jwt_token({"sub": "jwt-user"})
        headers = {
            MCP_SESSION_ID_HEADER: "jwt-session",
            AUTHORIZATION_HEADER: f"Bearer {token}",
        }

        with mcp_context(headers=headers) as ctx:
            assert ctx.session_id == "jwt-session"
            assert ctx.user_id == "jwt-user"


class TestMCPContextDecorator:
    """Tests for mcp_context.from_headers decorator."""

    def test_sync_function_decorator(self):
        """Test decorator with sync function."""
        captured_context = []

        @mcp_context.from_headers(lambda: {MCP_SESSION_ID_HEADER: "decorated-session"})
        def my_handler():
            ctx = get_mcp_context()
            captured_context.append(ctx)
            return "result"

        result = my_handler()
        assert result == "result"
        assert len(captured_context) == 1
        assert captured_context[0].session_id == "decorated-session"

    def test_async_function_decorator(self):
        """Test decorator with async function."""
        captured_context = []

        @mcp_context.from_headers(lambda: {MCP_SESSION_ID_HEADER: "async-session"})
        async def my_async_handler():
            ctx = get_mcp_context()
            captured_context.append(ctx)
            return "async-result"

        result = asyncio.run(my_async_handler())
        assert result == "async-result"
        assert len(captured_context) == 1
        assert captured_context[0].session_id == "async-session"

    def test_decorator_with_dynamic_headers(self):
        """Test decorator with dynamically changing headers."""
        current_headers = {}

        @mcp_context.from_headers(lambda: current_headers)
        def handler():
            ctx = get_mcp_context()
            return ctx.session_id if ctx else None

        current_headers[MCP_SESSION_ID_HEADER] = "first-session"
        assert handler() == "first-session"

        current_headers[MCP_SESSION_ID_HEADER] = "second-session"
        assert handler() == "second-session"

