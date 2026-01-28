"""Tests for HeimdallConfig."""

import os
import pytest
from unittest.mock import patch

from hmdl.config import HeimdallConfig


class TestHeimdallConfig:
    """Tests for HeimdallConfig class."""

    def test_default_values(self):
        """Test that config uses environment variables by default."""
        config = HeimdallConfig()
        
        assert config.api_key == "test-api-key"
        assert config.endpoint == "https://test.heimdall.dev"
        assert config.service_name == "test-service"
        assert config.environment == "test"

    def test_explicit_values_override_env(self):
        """Test that explicit values override environment variables."""
        config = HeimdallConfig(
            api_key="explicit-key",
            endpoint="https://explicit.heimdall.dev",
            service_name="explicit-service",
            environment="production",
        )
        
        assert config.api_key == "explicit-key"
        assert config.endpoint == "https://explicit.heimdall.dev"
        assert config.service_name == "explicit-service"
        assert config.environment == "production"

    def test_from_env_classmethod(self):
        """Test the from_env class method."""
        config = HeimdallConfig.from_env()
        
        assert config.api_key == "test-api-key"
        assert config.endpoint == "https://test.heimdall.dev"

    def test_validate_missing_api_key(self):
        """Test validation passes when API key is missing (optional for local dev)."""
        config = HeimdallConfig(api_key=None, enabled=True)

        # API key is now optional for local development
        config.validate()  # Should not raise

    def test_validate_invalid_batch_size(self):
        """Test validation fails for invalid batch size."""
        config = HeimdallConfig(api_key="key", batch_size=0)
        
        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            config.validate()

    def test_validate_invalid_flush_interval(self):
        """Test validation fails for invalid flush interval."""
        config = HeimdallConfig(api_key="key", flush_interval_ms=50)
        
        with pytest.raises(ValueError, match="flush_interval_ms must be at least 100"):
            config.validate()

    def test_validate_invalid_queue_size(self):
        """Test validation fails when queue size is less than batch size."""
        config = HeimdallConfig(api_key="key", batch_size=100, max_queue_size=50)
        
        with pytest.raises(ValueError, match="max_queue_size must be at least batch_size"):
            config.validate()

    def test_validate_success(self):
        """Test validation passes with valid config."""
        config = HeimdallConfig(
            api_key="valid-key",
            batch_size=100,
            flush_interval_ms=5000,
            max_queue_size=1000,
        )
        
        # Should not raise
        config.validate()

    def test_disabled_config_skips_api_key_validation(self):
        """Test that disabled config doesn't require API key."""
        config = HeimdallConfig(api_key=None, enabled=False)
        
        # Should not raise even without API key
        config.validate()

    def test_metadata_default(self):
        """Test that metadata defaults to empty dict."""
        config = HeimdallConfig()
        
        assert config.metadata == {}

    def test_metadata_custom(self):
        """Test custom metadata."""
        config = HeimdallConfig(metadata={"custom": "value"})
        
        assert config.metadata == {"custom": "value"}

