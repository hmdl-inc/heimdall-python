"""Tests for HeimdallClient."""

import os
import pytest
from unittest.mock import MagicMock, patch

from hmdl.client import HeimdallClient
from hmdl.config import HeimdallConfig


class TestHeimdallClient:
    """Tests for HeimdallClient class."""

    def test_singleton_pattern(self):
        """Test that HeimdallClient is a singleton."""
        client1 = HeimdallClient()
        client2 = HeimdallClient()
        
        assert client1 is client2

    def test_disabled_client_no_tracer(self):
        """Test that disabled client has no tracer setup."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()
            
            assert client._tracer is None
            assert client._provider is None

    def test_get_instance(self):
        """Test get_instance class method."""
        assert HeimdallClient.get_instance() is None
        
        client = HeimdallClient()
        
        assert HeimdallClient.get_instance() is client

    def test_reset(self):
        """Test reset class method."""
        client = HeimdallClient()
        assert HeimdallClient.get_instance() is not None
        
        HeimdallClient.reset()
        
        assert HeimdallClient.get_instance() is None

    def test_tracer_property_returns_noop_when_disabled(self):
        """Test tracer property returns no-op tracer when disabled."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()
            tracer = client.tracer
            
            # Should return a tracer (no-op)
            assert tracer is not None

    def test_config_from_arguments(self):
        """Test client accepts config arguments."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient(
                api_key="arg-key",
                service_name="arg-service",
            )
            
            assert client.config.api_key == "arg-key"
            assert client.config.service_name == "arg-service"

    def test_config_object(self):
        """Test client accepts config object."""
        config = HeimdallConfig(
            api_key="config-key",
            service_name="config-service",
            enabled=False,
        )
        
        client = HeimdallClient(config=config)
        
        assert client.config.api_key == "config-key"
        assert client.config.service_name == "config-service"

    def test_flush_when_disabled(self):
        """Test flush does nothing when disabled."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()
            
            # Should not raise
            client.flush()

    def test_shutdown_when_disabled(self):
        """Test shutdown does nothing when disabled."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()
            
            # Should not raise
            client.shutdown()

    def test_get_current_span(self):
        """Test get_current_span returns current span."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()

            # Should return a span (possibly invalid/no-op)
            span = client.get_current_span()
            assert span is not None


class TestSessionAndUserIdManagement:
    """Tests for session and user ID management."""

    def test_get_and_set_session_id(self):
        """Test get_session_id and set_session_id methods."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()

            # Initially undefined
            assert client.get_session_id() is None

            # Set session ID
            client.set_session_id("session-123")
            assert client.get_session_id() == "session-123"

            # Clear session ID
            client.set_session_id(None)
            assert client.get_session_id() is None

    def test_get_and_set_user_id(self):
        """Test get_user_id and set_user_id methods."""
        with patch.dict(os.environ, {"HEIMDALL_ENABLED": "false"}):
            client = HeimdallClient()

            # Initially undefined
            assert client.get_user_id() is None

            # Set user ID
            client.set_user_id("user-456")
            assert client.get_user_id() == "user-456"

            # Clear user ID
            client.set_user_id(None)
            assert client.get_user_id() is None

    def test_session_id_from_environment_variable(self):
        """Test session ID initialization from environment variable."""
        with patch.dict(os.environ, {
            "HEIMDALL_ENABLED": "false",
            "HEIMDALL_SESSION_ID": "env-session-id"
        }):
            HeimdallClient.reset()
            client = HeimdallClient()

            assert client.get_session_id() == "env-session-id"

    def test_user_id_from_environment_variable(self):
        """Test user ID initialization from environment variable."""
        with patch.dict(os.environ, {
            "HEIMDALL_ENABLED": "false",
            "HEIMDALL_USER_ID": "env-user-id"
        }):
            HeimdallClient.reset()
            client = HeimdallClient()

            assert client.get_user_id() == "env-user-id"
