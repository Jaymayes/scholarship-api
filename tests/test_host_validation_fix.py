"""
Test Host Validation Fix - Comprehensive CI/Production Security Tests
Ensures TestClient works in CI while maintaining production security
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from config.settings import Settings, Environment


class TestHostValidationFix:
    """Comprehensive host validation testing for CI/production security"""
    
    def test_testserver_allowed_in_development(self):
        """Ensure TestClient works in development environment"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "ok"]
    
    def test_testserver_allowed_in_staging(self):
        """Ensure TestClient works in staging environment"""
        with patch('config.settings.settings.environment', Environment.STAGING):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_localhost_always_allowed(self):
        """Verify localhost works in all environments"""
        for env in [Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]:
            with patch('config.settings.settings.environment', env):
                client = TestClient(app, headers={"Host": "localhost"})
                response = client.get("/health")
                assert response.status_code == 200, f"Failed in {env}"
    
    def test_api_endpoints_work_with_testclient(self):
        """Ensure critical API endpoints work with TestClient"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test core endpoints
            endpoints = ["/health", "/healthz", "/docs", "/openapi.json"]
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code in [200, 301], f"Failed: {endpoint}"
    
    def test_production_rejects_unknown_hosts(self):
        """CRITICAL: Ensure production still blocks unknown hosts"""
        malicious_hosts = [
            "evil.com",
            "attacker.net", 
            "malicious-host.xyz",
            "192.168.1.100"
        ]
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            for bad_host in malicious_hosts:
                client = TestClient(app, headers={"Host": bad_host})
                response = client.get("/health")
                assert response.status_code == 400, f"Production failed to block: {bad_host}"
                assert "not allowed" in response.text.lower()
    
    def test_production_allows_configured_hosts(self):
        """Verify production allows legitimate configured hosts"""
        valid_hosts = ["localhost", "127.0.0.1"]
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            for valid_host in valid_hosts:
                client = TestClient(app, headers={"Host": valid_host})
                response = client.get("/health")
                assert response.status_code == 200, f"Production blocked valid host: {valid_host}"
    
    def test_wildcard_patterns_work(self):
        """Test wildcard pattern matching"""
        test_hosts = [
            "test.replit.app",
            "dev.replit.dev", 
            "workspace.repl.co"
        ]
        
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            for host in test_hosts:
                client = TestClient(app, headers={"Host": host})
                response = client.get("/health")
                assert response.status_code == 200, f"Wildcard failed for: {host}"
    
    def test_case_insensitive_host_matching(self):
        """Verify host matching is case insensitive"""
        hosts = ["LOCALHOST", "TestServer", "127.0.0.1"]
        
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            for host in hosts:
                client = TestClient(app, headers={"Host": host})
                response = client.get("/health")
                assert response.status_code == 200, f"Case sensitivity issue: {host}"
    
    def test_port_stripping_works(self):
        """Ensure ports are properly stripped from host headers"""
        hosts_with_ports = ["localhost:8000", "testserver:5000", "127.0.0.1:3000"]
        
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            for host in hosts_with_ports:
                client = TestClient(app, headers={"Host": host})
                response = client.get("/health")
                assert response.status_code == 200, f"Port stripping failed: {host}"


class TestErrorResponseFormat:
    """Test error response format consistency"""
    
    def test_invalid_host_error_format(self):
        """Verify error response follows unified format"""
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            client = TestClient(app, headers={"Host": "evil.com"})
            response = client.get("/health")
            
            assert response.status_code == 400
            error_data = response.json()
            
            # Verify unified error format
            required_fields = ["code", "message", "status", "timestamp"]
            for field in required_fields:
                assert field in error_data, f"Missing field: {field}"
            
            assert error_data["code"] == "INVALID_HOST"
            assert "evil.com" in error_data["message"]
            assert error_data["status"] == 400


class TestCIIntegration:
    """Test CI/CD pipeline integration requirements"""
    
    def test_comprehensive_endpoint_coverage(self):
        """Test full endpoint coverage for CI validation"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Critical endpoints for CI tests
            endpoints = [
                ("/", "Root endpoint"),
                ("/health", "Health check"),
                ("/healthz", "Kubernetes health"),
                ("/readyz", "Readiness check"),
                ("/metrics", "Prometheus metrics"),
                ("/docs", "API documentation"),
                ("/openapi.json", "OpenAPI spec")
            ]
            
            for endpoint, description in endpoints:
                response = client.get(endpoint)
                assert response.status_code in [200, 503], f"{description} failed: {endpoint}"
    
    def test_api_endpoints_accessible(self):
        """Ensure API endpoints are accessible for testing"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            client = TestClient(app)
            
            # Test API endpoints (may require auth, but should not be host-blocked)
            api_endpoints = [
                "/api/v1/scholarships",
                "/api/v1/search",
                "/api/v1/health/database"
            ]
            
            for endpoint in api_endpoints:
                response = client.get(endpoint)
                # Should not be 400 (host validation error)
                assert response.status_code != 400, f"Host validation blocking: {endpoint}"
                # May be 401/403 (auth required) or 200 (success) - but not host blocked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])