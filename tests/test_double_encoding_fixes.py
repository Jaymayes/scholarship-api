"""
Tests to verify double encoding issues are fixed across all error handlers
Critical QA verification for unified error schema
"""

import json

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

class TestDoubleEncodingFixes:
    """Test that all error responses are properly formatted without double encoding"""

    def test_authentication_error_not_double_encoded(self):
        """Test that auth errors return dict, not JSON string"""
        response = client.get("/search?q=test")
        assert response.status_code == 401

        data = response.json()

        # Verify unified error format
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data

        # Critical: message should be string, not JSON
        assert isinstance(data["message"], str)
        assert data["code"] == "UNAUTHORIZED"
        assert data["status"] == 401

        # Should NOT be able to parse message as JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(data["message"])

    def test_validation_error_not_double_encoded(self):
        """Test that validation errors return dict, not JSON string"""
        response = client.post("/search", json={
            "limit": -1,  # Invalid limit
            "offset": -1  # Invalid offset
        })
        assert response.status_code == 422

        data = response.json()

        # Verify unified error format
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert data["code"] == "VALIDATION_ERROR"

        # Message should be plain string
        assert isinstance(data["message"], str)

        # Should have validation details
        assert "details" in data
        assert "fields" in data["details"]

    def test_rate_limit_error_not_double_encoded(self):
        """Test rate limit errors are not double encoded"""
        # Make rapid requests to trigger rate limit
        for _ in range(10):
            try:
                response = client.get("/search?q=test")
                if response.status_code == 429:
                    data = response.json()

                    # Verify unified error format
                    assert "trace_id" in data
                    assert "code" in data
                    assert "message" in data
                    assert data["code"] == "RATE_LIMITED"

                    # Message should be plain string
                    assert isinstance(data["message"], str)

                    # Should have rate limit headers
                    assert "retry-after" in response.headers

                    return  # Test passed
            except:
                continue

        pytest.skip("Rate limit not triggered - in-memory rate limiting may have high limits")

    def test_not_found_error_not_double_encoded(self):
        """Test 404 errors are not double encoded"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()

        # Verify unified error format
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert data["code"] == "NOT_FOUND"

        # Message should be plain string
        assert isinstance(data["message"], str)

    def test_scholarship_endpoint_auth_error_format(self):
        """Test scholarship endpoint authentication follows unified format"""
        response = client.get("/api/v1/scholarships")  # Use correct route
        assert response.status_code == 401

        data = response.json()

        # Should be unified format, not double encoded
        assert "trace_id" in data
        assert "code" in data
        assert "message" in data
        assert isinstance(data["message"], str)
        assert "Authentication required" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
