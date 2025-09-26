"""
Tests for configuration validation improvements - QA fixes
Ensures negative values and invalid settings are rejected
"""


import pytest
from pydantic import ValidationError

from config.settings import Environment, Settings


class TestConfigurationValidation:
    """Test configuration validation catches invalid values"""

    def test_reject_negative_token_expire(self):
        """Test that negative token expiry is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.DEVELOPMENT,
                access_token_expire_minutes=-10
            )
        assert "must be greater than 0" in str(exc_info.value)

    def test_reject_negative_database_pool_size(self):
        """Test that negative database pool size is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.DEVELOPMENT,
                database_pool_size=-5
            )
        assert "must be greater than 0" in str(exc_info.value)

    def test_reject_negative_cache_ttl(self):
        """Test that negative cache TTL is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.DEVELOPMENT,
                cache_ttl_seconds=-300
            )
        assert "must be greater than 0" in str(exc_info.value)

    def test_reject_negative_analytics_retention(self):
        """Test that negative analytics retention is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.DEVELOPMENT,
                analytics_retention_days=-90
            )
        assert "must be greater than 0" in str(exc_info.value)

    def test_reject_invalid_search_limits(self):
        """Test that invalid search limits are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.DEVELOPMENT,
                search_default_limit=0
            )
        assert "must be greater than 0" in str(exc_info.value)

    def test_production_jwt_secret_validation(self):
        """Test production JWT secret requirements"""
        # Production without JWT secret should fail in validation
        with pytest.raises(ValidationError) as exc_info:
            settings = Settings(
                environment=Environment.PRODUCTION,
                jwt_secret_key=""
            )
            settings.model_post_init(None)  # Trigger production validation

        # Short JWT secret should fail
        with pytest.raises(ValueError) as exc_info:
            settings = Settings(
                environment=Environment.PRODUCTION,
                jwt_secret_key="too-short"
            )
            settings._validate_production_config()
        assert "at least 64 characters" in str(exc_info.value)

    def test_banned_jwt_secrets_rejected(self):
        """Test that common default JWT secrets are rejected"""
        banned_secrets = ["secret", "dev", "test", "changeme", "default"]

        for banned in banned_secrets:
            with pytest.raises(ValidationError) as exc_info:
                Settings(
                    environment=Environment.PRODUCTION,
                    jwt_secret_key=banned
                )
            assert "banned default value" in str(exc_info.value)

    def test_development_auto_generates_jwt_secret(self):
        """Test that development auto-generates JWT secret"""
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            jwt_secret_key=""  # Empty
        )
        settings.model_post_init(None)

        # Should auto-generate a secure secret
        assert settings.jwt_secret_key is not None
        assert len(settings.jwt_secret_key) >= 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
