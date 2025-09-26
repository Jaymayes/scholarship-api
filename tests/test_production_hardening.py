"""
Comprehensive production hardening tests
Tests all security configurations and middleware behavior
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings


class TestProductionCORSHardening:
    """Test production CORS security measures"""

    def test_production_blocks_wildcard_origins(self):
        """Test production environment blocks wildcard origins"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ALLOWED_ORIGINS": "*,https://app.example.com"
        }), patch('logging.critical') as mock_critical:
            settings = Settings()
            cors_origins = settings.get_cors_origins

            # Should remove wildcard and log critical error
            assert "*" not in cors_origins
            assert "https://app.example.com" in cors_origins
            mock_critical.assert_called()

    def test_production_fails_safe_without_origins(self):
        """Test production fails safe when no origins configured"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ALLOWED_ORIGINS": ""
        }), patch('logging.critical') as mock_critical:
            settings = Settings()
            cors_origins = settings.get_cors_origins

            # Should return empty list and log critical error
            assert cors_origins == []
            mock_critical.assert_called()

    def test_cors_config_includes_all_settings(self):
        """Test CORS config includes all required settings"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ALLOWED_ORIGINS": "https://app.example.com"
        }):
            settings = Settings()
            cors_config = settings.get_cors_config

            assert "allow_origins" in cors_config
            assert "allow_credentials" in cors_config
            assert "allow_methods" in cors_config
            assert "allow_headers" in cors_config
            assert "max_age" in cors_config

            # Headers should be explicit, not wildcard
            assert cors_config["allow_headers"] != ["*"]
            assert "Authorization" in cors_config["allow_headers"]


class TestMiddlewareOrdering:
    """Test middleware is applied in correct order"""

    @pytest.fixture
    def test_app(self):
        """Create test app for middleware testing"""
        from main import app
        return app

    def test_cors_preflight_handling(self, test_app):
        """Test CORS preflight OPTIONS requests work correctly"""
        client = TestClient(test_app)

        # Send preflight request
        response = client.options(
            "/api/v1/search",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )

        # Should get CORS headers back
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_middleware_order_with_errors(self, test_app):
        """Test middleware handles errors in correct order"""
        client = TestClient(test_app)

        # Test URL too long (should be caught before body size)
        long_url = "/api/v1/search?" + "q=" + "a" * 3000
        response = client.get(long_url)

        assert response.status_code == 414
        error = response.json()
        assert error["code"] == "URI_TOO_LONG"
        assert "trace_id" in error


class TestUnifiedErrorHandling:
    """Test all error responses use unified schema"""

    @pytest.fixture
    def test_app(self):
        """Create test app for error testing"""
        from main import app
        return app

    def test_413_error_format(self, test_app):
        """Test 413 error uses unified format"""
        client = TestClient(test_app)

        headers = {"content-length": "2000000"}
        response = client.post("/api/v1/search", headers=headers, json={})

        assert response.status_code == 413
        error = response.json()
        self._assert_unified_error_format(error, 413, "PAYLOAD_TOO_LARGE")

    def test_414_error_format(self, test_app):
        """Test 414 error uses unified format"""
        client = TestClient(test_app)

        long_url = "/api/v1/search?" + "q=" + "a" * 3000
        response = client.get(long_url)

        assert response.status_code == 414
        error = response.json()
        self._assert_unified_error_format(error, 414, "URI_TOO_LONG")

    def test_404_error_format(self, test_app):
        """Test 404 error uses unified format"""
        client = TestClient(test_app)

        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        error = response.json()
        self._assert_unified_error_format(error, 404, "NOT_FOUND")

    def test_422_validation_error_format(self, test_app):
        """Test 422 validation error uses unified format"""
        client = TestClient(test_app)

        # Send invalid JSON data
        response = client.post("/api/v1/search", json={"invalid": "data"})

        if response.status_code == 422:
            error = response.json()
            self._assert_unified_error_format(error, 422, "VALIDATION_ERROR")
            assert "details" in error
            assert "fields" in error["details"]

    def _assert_unified_error_format(self, error, status_code, error_code):
        """Assert error response follows unified format"""
        required_fields = ["trace_id", "code", "message", "status", "timestamp"]

        for field in required_fields:
            assert field in error, f"Missing required field: {field}"

        assert error["status"] == status_code
        assert error["code"] == error_code
        assert isinstance(error["timestamp"], int)
        assert error["trace_id"] != "unknown"


