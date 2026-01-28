"""Tests for decorators."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from hmdl.decorators import (
    trace_mcp_tool,
    trace_mcp_resource,
    trace_mcp_prompt,
    observe,
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


class TestTraceMCPResource:
    """Tests for trace_mcp_resource decorator."""

    def test_sync_function(self):
        """Test sync resource function."""
        @trace_mcp_resource()
        def read_resource(uri: str) -> str:
            return f"content of {uri}"
        
        result = read_resource("file://test.txt")
        assert result == "content of file://test.txt"


class TestTraceMCPPrompt:
    """Tests for trace_mcp_prompt decorator."""

    def test_sync_function(self):
        """Test sync prompt function."""
        @trace_mcp_prompt()
        def generate_prompt(context: str) -> list:
            return [{"role": "user", "content": context}]
        
        result = generate_prompt("hello")
        assert result == [{"role": "user", "content": "hello"}]


class TestObserve:
    """Tests for observe decorator."""

    def test_without_parentheses(self):
        """Test @observe without parentheses."""
        @observe
        def my_func(x: int) -> int:
            return x * 2
        
        result = my_func(5)
        assert result == 10

    def test_with_parentheses(self):
        """Test @observe() with parentheses."""
        @observe()
        def my_func(x: int) -> int:
            return x * 2
        
        result = my_func(5)
        assert result == 10

    def test_with_custom_name(self):
        """Test @observe with custom name."""
        @observe(name="custom-operation")
        def my_func():
            return "result"
        
        result = my_func()
        assert result == "result"

    def test_async_function(self):
        """Test @observe with async function."""
        @observe
        async def async_func(x: int) -> int:
            return x * 2
        
        import asyncio
        result = asyncio.run(async_func(5))
        assert result == 10

    def test_preserves_function_name(self):
        """Test decorator preserves function name."""
        @observe
        def my_func():
            pass
        
        assert my_func.__name__ == "my_func"

