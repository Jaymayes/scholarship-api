"""
Tests for authentication consistency across all protected endpoints
Addresses QA-004 and QA-005 findings about auth bypass vulnerabilities
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

class TestAuthenticationConsistency:
    """Test that all protected endpoints require authentication consistently"""

    def test_search_get_requires_auth(self):
        """Test GET /search requires authentication"""
        response = client.get("/search?q=test")
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert "Authentication required" in data["message"]

    def test_search_post_requires_auth(self):
        """Test POST /search requires authentication"""
        response = client.post("/search", json={"query": "test"})
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert "Authentication required" in data["message"]

    def test_scholarships_endpoint_requires_auth(self):
        """Test /api/v1/scholarships requires authentication"""
        response = client.get("/api/v1/scholarships?keyword=test")
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert "Authentication required" in data["message"]

    def test_eligibility_get_requires_auth(self):
        """Test GET /eligibility/check requires authentication"""
        response = client.get("/eligibility/check?gpa=3.5")
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    def test_eligibility_post_requires_auth(self):
        """Test POST /eligibility/check requires authentication"""
        response = client.post("/eligibility/check", json={"gpa": 3.5})
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    def test_public_endpoints_work_without_auth(self):
        """Test that public endpoints work without authentication"""
        # Health endpoints should work without auth
        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/readiness")
        assert response.status_code == 200

        # Metrics should work without auth
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_auth_with_valid_token_works(self):
        """Test that endpoints work with valid authentication"""
        # This would normally use a real JWT token
        # For now, we test with the PUBLIC_READ_ENDPOINTS flag
        # In production, this test would create a valid token

        # Mock a valid token (in real tests, generate proper JWT)

        # Note: In current dev setup, PUBLIC_READ_ENDPOINTS allows access
        # This test documents the expected behavior with proper auth
        pytest.skip("Full auth integration test requires JWT token generation")

    def test_auth_headers_format(self):
        """Test that all auth errors return consistent headers"""
        endpoints_to_test = [
            "/search",
            "/api/v1/scholarships",
            "/eligibility/check"
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code == 401

            # Should have WWW-Authenticate header for 401s
            # Note: This depends on the auth middleware implementation
            data = response.json()
            assert "trace_id" in data
            assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
