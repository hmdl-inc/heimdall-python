"""Decorators for instrumenting MCP functions with Heimdall observability."""

from __future__ import annotations

import functools
import inspect
import json
import time
from typing import Any, Callable, Optional, TypeVar, Union, overload

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from hmdl.types import HeimdallAttributes, SpanKind, SpanStatus

F = TypeVar("F", bound=Callable[..., Any])


def _serialize_value(value: Any) -> str:
    """Safely serialize a value to string for span attributes."""
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _get_client() -> Any:
    """Get the Heimdall client instance."""
    from hmdl.client import HeimdallClient
    return HeimdallClient.get_instance()


def _create_span_decorator(
    span_kind: SpanKind,
    name_attr: str,
    args_attr: str,
    result_attr: str,
) -> Callable[[Optional[str]], Callable[[F], F]]:
    """Factory for creating MCP-specific decorators."""
    
    def decorator(name: Optional[str] = None) -> Callable[[F], F]:
        def wrapper(func: F) -> F:
            span_name = name or func.__name__
            is_async = inspect.iscoroutinefunction(func)
            
            if is_async:
                @functools.wraps(func)
                async def async_wrapped(*args: Any, **kwargs: Any) -> Any:
                    client = _get_client()
                    if client is None:
                        return await func(*args, **kwargs)
                    
                    tracer = client.tracer
                    with tracer.start_as_current_span(
                        name=span_name,
                        kind=trace.SpanKind.SERVER,
                    ) as span:
                        start_time = time.perf_counter()
                        
                        # Set input attributes
                        span.set_attribute(name_attr, span_name)
                        span.set_attribute("heimdall.span_kind", span_kind.value)
                        
                        # Capture arguments
                        try:
                            all_args = _capture_arguments(func, args, kwargs)
                            span.set_attribute(args_attr, _serialize_value(all_args))
                        except Exception:
                            pass
                        
                        try:
                            result = await func(*args, **kwargs)
                            
                            # Set output attributes
                            span.set_attribute(result_attr, _serialize_value(result))
                            span.set_attribute(HeimdallAttributes.STATUS, SpanStatus.OK.value)
                            span.set_status(Status(StatusCode.OK))
                            
                            return result
                        except Exception as e:
                            _record_error(span, e)
                            raise
                        finally:
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            span.set_attribute(HeimdallAttributes.DURATION_MS, duration_ms)
                
                return async_wrapped  # type: ignore
            else:
                @functools.wraps(func)
                def sync_wrapped(*args: Any, **kwargs: Any) -> Any:
                    client = _get_client()
                    if client is None:
                        return func(*args, **kwargs)
                    
                    tracer = client.tracer
                    with tracer.start_as_current_span(
                        name=span_name,
                        kind=trace.SpanKind.SERVER,
                    ) as span:
                        start_time = time.perf_counter()
                        
                        # Set input attributes
                        span.set_attribute(name_attr, span_name)
                        span.set_attribute("heimdall.span_kind", span_kind.value)
                        
                        # Capture arguments
                        try:
                            all_args = _capture_arguments(func, args, kwargs)
                            span.set_attribute(args_attr, _serialize_value(all_args))
                        except Exception:
                            pass
                        
                        try:
                            result = func(*args, **kwargs)
                            
                            # Set output attributes
                            span.set_attribute(result_attr, _serialize_value(result))
                            span.set_attribute(HeimdallAttributes.STATUS, SpanStatus.OK.value)
                            span.set_status(Status(StatusCode.OK))
                            
                            return result
                        except Exception as e:
                            _record_error(span, e)
                            raise
                        finally:
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            span.set_attribute(HeimdallAttributes.DURATION_MS, duration_ms)
                
                return sync_wrapped  # type: ignore
        
        return wrapper
    
    return decorator


def _capture_arguments(func: Callable[..., Any], args: tuple, kwargs: dict) -> dict:
    """Capture function arguments as a dictionary."""
    sig = inspect.signature(func)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _record_error(span: trace.Span, error: Exception) -> None:
    """Record an error on a span."""
    span.set_attribute(HeimdallAttributes.STATUS, SpanStatus.ERROR.value)
    span.set_attribute(HeimdallAttributes.ERROR_MESSAGE, str(error))
    span.set_attribute(HeimdallAttributes.ERROR_TYPE, type(error).__name__)
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)


