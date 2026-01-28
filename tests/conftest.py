"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import MagicMock, patch

# Set test environment variables before importing SDK
os.environ["HEIMDALL_API_KEY"] = "test-api-key"
os.environ["HEIMDALL_ENDPOINT"] = "https://test.heimdall.dev"
os.environ["HEIMDALL_SERVICE_NAME"] = "test-service"
os.environ["HEIMDALL_ENVIRONMENT"] = "test"
os.environ["HEIMDALL_ENABLED"] = "false"  # Disable actual tracing in tests


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the HeimdallClient singleton before each test."""
    from hmdl.client import HeimdallClient
    HeimdallClient.reset()
    yield
    HeimdallClient.reset()


@pytest.fixture
def mock_tracer():
    """Create a mock tracer for testing."""
    mock = MagicMock()
    mock_span = MagicMock()
    mock_span.__enter__ = MagicMock(return_value=mock_span)
    mock_span.__exit__ = MagicMock(return_value=False)
    mock.start_as_current_span.return_value = mock_span
    return mock, mock_span


@pytest.fixture
def enabled_client(mock_tracer):
    """Create a client with tracing enabled but mocked."""
    from hmdl.client import HeimdallClient
    
    mock, mock_span = mock_tracer
    
    with patch.dict(os.environ, {"HEIMDALL_ENABLED": "true"}):
        with patch("hmdl.client.OTLPSpanExporter"):
            with patch("hmdl.client.BatchSpanProcessor"):
                with patch("hmdl.client.TracerProvider"):
                    with patch("hmdl.client.trace") as mock_trace:
                        mock_trace.get_tracer.return_value = mock
                        client = HeimdallClient()
                        client._tracer = mock
                        yield client, mock, mock_span

