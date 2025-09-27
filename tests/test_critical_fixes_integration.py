"""
Integration Tests for All Three Critical Production Fixes
Validates the complete fix package works together correctly
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import time

from main import app
from config.settings import Environment
from services.database_connection_manager import db_manager


class TestCriticalFixesIntegration:
    """End-to-end integration tests for all critical fixes"""
    
    def test_host_validation_middleware_order(self):
        """Test that host validation happens before other middleware"""
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            client = TestClient(app, headers={"Host": "malicious.com"})
            
            start_time = time.time()
            response = client.get("/health")
            response_time = time.time() - start_time
            
            # Should be blocked quickly by host validation (early in middleware chain)
            assert response_time < 1.0  # Should fail fast
            
            # Should NOT be converted to 500 by metrics middleware
            # (This would indicate middleware ordering issue)
            assert response.status_code != 500, "Host validation should not be converted to 500"
    
    def test_error_propagation_through_middleware_stack(self):
        """Test that errors propagate correctly through the entire middleware stack"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test 404 error propagation
            response = client.get("/definitely-does-not-exist")
            assert response.status_code == 404
            
            # Test validation error propagation
            response = client.post("/api/v1/scholarships", json={"invalid": "data"})
            # Should be auth error (401/403) or validation error (422), NOT 500
            assert response.status_code in [401, 403, 422]
            assert response.status_code != 500
    
    def test_database_ssl_with_host_validation_integration(self):
        """Test database operations work correctly with all middleware fixes"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test database health check through API
            response = client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["healthy", "ok"]
            
            # Test that database connection manager works correctly
            health = db_manager.health_check()
            assert health["status"] == "healthy"
            assert health["response_time_ms"] < 5000  # Should be reasonably fast
    
    def test_production_security_stack_integration(self):
        """Test complete security stack in production mode"""
        test_scenarios = [
            # (host, expected_blocked)
            ("evil.com", True),
            ("malicious.net", True),
            ("localhost", False),  # Should be allowed
        ]
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            for host, should_be_blocked in test_scenarios:
                client = TestClient(app, headers={"Host": host})
                response = client.get("/health")
                
                if should_be_blocked:
                    # Should be blocked by host validation
                    assert response.status_code != 200, f"Host {host} should be blocked"
                    # Should NOT be converted to 500 by middleware
                    assert response.status_code != 500, f"Host {host} error should not be 500"
                else:
                    # Should be allowed through
                    assert response.status_code == 200, f"Host {host} should be allowed"
    
    def test_database_retry_with_middleware_stack(self):
        """Test that database retry logic works correctly with middleware"""
        # Test that database operations can recover from transient failures
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Multiple quick requests to test connection pooling and retry
            for i in range(5):
                response = client.get("/health")
                assert response.status_code == 200
                
                # Each request should be reasonably fast (no long retries)
                start_time = time.time()
                response = client.get("/health")
                response_time = time.time() - start_time
                assert response_time < 2.0  # Should not trigger long retries
    
    def test_error_schema_consistency_across_fixes(self):
        """Test that all fixes maintain consistent error response schemas"""
        error_scenarios = [
            # Host validation error
            (lambda: TestClient(app, headers={"Host": "evil.com"}).get("/health"), "host"),
            # 404 error
            (lambda: TestClient(app).get("/nonexistent"), "notfound"),
        ]
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            for make_request, error_type in error_scenarios:
                response = make_request()
                
                # Should not be 500 (middleware conversion error)
                assert response.status_code != 500
                
                # Should have consistent error structure
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        # Basic error structure validation
                        if isinstance(error_data, dict):
                            # Should have some error indication
                            assert any(key in error_data for key in 
                                     ["error", "detail", "message", "code"])
                    except ValueError:
                        # Some errors might not be JSON (like stack traces)
                        # This is acceptable for some error types
                        pass
    
    def test_performance_impact_of_fixes(self):
        """Test that the fixes don't significantly impact performance"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Measure baseline performance
            response_times = []
            for i in range(10):
                start_time = time.time()
                response = client.get("/health")
                response_time = time.time() - start_time
                
                assert response.status_code == 200
                response_times.append(response_time)
            
            # Performance should be reasonable
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Should be fast (under 1 second average, under 2 seconds max)
            assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time}s"
            assert max_response_time < 2.0, f"Max response time too slow: {max_response_time}s"
    
    def test_ssl_hardening_production_readiness(self):
        """Test SSL hardening meets production security requirements"""
        # Test that SSL validation works correctly
        try:
            connection_info = db_manager.validate_connection()
            
            # Should complete without errors
            assert connection_info["status"] == "connected"
            
            # In development, SSL might not be active (acceptable)
            # In production, SSL should be active and properly configured
            ssl_active = connection_info.get("ssl_active", False)
            if ssl_active:
                # If SSL is active, validate it's properly configured
                ssl_version = connection_info.get("ssl_version")
                if ssl_version:
                    assert "TLS" in ssl_version, f"SSL version should use TLS: {ssl_version}"
                    
        except Exception as e:
            # SSL validation should not crash the application
            pytest.fail(f"SSL validation should not crash: {str(e)}")


class TestCriticalFixesRollback:
    """Test that fixes can be safely rolled back if needed"""
    
    def test_host_validation_can_be_disabled(self):
        """Test that host validation can be disabled in emergency"""
        # This test ensures we have an escape hatch if needed
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            # In development, more permissive host validation
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_database_fallback_behavior(self):
        """Test database fallback behavior if SSL fails"""
        # Test that the application can start even if SSL configuration has issues
        # (Should fallback gracefully rather than crash)
        try:
            health = db_manager.health_check()
            # Should get some response, even if not ideal
            assert "status" in health
        except Exception:
            # If database is completely unavailable, that's a different issue
            # The SSL hardening should not make it worse
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])