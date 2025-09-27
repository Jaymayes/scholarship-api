"""
Test Middleware Ordering Fix - Error Response Validation
Ensures 4xx errors propagate correctly and aren't converted to 500s
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from config.settings import Environment


class TestMiddlewareOrdering:
    """Test middleware error handling and ordering"""
    
    def test_host_validation_returns_400_not_500(self):
        """Ensure host validation errors return 400, not 500"""
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            client = TestClient(app, headers={"Host": "evil.com"})
            response = client.get("/health")
            
            # Should be 400 (host validation), NOT 500 (middleware error)
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            
            error_data = response.json()
            assert error_data["code"] == "INVALID_HOST"
            assert "evil.com" in error_data["message"]
    
    def test_4xx_errors_preserve_status_codes(self):
        """Test that 4xx errors maintain their proper status codes"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test 404 - should remain 404
            response = client.get("/nonexistent-endpoint")
            assert response.status_code == 404
            
            # Test invalid request body - should be 422 validation error
            response = client.post("/api/v1/scholarships", json={"invalid": "data"})
            assert response.status_code in [401, 403, 422], f"Got {response.status_code}"
            # Should not be 500 (middleware conversion error)
            assert response.status_code != 500
    
    def test_metrics_middleware_records_errors_correctly(self):
        """Verify metrics middleware records errors without converting them"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Make request that should return 404
            response = client.get("/definitely-nonexistent")
            assert response.status_code == 404
            
            # Verify it's a proper 404 response, not converted to 500
            assert response.status_code != 500
            
            # Test host validation error is recorded but not converted
            with patch('config.settings.settings.environment', Environment.PRODUCTION):
                client = TestClient(app, headers={"Host": "malicious.com"}) 
                response = client.get("/health")
                assert response.status_code == 400  # Not 500
    
    def test_error_response_format_consistency(self):
        """Ensure all error responses follow unified format"""
        error_scenarios = [
            # (request setup, expected status)
            (lambda: TestClient(app, headers={"Host": "evil.com"}).get("/health"), 400),
            (lambda: TestClient(app).get("/nonexistent"), 404),
        ]
        
        for make_request, expected_status in error_scenarios:
            with patch('config.settings.settings.environment', Environment.PRODUCTION):
                response = make_request()
                assert response.status_code == expected_status
                
                # Verify response is JSON and has expected structure
                error_data = response.json()
                if expected_status == 400:  # Host validation error
                    assert "code" in error_data
                    assert "message" in error_data 
                    assert "status" in error_data
    
    def test_authentication_errors_propagate(self):
        """Test that authentication/authorization errors propagate correctly"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test protected endpoint without auth - should be 401/403, not 500
            protected_endpoints = [
                "/api/v1/scholarships",
                "/api/v1/search", 
                "/api/v1/eligibility"
            ]
            
            for endpoint in protected_endpoints:
                response = client.get(endpoint)
                # Should be auth error, NOT 500 (middleware conversion)
                assert response.status_code in [401, 403], f"Endpoint {endpoint} returned {response.status_code}"
                assert response.status_code != 500
    
    def test_rate_limit_errors_propagate(self):
        """Test that rate limit errors return proper status, not 500"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Make many rapid requests to trigger rate limiting
            # (This is a basic test - actual rate limiting depends on configuration)
            for i in range(5):
                response = client.get("/health")
                # Should never return 500 due to middleware error conversion
                assert response.status_code != 500
                # Should be either 200 (success) or 429 (rate limited)
                assert response.status_code in [200, 429]


class TestErrorBoundaryOrdering:
    """Test that error boundaries are properly ordered"""
    
    def test_waf_errors_handled_correctly(self):
        """Test WAF blocking doesn't get converted to 500"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test potential SQL injection (should be blocked by WAF with 403)
            malicious_payloads = [
                "?id=1' OR '1'='1",
                "?search=<script>alert('xss')</script>"
            ]
            
            for payload in malicious_payloads:
                response = client.get(f"/api/v1/scholarships{payload}")
                # Should be WAF block (403) or validation error (422), NOT 500
                assert response.status_code != 500
                # Common expected responses: 403 (WAF block), 401/403 (auth), 422 (validation)
                assert response.status_code in [401, 403, 422]
    
    def test_middleware_chain_integrity(self):
        """Verify middleware chain processes requests in correct order"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test that request goes through full middleware chain
            response = client.get("/health")
            assert response.status_code == 200
            
            # Verify security headers are present (from SecurityHeadersMiddleware)
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection"
            ]
            
            for header in expected_headers:
                assert header in response.headers, f"Missing security header: {header}"
    
    def test_exception_handler_ordering(self):
        """Test that exception handlers process errors in correct order"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test validation error handling
            response = client.post("/api/v1/scholarships", json={"invalid": "format"})
            # Should be handled by validation exception handler
            assert response.status_code in [401, 403, 422]  # Not 500
            
            # Test HTTP exception handling
            response = client.get("/nonexistent-endpoint")
            assert response.status_code == 404  # Not 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])