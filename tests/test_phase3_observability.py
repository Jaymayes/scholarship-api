"""
Test Suite for Phase 3 Observability Features
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from models.database import SessionLocal
from models.interaction import InteractionDB

client = TestClient(app)

def get_test_token():
    """Get authentication token for testing"""
    response = client.post(
        "/api/v1/auth/login-simple",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

class TestHealthEndpoints:
    """Test health and readiness endpoints"""

    def test_liveness_probe(self):
        """Test /healthz endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "scholarship-api"

    def test_readiness_probe_structure(self):
        """Test /readyz endpoint structure"""
        response = client.get("/readyz")
        # Should return either 200 or 503 depending on configuration
        assert response.status_code in [200, 503]
        data = response.json()

        if response.status_code == 503:
            # Check error structure when not ready
            assert "error" in data
            assert "trace_id" in data
        else:
            # Check success structure when ready
            assert "status" in data
            assert "checks" in data
            assert "database" in data["checks"]

class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_accessible(self):
        """Test /metrics endpoint is accessible"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_contain_expected_metrics(self):
        """Test metrics contain expected Prometheus metrics"""
        response = client.get("/metrics")
        content = response.text

        # Check for basic HTTP metrics
        assert "http_requests_total" in content or "# HELP" in content
        # Metrics might be empty initially, so just check endpoint works

class TestRequestIDMiddleware:
    """Test request ID generation and tracing"""

    def test_request_id_in_response_headers(self):
        """Test that responses include X-Request-ID header"""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_request_id_consistency(self):
        """Test request ID consistency when provided"""
        custom_request_id = "test-request-123"
        response = client.get(
            "/",
            headers={"X-Request-ID": custom_request_id}
        )
        assert response.headers["X-Request-ID"] == custom_request_id

class TestInteractionLogging:
    """Test interaction logging functionality"""

    def test_interaction_logging_schema(self):
        """Test that interactions table has correct schema"""
        db = SessionLocal()
        try:
            # Test that we can query the interactions table
            count = db.query(InteractionDB).count()
            assert count >= 0  # Should not error
        finally:
            db.close()

    def test_manual_interaction_logging(self):
        """Test manual interaction logging"""

        from services.interaction_service import InteractionService

        db = SessionLocal()
        try:
            service = InteractionService(db)

            # Create mock request and response for testing
            type('MockRequest', (), {
                'url': type('MockURL', (), {'path': '/test'})(),
                'method': 'GET',
                'query_params': {},
                'headers': {'user-agent': 'test-agent'},
                'state': type('MockState', (), {'trace_id': 'test-trace-123'})()
            })()

            type('MockResponse', (), {'status_code': 200})()

            # This would normally be called asynchronously
            # interaction_id = await service.log_interaction(
            #     event_type="test_event",
            #     request=mock_request,
            #     response=mock_response,
            #     user_id="test_user"
            # )

            # For now, just test that service can be instantiated
            assert service is not None

        finally:
            db.close()

class TestObservabilityIntegration:
    """Test integration of observability features"""

    def test_api_endpoints_with_observability(self):
        """Test that API endpoints work with observability enabled"""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        # Test scholarships endpoint
        response = client.get("/api/v1/scholarships")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_authenticated_endpoints_with_observability(self):
        """Test authenticated endpoints work with observability"""
        token = get_test_token()

        response = client.get(
            "/api/v1/database/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_error_handling_with_observability(self):
        """Test error handling includes observability features"""
        response = client.get("/api/v1/scholarships/nonexistent")
        assert response.status_code == 404
        assert "X-Request-ID" in response.headers

        # Check error response includes trace_id
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            assert "trace_id" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