# Create MCP-specific decorators
trace_mcp_tool = _create_span_decorator(
    span_kind=SpanKind.MCP_TOOL,
    name_attr=HeimdallAttributes.MCP_TOOL_NAME,
    args_attr=HeimdallAttributes.MCP_TOOL_ARGUMENTS,
    result_attr=HeimdallAttributes.MCP_TOOL_RESULT,
)
trace_mcp_tool.__doc__ = """
Decorator to trace MCP tool calls.

Example:
    >>> @trace_mcp_tool()
    ... def my_tool(arg1: str, arg2: int) -> str:
    ...     return f"Result: {arg1}, {arg2}"

    >>> @trace_mcp_tool("custom-tool-name")
    ... async def async_tool(data: dict) -> dict:
    ...     return {"processed": data}
"""

trace_mcp_resource = _create_span_decorator(
    span_kind=SpanKind.MCP_RESOURCE,
    name_attr=HeimdallAttributes.MCP_RESOURCE_URI,
    args_attr="mcp.resource.arguments",
    result_attr="mcp.resource.result",
)
trace_mcp_resource.__doc__ = """
Decorator to trace MCP resource access.

Example:
    >>> @trace_mcp_resource()
    ... def read_file(uri: str) -> str:
    ...     return open(uri).read()
"""

trace_mcp_prompt = _create_span_decorator(
    span_kind=SpanKind.MCP_PROMPT,
    name_attr=HeimdallAttributes.MCP_PROMPT_NAME,
    args_attr=HeimdallAttributes.MCP_PROMPT_ARGUMENTS,
    result_attr=HeimdallAttributes.MCP_PROMPT_MESSAGES,
)
trace_mcp_prompt.__doc__ = """
Decorator to trace MCP prompt calls.

Example:
    >>> @trace_mcp_prompt()
    ... def generate_prompt(context: str) -> list:
    ...     return [{"role": "user", "content": context}]
"""


@overload
def observe(func: F) -> F: ...

@overload
def observe(
    name: Optional[str] = None,
    *,
    capture_input: bool = True,
    capture_output: bool = True,
) -> Callable[[F], F]: ...

def observe(
    func: Optional[F] = None,
    name: Optional[str] = None,
    *,
    capture_input: bool = True,
    capture_output: bool = True,
) -> Union[F, Callable[[F], F]]:
    """
    General-purpose decorator to observe any function.

    Can be used with or without arguments:

    Example:
        >>> @observe
        ... def my_function():
        ...     pass

        >>> @observe(name="custom-name", capture_output=False)
        ... def another_function():
        ...     pass
    """
    def decorator(fn: F) -> F:
        span_name = name or fn.__name__
        is_async = inspect.iscoroutinefunction(fn)

        if is_async:
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                client = _get_client()
                if client is None:
                    return await fn(*args, **kwargs)

                tracer = client.tracer
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=trace.SpanKind.INTERNAL,
                ) as span:
                    start_time = time.perf_counter()
                    span.set_attribute("heimdall.span_kind", SpanKind.INTERNAL.value)

                    if capture_input:
                        try:
                            all_args = _capture_arguments(fn, args, kwargs)
                            span.set_attribute("heimdall.input", _serialize_value(all_args))
                        except Exception:
                            pass

                    try:
                        result = await fn(*args, **kwargs)
                        if capture_output:
                            span.set_attribute("heimdall.output", _serialize_value(result))
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        _record_error(span, e)
                        raise
                    finally:
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        span.set_attribute(HeimdallAttributes.DURATION_MS, duration_ms)

            return async_wrapper  # type: ignore
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                client = _get_client()
                if client is None:
                    return fn(*args, **kwargs)

                tracer = client.tracer
                with tracer.start_as_current_span(
                    name=span_name,
                    kind=trace.SpanKind.INTERNAL,
                ) as span:
                    start_time = time.perf_counter()
                    span.set_attribute("heimdall.span_kind", SpanKind.INTERNAL.value)

                    if capture_input:
                        try:
                            all_args = _capture_arguments(fn, args, kwargs)
                            span.set_attribute("heimdall.input", _serialize_value(all_args))
                        except Exception:
                            pass

                    try:
                        result = fn(*args, **kwargs)
                        if capture_output:
                            span.set_attribute("heimdall.output", _serialize_value(result))
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        _record_error(span, e)
                        raise
                    finally:
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        span.set_attribute(HeimdallAttributes.DURATION_MS, duration_ms)

            return sync_wrapper  # type: ignore

    # Handle both @observe and @observe() syntax
    if func is not None:
        return decorator(func)
    return decorator

