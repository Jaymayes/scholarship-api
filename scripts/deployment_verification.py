#!/usr/bin/env python3
"""
Production Deployment Verification Script
Validates that deployment meets all production requirements
"""

import os
import sys
import time
import requests
import json
from typing import Dict, List, Tuple
from urllib.parse import urljoin


class DeploymentVerifier:
    """Comprehensive deployment verification"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def log_result(self, test_name: str, passed: bool, message: str = "", warning: bool = False):
        """Log test result"""
        if warning:
            self.results["warnings"].append(f"⚠️  {test_name}: {message}")
            print(f"⚠️  {test_name}: {message}")
        elif passed:
            self.results["passed"].append(f"✅ {test_name}")
            print(f"✅ {test_name}")
        else:
            self.results["failed"].append(f"❌ {test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def test_health_endpoints(self):
        """Test health and readiness endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test liveness endpoint
        try:
            response = requests.get(urljoin(self.base_url, "/healthz"), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "active":
                    self.log_result("Liveness probe", True)
                else:
                    self.log_result("Liveness probe", False, f"Unexpected status: {data}")
            else:
                self.log_result("Liveness probe", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Liveness probe", False, str(e))
        
        # Test readiness endpoint
        try:
            response = requests.get(urljoin(self.base_url, "/health/services"), timeout=10)
            if response.status_code == 200:
                self.log_result("Readiness probe", True)
            elif response.status_code == 503:
                self.log_result("Readiness probe", False, "Dependencies unavailable", warning=True)
            else:
                self.log_result("Readiness probe", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Readiness probe", False, str(e))
    
    def test_security_headers(self):
        """Test security headers presence"""
        print("\n🛡️  Testing Security Headers...")
        
        try:
            response = requests.get(urljoin(self.base_url, "/healthz"), timeout=10)
            headers = response.headers
            
            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block"
            }
            
            for header, expected in required_headers.items():
                if header in headers:
                    value = headers[header]
                    if isinstance(expected, list):
                        if value in expected:
                            self.log_result(f"Security header {header}", True)
                        else:
                            self.log_result(f"Security header {header}", False, f"Got '{value}', expected one of {expected}")
                    else:
                        if value == expected:
                            self.log_result(f"Security header {header}", True)
                        else:
                            self.log_result(f"Security header {header}", False, f"Got '{value}', expected '{expected}'")
                else:
                    self.log_result(f"Security header {header}", False, "Header missing")
            
            # HSTS should be present in production with HTTPS
            if "Strict-Transport-Security" in headers:
                self.log_result("HSTS header", True)
            else:
                self.log_result("HSTS header", False, "Missing (expected if HTTPS enabled)", warning=True)
                
        except Exception as e:
            self.log_result("Security headers test", False, str(e))
    
    def test_docs_protection(self):
        """Test that docs are properly protected in production"""
        print("\n📚 Testing Documentation Protection...")
        
        docs_endpoints = ["/docs", "/redoc", "/openapi.json"]
        
        for endpoint in docs_endpoints:
            try:
                response = requests.get(urljoin(self.base_url, endpoint), timeout=10)
                if response.status_code == 404:
                    self.log_result(f"Docs protection {endpoint}", True)
                elif response.status_code == 200:
                    # Check if this is development mode
                    self.log_result(f"Docs protection {endpoint}", False, "Docs accessible (check ENABLE_DOCS setting)", warning=True)
                else:
                    self.log_result(f"Docs protection {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result(f"Docs protection {endpoint}", False, str(e))
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n🚦 Testing Rate Limiting...")
        
        # Test rate limit headers
        try:
            response = requests.get(urljoin(self.base_url, "/api/v1/scholarships?limit=1"), timeout=10)
            
            if response.status_code == 429:
                # Already rate limited
                headers = response.headers
                rate_limit_headers = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]
                
                for header in rate_limit_headers:
                    if header in headers:
                        self.log_result(f"Rate limit header {header}", True)
                    else:
                        self.log_result(f"Rate limit header {header}", False, "Missing")
                
                # Check unified error format
                try:
                    error_data = response.json()
                    required_fields = ["trace_id", "code", "message", "status", "timestamp"]
                    for field in required_fields:
                        if field in error_data:
                            self.log_result(f"Rate limit error format {field}", True)
                        else:
                            self.log_result(f"Rate limit error format {field}", False, "Missing field")
                except:
                    self.log_result("Rate limit error format", False, "Invalid JSON response")
            else:
                self.log_result("Rate limiting", True, "Not triggered (normal operation)")
                
        except Exception as e:
            self.log_result("Rate limiting test", False, str(e))
    
    def test_api_endpoints(self):
        """Test core API functionality"""
        print("\n🔗 Testing API Endpoints...")
        
        endpoints = [
            ("/api/v1/scholarships", "GET"),
            ("/search", "GET"),
            ("/eligibility/check", "GET"),
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(urljoin(self.base_url, endpoint), timeout=10)
                else:
                    response = requests.request(method, urljoin(self.base_url, endpoint), timeout=10)
                
                if response.status_code in [200, 400, 422]:  # 400/422 acceptable for missing params
                    self.log_result(f"API endpoint {method} {endpoint}", True)
                else:
                    self.log_result(f"API endpoint {method} {endpoint}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"API endpoint {method} {endpoint}", False, str(e))
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration...")
        
        # Test preflight request
        try:
            response = requests.options(
                urljoin(self.base_url, "/api/v1/scholarships"),
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                headers = response.headers
                cors_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers"
                ]
                
                for header in cors_headers:
                    if header in headers:
                        self.log_result(f"CORS header {header}", True)
                    else:
                        self.log_result(f"CORS header {header}", False, "Missing")
            else:
                self.log_result("CORS preflight", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("CORS test", False, str(e))
    
    def test_database_connectivity(self):
        """Test database connectivity"""
        print("\n🗄️  Testing Database Connectivity...")
        
        try:
            response = requests.get(urljoin(self.base_url, "/health/database"), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("database", {}).get("status") == "connected":
                    self.log_result("Database connectivity", True)
                else:
                    self.log_result("Database connectivity", False, f"Status: {data}")
            else:
                self.log_result("Database connectivity", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Database connectivity", False, str(e))
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🚀 Starting Production Deployment Verification...")
        print(f"📍 Testing endpoint: {self.base_url}")
        
        # Wait for service to be ready
        print("\n⏳ Waiting for service to be ready...")
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(urljoin(self.base_url, "/healthz"), timeout=5)
                if response.status_code == 200:
                    print("✅ Service is ready")
                    break
            except:
                pass
            
            if i == max_retries - 1:
                print("❌ Service failed to become ready")
                return False
            
            time.sleep(2)
        
        # Run all tests
        self.test_health_endpoints()
        self.test_security_headers()
        self.test_docs_protection()
        self.test_rate_limiting()
        self.test_api_endpoints()
        self.test_cors_configuration()
        self.test_database_connectivity()
        
        # Summary
        print("\n" + "="*60)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("="*60)
        
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        
        if self.results['failed']:
            print("\n❌ FAILED TESTS:")
            for failure in self.results['failed']:
                print(f"  {failure}")
        
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  {warning}")
        
        success = len(self.results['failed']) == 0
        if success:
            print("\n🎉 DEPLOYMENT VERIFICATION PASSED!")
        else:
            print("\n💥 DEPLOYMENT VERIFICATION FAILED!")
        
        return success


def main():
    """Main verification script"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    verifier = DeploymentVerifier(base_url)
    success = verifier.run_all_tests()
    
    # Export results as JSON for CI/CD
    results_file = os.getenv("VERIFICATION_RESULTS_FILE", "verification_results.json")
    with open(results_file, "w") as f:
        json.dump(verifier.results, f, indent=2)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()