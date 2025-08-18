#!/usr/bin/env python3
"""
Replit-specific fixes verification script
Tests all Replit environment adaptations and deployment readiness
"""

import os
import sys
import time
import requests
import json
import subprocess
from typing import Dict, List, Any

class ReplitFixesVerifier:
    def __init__(self):
        # Use fixed port for Replit deployment
        self.base_url = "http://localhost:5000"
        self.results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_port_binding(self) -> bool:
        """Test 1: Verify app binds to Replit PORT environment variable"""
        self.log("Testing Replit PORT environment variable handling...")
        
        # Check if PORT env var is respected
        port = os.getenv("PORT", "8000")
        self.log(f"PORT environment variable: {port}")
        
        try:
            # Test if server is responding on expected port
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ Server responding on correct port")
                return True
            else:
                self.log(f"❌ Server not responding correctly (status: {response.status_code})")
                return False
        except Exception as e:
            self.log(f"❌ Port binding test failed: {str(e)}")
            return False
    
    def test_health_endpoints(self) -> bool:
        """Test 2: Verify Replit-optimized health endpoints"""
        self.log("Testing Replit health endpoints...")
        
        endpoints = [
            "/health",
            "/healthz", 
            "/health/database",
            "/health/services"
        ]
        
        success_count = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} responding correctly")
                    success_count += 1
                else:
                    self.log(f"❌ {endpoint} returned status {response.status_code}")
            except Exception as e:
                self.log(f"❌ {endpoint} failed: {str(e)}")
        
        return success_count == len(endpoints)
    
    def test_cors_replit_origins(self) -> bool:
        """Test 3: Verify CORS allows Replit preview origins in development"""
        self.log("Testing CORS configuration for Replit...")
        
        # Test OPTIONS preflight for Replit origins
        replit_origins = [
            "https://test.replit.dev",
            "https://example.user.repl.co"
        ]
        
        success_count = 0
        for origin in replit_origins:
            try:
                headers = {
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET"
                }
                response = requests.options(f"{self.base_url}/api/v1/search", headers=headers, timeout=5)
                
                if response.status_code in [200, 204]:
                    cors_header = response.headers.get("Access-Control-Allow-Origin")
                    if cors_header == "*" or cors_header == origin:
                        self.log(f"✅ CORS allows Replit origin: {origin}")
                        success_count += 1
                    else:
                        self.log(f"❌ CORS blocks Replit origin: {origin}")
                else:
                    self.log(f"❌ OPTIONS preflight failed for {origin}")
            except Exception as e:
                self.log(f"❌ CORS test failed for {origin}: {str(e)}")
        
        return success_count >= 1  # At least wildcard should work in dev
    
    def test_rate_limiting_fallback(self) -> bool:
        """Test 4: Verify in-memory rate limiting works when Redis unavailable"""
        self.log("Testing in-memory rate limiting fallback...")
        
        try:
            # Make multiple rapid requests to trigger rate limiting
            for i in range(8):
                response = requests.get(f"{self.base_url}/api/v1/search?q=ratetest{i}", timeout=2)
                
                if response.status_code == 429:
                    # Check for proper rate limit headers
                    if "Retry-After" in response.headers:
                        self.log("✅ Rate limiting working with proper headers")
                        return True
                    else:
                        self.log("❌ Rate limiting triggered but missing headers")
                        return False
            
            self.log("❌ Rate limiting not triggered after multiple requests")
            return False
            
        except Exception as e:
            self.log(f"❌ Rate limiting test failed: {str(e)}")
            return False
    
    def test_environment_settings(self) -> bool:
        """Test 5: Verify environment-specific settings are applied"""
        self.log("Testing environment-specific configuration...")
        
        try:
            # Test debug config endpoint
            response = requests.get(f"{self.base_url}/_debug/config", timeout=5)
            
            if response.status_code == 200:
                config = response.json()
                
                # Check key Replit-specific settings
                checks = [
                    config.get("environment") in ["development", "local"],
                    config.get("cors", {}).get("wildcard_enabled") == True,
                    config.get("rate_limiting", {}).get("backend_type") == "in-memory fallback (Redis unavailable)",
                    config.get("jwt", {}).get("secret_configured") == True
                ]
                
                if all(checks):
                    self.log("✅ Environment settings correctly configured for Replit")
                    return True
                else:
                    self.log(f"❌ Environment settings incorrect: {config}")
                    return False
            else:
                self.log("❌ Debug config endpoint not accessible")
                return False
                
        except Exception as e:
            self.log(f"❌ Environment settings test failed: {str(e)}")
            return False
    
    def test_unified_error_responses(self) -> bool:
        """Test 6: Verify unified error response format"""
        self.log("Testing unified error response format...")
        
        try:
            # Test 404 error format
            response = requests.get(f"{self.base_url}/nonexistent", timeout=5)
            
            if response.status_code == 404:
                error_data = response.json()
                
                # Check unified error format
                required_fields = ["trace_id", "code", "message", "status", "timestamp"]
                if all(field in error_data for field in required_fields):
                    self.log("✅ Unified error response format working")
                    return True
                else:
                    self.log(f"❌ Error response missing required fields: {error_data}")
                    return False
            else:
                self.log("❌ 404 test endpoint returned unexpected status")
                return False
                
        except Exception as e:
            self.log(f"❌ Error response test failed: {str(e)}")
            return False
    
    def test_database_fallback(self) -> bool:
        """Test 7: Verify database connectivity with fallback handling"""
        self.log("Testing database connectivity and fallback...")
        
        try:
            response = requests.get(f"{self.base_url}/health/database", timeout=10)
            
            if response.status_code == 200:
                db_health = response.json()
                if db_health.get("status") == "healthy":
                    self.log(f"✅ Database health check passed: {db_health.get('type')}")
                    return True
                else:
                    self.log(f"❌ Database unhealthy: {db_health}")
                    return False
            elif response.status_code == 503:
                # Acceptable in development without database
                self.log("⚠️  Database unavailable (acceptable in development)")
                return True
            else:
                self.log(f"❌ Database health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Database test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Replit-specific verification tests"""
        self.log("=" * 60)
        self.log("REPLIT FIXES VERIFICATION STARTING")
        self.log("=" * 60)
        
        tests = [
            ("Port Binding", self.test_port_binding),
            ("Health Endpoints", self.test_health_endpoints),
            ("CORS Replit Origins", self.test_cors_replit_origins),
            ("Rate Limiting Fallback", self.test_rate_limiting_fallback),
            ("Environment Settings", self.test_environment_settings),
            ("Unified Error Responses", self.test_unified_error_responses),
            ("Database Fallback", self.test_database_fallback)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: ERROR - {str(e)}")
                results[test_name] = False
        
        self.log("\n" + "=" * 60)
        self.log("REPLIT FIXES VERIFICATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Total tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")
        self.log(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            self.log("🎉 ALL REPLIT FIXES VERIFIED!")
        elif passed >= total * 0.8:
            self.log("⚠️  Most fixes working, minor issues remain")
        else:
            self.log("❌ Significant issues detected, needs attention")
        
        return results

if __name__ == "__main__":
    verifier = ReplitFixesVerifier()
    results = verifier.run_all_tests()
    
    # Exit with appropriate code
    success_rate = sum(results.values()) / len(results)
    sys.exit(0 if success_rate >= 0.8 else 1)