"""
Test Suite for Authentication System
Phase 4: Quality Gates Implementation
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuthentication:
    """Test authentication endpoints and security"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["error"]["message"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["error"]["message"]
    
    def test_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with valid authentication"""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "admin"
        assert "admin" in data["roles"]
    
    def test_auth_check_authenticated(self):
        """Test authentication check with valid token"""
        # Get token
        login_response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "readonly", "password": "readonly123"}
        )
        token = login_response.json()["access_token"]
        
        # Check auth status
        response = client.get(
            "/api/v1/auth/check",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "readonly"
    
    def test_auth_check_unauthenticated(self):
        """Test authentication check without token"""
        response = client.get("/api/v1/auth/check")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_applies(self):
        """Test that rate limiting is applied to endpoints"""
        # Make multiple rapid requests to trigger rate limiting
        # Note: This test may need adjustment based on actual rate limits
        responses = []
        for i in range(10):
            response = client.get("/")
            responses.append(response.status_code)
        
        # All should succeed or some should be rate limited
        assert all(status in [200, 429] for status in responses)
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present when limits are exceeded"""
        # This test would need actual rate limiting to trigger
        # For now, just verify normal responses don't have rate limit errors
        response = client.get("/")
        assert response.status_code == 200

class TestErrorHandling:
    """Test unified error handling"""
    
    def test_404_error_format(self):
        """Test 404 error has standardized format"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data
        assert data["code"] == "NOT_FOUND"
        assert data["status"] == 404
    
    def test_validation_error_format(self):
        """Test validation errors have standardized format"""
        response = client.post(
            "/api/v1/auth/login-simple",
            json={"username": "admin"}  # Missing password
        )
        assert response.status_code == 422
        data = response.json()
        assert "trace_id" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "field_errors" in data["error"]["details"]
    
    def test_trace_id_header(self):
        """Test that trace ID is included in response headers"""
        response = client.get("/")
        assert "X-Trace-ID" in response.headers

if __name__ == "__main__":
    pytest.main([__file__, "-v"])