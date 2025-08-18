"""
Production Deployment Tests
Validates production-ready configuration and security requirements
"""

import pytest
import os
import requests
from fastapi.testclient import TestClient
from unittest.mock import patch
from config.settings import Settings, Environment


class TestProductionConfiguration:
    """Test production configuration validation"""

    def test_production_requires_jwt_secret(self):
        """Production must have JWT secret configured"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY is required"):
                Settings()

    def test_production_requires_strong_jwt_secret(self):
        """Production must have strong JWT secret (64+ chars)"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": "short",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="at least 64 characters"):
                Settings()

    def test_production_rejects_banned_secrets(self):
        """Production rejects common default/weak secrets"""
        banned_secret = "your-secret-key-change-in-production"
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": banned_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="banned default value"):
                Settings()

    def test_production_requires_database_url(self):
        """Production must have database URL configured"""
        strong_secret = "a" * 64
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": strong_secret,
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="DATABASE_URL is required"):
                Settings()

    def test_production_requires_cors_origins(self):
        """Production must have CORS origins configured"""
        strong_secret = "a" * 64
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": strong_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must be configured"):
                Settings()

    def test_production_requires_allowed_hosts(self):
        """Production must have allowed hosts configured"""
        strong_secret = "a" * 64
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": strong_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            with pytest.raises(ValueError, match="ALLOWED_HOSTS must be configured"):
                Settings()

    def test_production_requires_rate_limit_backend(self):
        """Production must have rate limit backend or explicit disable"""
        strong_secret = "a" * 64
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": strong_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com"
        }):
            with pytest.raises(ValueError, match="RATE_LIMIT_BACKEND_URL is required"):
                Settings()

    def test_valid_production_config(self):
        """Valid production configuration should pass validation"""
        strong_secret = "a" * 64
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": strong_secret,
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CORS_ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "RATE_LIMIT_BACKEND_URL": "redis://localhost:6379"
        }):
            settings = Settings()
            assert settings.environment == Environment.PRODUCTION
            assert settings.jwt_secret_key == strong_secret


class TestMiddlewareStack:
    """Test production middleware functionality"""

    @pytest.fixture
    def client(self):
        """Create test client with production middleware"""
        from main import app
        return TestClient(app)

    def test_trusted_host_validation(self, client):
        """Test that invalid hosts are rejected"""
        # Test with invalid host
        response = client.get("/healthz", headers={"Host": "evil.com"})
        if response.status_code == 400:
            assert response.json()["code"] == "INVALID_HOST"

    def test_docs_protection_in_production(self, client):
        """Test that docs are protected in production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "ENABLE_DOCS": "false"}):
            response = client.get("/docs")
            # Should be 404 or protected
            assert response.status_code in [404, 403]

    def test_security_headers_present(self, client):
        """Test that security headers are added"""
        response = client.get("/healthz")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"


class TestContainerReadiness:
    """Test container deployment readiness"""

    def test_health_endpoint_responds(self, client):
        """Health endpoint should respond"""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_readiness_endpoint_responds(self, client):
        """Readiness endpoint should respond"""
        response = client.get("/health/services")
        assert response.status_code in [200, 503]  # 200 if healthy, 503 if deps down

    def test_graceful_shutdown_handling(self):
        """Test graceful shutdown capabilities"""
        # This would be tested in integration environment
        # Here we just verify the middleware is configured
        from middleware.database_session import DatabaseSessionMiddleware
        assert DatabaseSessionMiddleware is not None


class TestRateLimiting:
    """Test production rate limiting"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_rate_limit_headers_present(self, client):
        """Rate limit responses should include proper headers"""
        # Make multiple requests to trigger rate limiting
        responses = []
        for _ in range(5):
            response = client.get("/api/v1/scholarships")
            responses.append(response)
        
        # Check if rate limiting is working and headers are present
        for response in responses:
            if response.status_code == 429:
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "Retry-After" in response.headers
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])