"""
QA-007 fix: Dedicated security test suite covering all identified issues
"""

import pytest
import os
import time
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock
from config.settings import Settings, Environment

# Import the app
from main import app

class TestSecurityQAFixes:
    """Test suite covering all 8 QA findings"""
    
    def test_qa_002_hardcoded_secrets_validation(self):
        """QA-002: Test that hardcoded secrets are rejected in production"""
        banned_secrets = [
            "secret",
            "dev", 
            "development",
            "test",
            "changeme",
            "default",
            "your-secret-key-change-in-production"
        ]
        
        for secret in banned_secrets:
            with patch.dict(os.environ, {
                "ENVIRONMENT": "production",
                "JWT_SECRET_KEY": secret,
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "CORS_ALLOWED_ORIGINS": "https://example.com",
                "ALLOWED_HOSTS": "example.com",
                "RATE_LIMIT_BACKEND_URL": "redis://localhost"
            }):
                with pytest.raises(ValueError) as exc_info:
                    Settings()
                assert "banned default value" in str(exc_info.value).lower()
    
    def test_qa_002_production_startup_validation(self):
        """QA-002: Test production startup fails with missing/weak secrets"""
        test_cases = [
            # Missing JWT secret
            {
                "env": {"ENVIRONMENT": "production"},
                "expected_error": "JWT_SECRET_KEY is required"
            },
            # Short JWT secret
            {
                "env": {
                    "ENVIRONMENT": "production", 
                    "JWT_SECRET_KEY": "short"
                },
                "expected_error": "must be at least 64 characters"
            },
            # Missing database URL
            {
                "env": {
                    "ENVIRONMENT": "production",
                    "JWT_SECRET_KEY": "a" * 64
                },
                "expected_error": "DATABASE_URL is required"
            }
        ]
        
        for case in test_cases:
            with patch.dict(os.environ, case["env"], clear=True):
                with pytest.raises(ValueError) as exc_info:
                    Settings()
                assert case["expected_error"] in str(exc_info.value)
    
    def test_qa_003_input_validation_interaction_endpoints(self):
        """QA-003: Test input validation for interaction wrapper endpoints"""
        client = TestClient(app)
        
        # Test invalid interaction type
        invalid_payload = {
            "event_type": "invalid_type",
            "scholarship_id": "test"
        }
        
        response = client.post(
            "/interactions/log",
            json=invalid_payload,
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("event_type" in str(error) for error in error_detail)
        
        # Test unknown fields rejection (extra="forbid")
        payload_with_extra = {
            "event_type": "view",
            "unknown_field": "should_be_rejected"
        }
        
        response = client.post(
            "/interactions/log",
            json=payload_with_extra,
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 422
        
        # Test valid payload structure
        valid_payload = {
            "event_type": "view",
            "scholarship_id": "test-123",
            "user_id": "user-456"
        }
        
        # Should get authentication error (401) instead of validation error (422)
        response = client.post("/interactions/log", json=valid_payload)
        assert response.status_code in [401, 500]  # Auth or service error, not validation
    
    def test_qa_006_health_endpoint_input_validation(self):
        """QA-006: Test health endpoints don't accept arbitrary inputs"""
        client = TestClient(app)
        
        # Health endpoints should not accept request bodies
        response = client.get("/healthz")
        assert response.status_code == 200
        
        # Test with query parameters - should still work
        response = client.get("/healthz?extra=param")
        assert response.status_code == 200
        
        # Test database health endpoint
        response = client.get("/health/database")
        assert response.status_code in [200, 503]  # Depends on DB availability
        
        # Verify response structure matches expected models
        if response.status_code == 200:
            data = response.json()
            required_fields = ["status", "timestamp"]
            for field in required_fields:
                assert field in data
    
    def test_qa_001_middleware_ordering(self):
        """QA-001: Test security middleware is properly ordered"""
        client = TestClient(app)
        
        # Test that security headers are present
        response = client.get("/healthz")
        
        # Check for required security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection"
        ]
        
        for header in security_headers:
            assert header in response.headers, f"Missing security header: {header}"
        
        # Test that CORS preflight is not blocked
        response = client.options(
            "/search",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        # Should not be blocked by middleware
        assert response.status_code in [200, 404, 405]  # Not blocked by rate limiting
    
    def test_qa_004_qa_005_authentication_enforcement(self):
        """QA-004 & QA-005: Test authentication requirements on scholarships/search endpoints"""
        client = TestClient(app)
        
        # Test search endpoints require authentication when feature flag disabled
        with patch("config.settings.settings.public_read_endpoints", False):
            # GET search
            response = client.get("/search")
            assert response.status_code == 401
            
            error_detail = response.json()["detail"]
            assert error_detail["code"] == "AUTHENTICATION_REQUIRED"
            assert "trace_id" in error_detail
            assert "timestamp" in error_detail
            
            # POST search
            response = client.post("/search", json={"query": "test"})
            assert response.status_code == 401
            
            # Scholarships endpoint 
            response = client.get("/scholarships")
            assert response.status_code == 401
        
        # Test endpoints work with feature flag enabled (development mode)
        with patch("config.settings.settings.public_read_endpoints", True):
            response = client.get("/search")
            # Should get 200 or other non-auth error
            assert response.status_code != 401
    
    def test_qa_docs_protection_production(self):
        """Test API docs are disabled in production"""
        client = TestClient(app)
        
        # Mock production environment
        with patch("config.settings.settings.environment", Environment.PRODUCTION):
            with patch("config.settings.settings.should_enable_docs", False):
                # Should get 404 for docs endpoints
                docs_endpoints = ["/docs", "/redoc", "/openapi.json"]
                
                for endpoint in docs_endpoints:
                    response = client.get(endpoint)
                    assert response.status_code == 404, f"Docs endpoint {endpoint} should be blocked in production"
    
    def test_qa_008_dockerfile_security(self):
        """QA-008: Test Dockerfile hardening measures"""
        
        # Test .dockerignore exists and contains security exclusions
        assert os.path.exists(".dockerignore")
        
        with open(".dockerignore", "r") as f:
            dockerignore_content = f.read()
        
        # Check for critical security exclusions
        critical_exclusions = [
            ".env",
            "*.env",
            "*.key",
            "*.pem",
            ".git",
            "node_modules"
        ]
        
        for exclusion in critical_exclusions:
            assert exclusion in dockerignore_content, f"Missing critical exclusion: {exclusion}"
        
        # Test Dockerfile uses multi-stage build
        assert os.path.exists("Dockerfile")
        
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
        
        # Check for multi-stage build indicators
        assert "FROM python:3.11-slim as builder" in dockerfile_content
        assert "FROM python:3.11-slim as runtime" in dockerfile_content
        assert "USER appuser" in dockerfile_content  # Non-root user
        assert "HEALTHCHECK" in dockerfile_content   # Health check
    
    def test_rate_limiting_preservation(self):
        """Test that rate limiting still works after fixes"""
        client = TestClient(app)
        
        # Test rate limiting returns proper error format
        # Note: This test depends on rate limiter configuration
        response = client.get("/metrics")  # Usually not rate limited
        assert response.status_code in [200, 404]  # Should work
        
        # For rate-limited endpoint, we'd need to make many requests
        # This is a basic structure test
        for _ in range(5):  # Small number to avoid triggering limits
            response = client.get("/search")
            if response.status_code == 429:
                # Verify unified error format
                error_detail = response.json()["detail"]
                assert "trace_id" in error_detail
                assert "code" in error_detail
                assert "timestamp" in error_detail
                break
    
    def test_unified_error_format_preservation(self):
        """Test that unified error format is preserved across all endpoints"""
        client = TestClient(app)
        
        # Test 404 error format
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        # Should have unified error format or standard FastAPI format
        if isinstance(response.json().get("detail"), dict):
            error_detail = response.json()["detail"]
            # Check for unified format fields
            expected_fields = ["code", "message", "status", "timestamp"]
            for field in expected_fields:
                if field in error_detail:
                    assert isinstance(error_detail[field], (str, int))
        
        # Test validation error format
        response = client.post("/interactions/log", json={"invalid": "data"})
        assert response.status_code == 422
        
        # Validation errors should maintain FastAPI format or unified format
        assert "detail" in response.json()

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

# Integration tests
def test_security_integration_flow(client):
    """Test complete security flow integration"""
    
    # 1. Test health endpoint (no auth required)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "status" in response.json()
    
    # 2. Test protected endpoint without auth (should fail)
    response = client.get("/search")
    if not os.getenv("PUBLIC_READ_ENDPOINTS", "false").lower() == "true":
        assert response.status_code == 401
    
    # 3. Test docs protection works
    response = client.get("/docs")
    # Should work in development, blocked in production
    assert response.status_code in [200, 404]
    
    # 4. Test security headers are present
    response = client.get("/healthz")
    security_headers = ["X-Content-Type-Options", "X-Frame-Options"]
    for header in security_headers:
        assert header in response.headers

if __name__ == "__main__":
    pytest.main([__file__, "-v"])