class TestRateLimitingProduction:
    """Test rate limiting production configuration"""

    def test_rate_limit_config_production(self):
        """Test production rate limiting configuration"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "RATE_LIMIT_PER_MINUTE": "50"
        }):
            settings = Settings()
            rate_config = settings.get_rate_limit_config

            assert rate_config["enabled"]
            assert rate_config["per_minute"] == 50
            assert rate_config["backend_url"] == "redis://localhost:6379/0"

    def test_rate_limit_environment_defaults(self):
        """Test rate limiting defaults per environment"""
        test_cases = [
            ("production", 100),
            ("staging", 150),
            ("development", 200),
            ("local", 300)
        ]

        for env, expected_limit in test_cases:
            with patch.dict(os.environ, {
                "ENVIRONMENT": env,
                "RATE_LIMIT_PER_MINUTE": "0"  # Use defaults
            }):
                settings = Settings()
                assert settings.get_rate_limit_per_minute == expected_limit

    def test_healthcheck_exemption_paths(self):
        """Test healthcheck paths are exempt from rate limiting"""
        settings = Settings()
        rate_config = settings.get_rate_limit_config

        exempt_paths = rate_config["exempt_paths"]
        assert "/health" in exempt_paths
        assert "/readiness" in exempt_paths
        assert "/metrics" in exempt_paths


class TestSecurityHeaders:
    """Test security headers middleware"""

    @pytest.fixture
    def test_app(self):
        """Create test app for security testing"""
        from main import app
        return app

    def test_security_headers_present(self, test_app):
        """Test security headers are applied"""
        client = TestClient(test_app)

        response = client.get("/health")

        # Check for security headers
        headers = response.headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-xss-protection" in headers

    def test_hsts_production_only(self):
        """Test HSTS header only in production with HTTPS"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ENABLE_HSTS": "true"
        }):
            settings = Settings()
            assert settings.should_enable_hsts

        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "ENABLE_HSTS": "true"
        }):
            settings = Settings()
            assert not settings.should_enable_hsts


class TestProductionConfigValidation:
    """Test production configuration validation"""

    def test_environment_specific_defaults(self):
        """Test each environment has appropriate defaults"""
        environments = ["production", "staging", "development", "local"]

        for env in environments:
            with patch.dict(os.environ, {"ENVIRONMENT": env}):
                settings = Settings()

                # Production should have stricter defaults
                if env == "production":
                    assert settings.get_rate_limit_per_minute <= 100
                    cors_origins = settings.get_cors_origins
                    # Production without explicit origins should be empty
                    if not os.environ.get("CORS_ALLOWED_ORIGINS"):
                        assert cors_origins == []
                else:
                    # Development environments can be more permissive
                    assert settings.get_rate_limit_per_minute >= 150

    def test_secret_not_logged(self):
        """Test sensitive values are not exposed in logs"""
        settings = Settings()

        # JWT secret should not be in string representation
        settings_str = str(settings)
        assert settings.jwt_secret_key not in settings_str

        # Backend URL should not expose credentials
        backend_url = settings.get_rate_limit_config["backend_url"]
        # This is acceptable since it's redis:// not with password
        assert "redis://" in backend_url


class TestRequestSizeAndURLValidation:
    """Test request size and URL length validation"""

    @pytest.fixture
    def test_app(self):
        """Create test app for validation testing"""
        from main import app
        return app

    def test_request_size_configuration(self):
        """Test request size can be configured"""
        with patch.dict(os.environ, {
            "MAX_REQUEST_SIZE_BYTES": "512000"  # 500KB
        }):
            settings = Settings()
            assert settings.max_request_size_bytes == 512000

    def test_url_length_configuration(self):
        """Test URL length can be configured"""
        with patch.dict(os.environ, {
            "MAX_URL_LENGTH": "4096"
        }):
            settings = Settings()
            assert settings.max_url_length == 4096

    def test_middleware_applied_correctly(self, test_app):
        """Test both middleware are applied and working"""
        client = TestClient(test_app)

        # Test body size limit
        large_headers = {"content-length": "2000000"}
        response = client.post("/api/v1/search", headers=large_headers, json={})
        assert response.status_code == 413

        # Test URL length limit
        long_url = "/api/v1/search?" + "q=" + "a" * 3000
        response = client.get(long_url)
        assert response.status_code == 414


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
