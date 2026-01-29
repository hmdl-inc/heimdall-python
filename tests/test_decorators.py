"""Tests for decorators."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from hmdl.decorators import (
    trace_mcp_tool,
    _serialize_value,
    _capture_arguments,
)


class TestSerializeValue:
    """Tests for _serialize_value helper."""

    def test_serialize_dict(self):
        """Test serializing a dictionary."""
        result = _serialize_value({"key": "value"})
        assert result == '{"key": "value"}'

    def test_serialize_list(self):
        """Test serializing a list."""
        result = _serialize_value([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_serialize_string(self):
        """Test serializing a string."""
        result = _serialize_value("hello")
        assert result == '"hello"'

    def test_serialize_non_serializable(self):
        """Test serializing non-JSON-serializable object."""
        class Custom:
            def __str__(self):
                return "custom-object"

        result = _serialize_value(Custom())
        assert "custom-object" in result


class TestCaptureArguments:
    """Tests for _capture_arguments helper."""

    def test_capture_positional_args(self):
        """Test capturing positional arguments."""
        def func(a, b, c):
            pass

        result = _capture_arguments(func, (1, 2, 3), {})
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_capture_keyword_args(self):
        """Test capturing keyword arguments."""
        def func(a, b, c):
            pass

        result = _capture_arguments(func, (), {"a": 1, "b": 2, "c": 3})
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_capture_mixed_args(self):
        """Test capturing mixed positional and keyword arguments."""
        def func(a, b, c=10):
            pass

        result = _capture_arguments(func, (1,), {"b": 2})
        assert result == {"a": 1, "b": 2, "c": 10}


class TestTraceMCPTool:
    """Tests for trace_mcp_tool decorator."""

    def test_sync_function_without_client(self):
        """Test sync function works without client initialized."""
        @trace_mcp_tool()
        def my_tool(query: str) -> str:
            return f"result: {query}"

        result = my_tool("test")
        assert result == "result: test"

    def test_async_function_without_client(self):
        """Test async function works without client initialized."""
        @trace_mcp_tool()
        async def my_tool(query: str) -> str:
            return f"result: {query}"

        import asyncio
        result = asyncio.run(my_tool("test"))
        assert result == "result: test"

    def test_custom_name(self):
        """Test decorator with custom name."""
        @trace_mcp_tool("custom-tool-name")
        def my_tool():
            return "result"

        result = my_tool()
        assert result == "result"

    def test_preserves_function_name(self):
        """Test decorator preserves function name."""
        @trace_mcp_tool()
        def my_tool():
            pass

        assert my_tool.__name__ == "my_tool"

    def test_exception_propagation(self):
        """Test exceptions are propagated."""
        @trace_mcp_tool()
        def failing_tool():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_tool()

    def test_with_multiple_args(self):
        """Test decorator with multiple arguments."""
        @trace_mcp_tool()
        def search_tool(query: str, limit: int = 10) -> dict:
            return {"query": query, "limit": limit}

        result = search_tool("test", limit=5)
        assert result == {"query": "test", "limit": 5}

    def test_with_dict_return(self):
        """Test decorator with dictionary return value."""
        @trace_mcp_tool("calculator")
        def calculator(a: int, b: int) -> dict:
            return {"sum": a + b, "product": a * b}

        result = calculator(3, 4)
        assert result == {"sum": 7, "product": 12}

    def test_async_with_exception(self):
        """Test async function with exception."""
        @trace_mcp_tool()
        async def failing_async_tool():
            raise RuntimeError("async error")

        import asyncio
        with pytest.raises(RuntimeError, match="async error"):
            asyncio.run(failing_async_tool())

