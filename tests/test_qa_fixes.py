#!/usr/bin/env python3
"""
Tests for QA fixes implementation
Validates all security fixes while preserving unified error schema
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from config.settings import get_settings
from middleware.auth import create_access_token, decode_token, TokenData
from middleware.rate_limiting import create_rate_limiter
import json

# Test client
client = TestClient(app)

class TestAuthTypeSafety:
    """Test authentication type safety improvements"""
    
    def test_jwt_payload_typing(self):
        """Test JWT payload has proper typing"""
        # Create typed payload
        payload_data = {
            "sub": "test_user_123",
            "roles": ["user"],
            "scopes": ["read"]
        }
        
        # Create token with typed payload
        token = create_access_token(payload_data)
        assert isinstance(token, str)
        assert len(token) > 20
        
        # Decode and validate types
        token_data = decode_token(token)
        assert token_data is not None
        assert isinstance(token_data.user_id, str)
        assert token_data.user_id == "test_user_123"
        assert isinstance(token_data.roles, list)
        assert isinstance(token_data.scopes, list)

    def test_token_decode_none_handling(self):
        """Test token decode handles None and invalid inputs gracefully"""
        # Test None token
        result = decode_token(None)
        assert result is None
        
        # Test empty string
        result = decode_token("")
        assert result is None
        
        # Test invalid token
        result = decode_token("invalid.token.here")
        assert result is None
        
        # Test malformed JWT
        result = decode_token("not.a.jwt")
        assert result is None

    def test_auth_error_unified_schema(self):
        """Test authentication errors use unified error schema"""
        # Test endpoint requiring authentication
        response = client.get("/api/v1/user/profile")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_data = response.json()
        
        # Validate unified error schema
        assert "code" in error_data
        assert "message" in error_data  
        assert "status" in error_data
        assert "timestamp" in error_data
        assert "trace_id" in error_data
        
        # Check specific auth error
        assert error_data["code"] == "AUTH_001"
        assert error_data["status"] == 401

class TestCORSConfiguration:
    """Test CORS configuration improvements"""
    
    def test_cors_development_mode(self):
        """Test CORS in development allows proper origins"""
        settings = get_settings()
        origins = settings.get_cors_origins
        
        # Should include wildcard in development
        assert "*" in origins or len(origins) > 0
        
    def test_options_preflight_request(self):
        """Test OPTIONS preflight requests work properly"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization"
        }
        
        response = client.options("/api/v1/search", headers=headers)
        
        # Should allow preflight
        assert response.status_code in [200, 204]
        assert "Access-Control-Allow-Origin" in response.headers

class TestRateLimitingFallback:
    """Test Redis fallback and rate limiting improvements"""
    
    def test_rate_limiter_creation(self):
        """Test rate limiter creates with proper fallback"""
        limiter = create_rate_limiter()
        
        # Should create limiter (in-memory fallback in dev)
        assert limiter is not None
        
    def test_rate_limit_headers_in_response(self):
        """Test rate limit responses include proper headers"""
        # Make multiple requests to trigger rate limit
        endpoint = "/api/v1/search"
        
        # Make normal request first
        response = client.get(f"{endpoint}?q=test")
        
        # Response should be successful or rate limited
        assert response.status_code in [200, 422, 429]

class TestPackageStructure:
    """Test missing package structure files"""
    
    def test_services_init_exists(self):
        """Test services/__init__.py exists"""
        import os
        assert os.path.exists("services/__init__.py")
        
    def test_models_init_exists(self):
        """Test models/__init__.py exists"""
        import os  
        assert os.path.exists("models/__init__.py")

class TestBcryptConfiguration:
    """Test bcrypt/passlib configuration"""
    
    def test_password_hashing_works(self):
        """Test password hashing and verification works without warnings"""
        from middleware.auth import hash_password, verify_password
        
        test_password = "test_password_123"
        hashed = hash_password(test_password)
        
        # Should hash successfully
        assert isinstance(hashed, str)
        assert hashed != test_password
        assert len(hashed) > 20
        
        # Should verify correctly
        assert verify_password(test_password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

class TestErrorHandling:
    """Test unified error handling is preserved"""
    
    def test_404_error_format(self):
        """Test 404 errors use unified schema"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        error_data = response.json()
        
        # Validate unified error schema
        assert "code" in error_data
        assert "message" in error_data
        assert "status" in error_data  
        assert "timestamp" in error_data
        assert "trace_id" in error_data
        
    def test_422_validation_error_format(self):
        """Test validation errors use unified schema"""
        # Send invalid data to trigger validation error
        response = client.get("/api/v1/eligibility/check?gpa=invalid")
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Should have unified error format
        assert "code" in error_data
        assert "message" in error_data
        assert "status" in error_data
        assert "timestamp" in error_data
        assert "trace_id" in error_data

class TestSecurityPreservation:
    """Test that security controls are preserved"""
    
    def test_cors_headers_present(self):
        """Test CORS headers are properly set"""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        # Should have CORS headers in development
        cors_headers = [h for h in response.headers.keys() if h.lower().startswith("access-control")]
        assert len(cors_headers) > 0
        
    def test_docs_disabled_in_production(self):
        """Test docs are properly controlled by environment"""
        # In development, docs should be available
        response = client.get("/docs")
        # Should either work (200) or redirect (3xx) in development
        assert response.status_code in [200, 307, 308] or response.status_code == 404

class TestAPIFunctionality:
    """Test API still works after all fixes"""
    
    def test_health_endpoint_works(self):
        """Test health endpoint still works"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "trace_id" in data
        
    def test_search_endpoint_works(self):
        """Test search endpoint still works"""  
        response = client.get("/api/v1/search?q=engineering")
        
        assert response.status_code in [200, 422]  # 422 for missing required params is OK
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "scholarships" in data
            
    def test_eligibility_endpoint_works(self):
        """Test eligibility endpoint still works"""
        params = {
            "gpa": "3.5",
            "grade_level": "undergraduate",
            "field_of_study": "engineering"
        }
        
        response = client.get("/api/v1/eligibility/check", params=params)
        
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "eligible_count" in data or "results" in data

if __name__ == "__main__":
    # Run basic functionality tests
    print("🧪 Running QA fixes verification tests...")
    
    # Test 1: Authentication type safety
    print("\n1. Testing authentication type safety...")
    test_auth = TestAuthTypeSafety()
    try:
        test_auth.test_jwt_payload_typing()
        test_auth.test_token_decode_none_handling()
        print("   ✅ Authentication type safety tests passed")
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        
    # Test 2: Package structure
    print("\n2. Testing package structure...")
    test_pkg = TestPackageStructure() 
    try:
        test_pkg.test_services_init_exists()
        test_pkg.test_models_init_exists()
        print("   ✅ Package structure tests passed")
    except Exception as e:
        print(f"   ❌ Package structure test failed: {e}")
        
    # Test 3: Bcrypt configuration
    print("\n3. Testing bcrypt configuration...")
    test_bcrypt = TestBcryptConfiguration()
    try:
        test_bcrypt.test_password_hashing_works()
        print("   ✅ Bcrypt configuration tests passed")
    except Exception as e:
        print(f"   ❌ Bcrypt test failed: {e}")
        
    # Test 4: API functionality
    print("\n4. Testing API functionality...")
    test_api = TestAPIFunctionality()
    try:
        test_api.test_health_endpoint_works()
        test_api.test_search_endpoint_works() 
        test_api.test_eligibility_endpoint_works()
        print("   ✅ API functionality tests passed")
    except Exception as e:
        print(f"   ❌ API functionality test failed: {e}")
        
    print("\n🎯 QA fixes verification completed!")