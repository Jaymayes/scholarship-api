#!/usr/bin/env python3
"""
Comprehensive test for all QA fixes implementation
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set test environment before imports
os.environ.update({
    'ENVIRONMENT': 'development',
    'RATE_LIMIT_ENABLED': 'false',
    'DEBUG': 'true',
    'JWT_SECRET_KEY': 'test-secret-key-at-least-32-chars-long-for-testing-purposes-only',
    'ALLOWED_HOSTS': '[]',
    'TRUSTED_PROXY_IPS': '[]',
    'CORS_ALLOWED_ORIGINS': '*',
    'PUBLIC_READ_ENDPOINTS': 'true'
})

from main import app

client = TestClient(app)

class TestEnvironmentAwareConfig:
    """Test environment-aware configuration system"""

    def test_development_config_loads(self):
        """Test that development configuration loads without errors"""
        from config.settings import get_settings
        settings = get_settings()
        assert settings.environment.value == "development"
        assert settings.jwt_secret_key is not None
        assert len(settings.jwt_secret_key) >= 32

    def test_health_endpoints_work(self):
        """Test health endpoints are operational"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "trace_id" in data

        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = client.get("/health")
        headers = response.headers

        # Check required security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers

        # HSTS should not be present in development
        assert "Strict-Transport-Security" not in headers

    def test_cors_wildcard_in_development(self):
        """Test CORS allows wildcard in development"""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200

    def test_api_docs_accessible_in_development(self):
        """Test API documentation is accessible in development"""
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

        response = client.get("/openapi.json")
        assert response.status_code == 200

class TestUnifiedErrorFormat:
    """Test unified error response format"""

    def test_404_error_format(self):
        """Test 404 errors use unified format"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()

        # Check unified error schema
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == 404

    def test_validation_error_format(self):
        """Test validation errors use unified format"""
        # Try invalid field type for eligibility check
        response = client.get("/eligibility/check?gpa=invalid")
        assert response.status_code == 422
        data = response.json()

        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == 422

class TestRateLimitingDisabled:
    """Test that rate limiting is properly disabled in test environment"""

    def test_multiple_requests_no_rate_limiting(self):
        """Test multiple rapid requests don't get rate limited"""
        responses = []
        for _i in range(10):  # Make many requests
            response = client.get("/health")
            responses.append(response.status_code)

        # All should succeed (no 429 responses)
        assert all(code == 200 for code in responses)

    def test_sql_injection_patterns_processed(self):
        """Test SQL injection patterns are handled without rate limiting"""
        test_patterns = [
            "'; DROP TABLE scholarships; --",
            "' OR '1'='1",
            "admin'--"
        ]

        for pattern in test_patterns:
            # These should return 422 (validation error) not 429 (rate limited)
            response = client.get(f"/eligibility/check?gpa={pattern}")
            # Should be validation error (422) or success, not rate limited (429)
            assert response.status_code != 429

class TestProductionValidationStrict:
    """Test production validation prevents invalid startup"""

    def test_production_mode_validation_fails(self):
        """Test production mode fails with missing config"""
        import subprocess
        import sys

        # Try to start with production environment but missing config
        result = subprocess.run([
            sys.executable, "-c",
            """
import os
os.environ['ENVIRONMENT'] = 'production'
try:
    from config.settings import get_settings
    settings = get_settings()
    print('ERROR: Production should have failed')
except (RuntimeError, Exception) as e:
    print('SUCCESS: Production validation failed as expected')
    print(f'Error: {str(e)[:100]}...')
"""
        ], capture_output=True, text=True, timeout=10)

        assert "SUCCESS: Production validation failed as expected" in result.stdout

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
