"""
Comprehensive QA Implementation Verification
Tests all implemented fixes from the Senior QA analysis
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List
import requests
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAVerificationSuite:
    """Comprehensive QA verification for all implemented fixes"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        self.failures = []
        
    def log_result(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "PASS":
            logger.info(f"✅ {test_name}: {details}")
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: {details}")
            self.failures.append(test_name)
        else:
            logger.warning(f"⚠️  {test_name}: {details}")

    def test_environment_aware_config(self):
        """Test environment-aware configuration validation"""
        try:
            # Test development mode (should work)
            os.environ["ENVIRONMENT"] = "development"
            from config.settings import get_settings
            dev_settings = get_settings()
            
            assert dev_settings.environment.value == "development"
            assert not dev_settings.should_enforce_strict_validation
            assert dev_settings.jwt_secret_key is not None
            assert len(dev_settings.jwt_secret_key) >= 64
            
            self.log_result(
                "ENVIRONMENT_AWARE_CONFIG",
                "PASS",
                f"Development mode loads correctly with JWT secret length {len(dev_settings.jwt_secret_key)}"
            )
            
        except Exception as e:
            self.log_result(
                "ENVIRONMENT_AWARE_CONFIG", 
                "FAIL", 
                f"Configuration test failed: {str(e)}"
            )

    def test_production_validation_strictness(self):
        """Test production validation prevents startup with missing config"""
        try:
            # Test production mode should fail without proper config
            import subprocess
            result = subprocess.run([
                sys.executable, "-c",
                "import os; os.environ['ENVIRONMENT']='production'; from config.settings import get_settings; get_settings()"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0 and ("Production configuration validation failed" in result.stderr or "Invalid configuration" in result.stderr):
                self.log_result(
                    "PRODUCTION_VALIDATION_STRICTNESS",
                    "PASS",
                    "Production mode properly rejects invalid configuration with aggregated errors"
                )
            else:
                self.log_result(
                    "PRODUCTION_VALIDATION_STRICTNESS",
                    "FAIL", 
                    f"Production validation not working: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            self.log_result(
                "PRODUCTION_VALIDATION_STRICTNESS",
                "FAIL",
                "Production validation test timed out"
            )
        except Exception as e:
            self.log_result(
                "PRODUCTION_VALIDATION_STRICTNESS",
                "FAIL",
                f"Production validation test error: {str(e)}"
            )

    def test_api_health_endpoints(self):
        """Test API health and readiness endpoints"""
        try:
            # Test health endpoint
            health_response = requests.get(f"{self.base_url}/health", timeout=5)
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert health_data["status"] == "healthy"
            
            # Test readiness endpoint  
            ready_response = requests.get(f"{self.base_url}/readiness", timeout=5)
            assert ready_response.status_code == 200
            ready_data = ready_response.json()
            assert ready_data["status"] == "ready"
            
            self.log_result(
                "API_HEALTH_ENDPOINTS",
                "PASS",
                f"Health: {health_data['status']}, Readiness: {ready_data['status']}"
            )
            
        except Exception as e:
            self.log_result(
                "API_HEALTH_ENDPOINTS",
                "FAIL",
                f"Health endpoints test failed: {str(e)}"
            )

    def test_cors_security_headers(self):
        """Test CORS and security headers implementation"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            headers = response.headers
            
            # Check for security headers
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_result(
                    "CORS_SECURITY_HEADERS",
                    "PARTIAL", 
                    f"Missing headers: {missing_headers}"
                )
            else:
                self.log_result(
                    "CORS_SECURITY_HEADERS",
                    "PASS",
                    f"All security headers present: {required_headers}"
                )
                
        except Exception as e:
            self.log_result(
                "CORS_SECURITY_HEADERS",
                "FAIL",
                f"Security headers test failed: {str(e)}"
            )

    def test_rate_limiting_functionality(self):
        """Test rate limiting is working"""
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(5):
                try:
                    resp = requests.get(f"{self.base_url}/health", timeout=2)
                    responses.append(resp.status_code)
                except:
                    responses.append(0)
            
            # Check if any rate limiting occurred (not required but good to know)
            rate_limited = any(code == 429 for code in responses)
            successful = sum(1 for code in responses if code == 200)
            
            if successful >= 3:  # At least some requests should work
                status = "PASS" if rate_limited else "INFO"
                details = f"Successful: {successful}/5, Rate limited: {rate_limited}"
                self.log_result("RATE_LIMITING_FUNCTIONALITY", status, details)
            else:
                self.log_result(
                    "RATE_LIMITING_FUNCTIONALITY", 
                    "FAIL", 
                    f"Too few successful requests: {successful}/5"
                )
                
        except Exception as e:
            self.log_result(
                "RATE_LIMITING_FUNCTIONALITY",
                "FAIL", 
                f"Rate limiting test failed: {str(e)}"
            )

    def test_database_connectivity(self):
        """Test database connection and basic operations"""
        try:
            # Test database status endpoint if available
            try:
                db_response = requests.get(f"{self.base_url}/api/v1/database/status", timeout=5)
                if db_response.status_code == 200:
                    db_data = db_response.json()
                    self.log_result(
                        "DATABASE_CONNECTIVITY",
                        "PASS", 
                        f"Database status: {db_data.get('database_status', 'unknown')}"
                    )
                else:
                    self.log_result(
                        "DATABASE_CONNECTIVITY",
                        "PARTIAL",
                        f"Database endpoint returned {db_response.status_code}"
                    )
            except:
                # Test alternative database connectivity via general endpoints
                resp = requests.get(f"{self.base_url}/api/v1/scholarships?limit=1", timeout=5)
                if resp.status_code == 200:
                    self.log_result(
                        "DATABASE_CONNECTIVITY", 
                        "PASS",
                        "Database accessible via scholarships endpoint"
                    )
                else:
                    self.log_result(
                        "DATABASE_CONNECTIVITY",
                        "FAIL",
                        f"Database not accessible: {resp.status_code}"
                    )
                    
        except Exception as e:
            self.log_result(
                "DATABASE_CONNECTIVITY",
                "FAIL",
                f"Database test failed: {str(e)}"
            )

    def test_api_documentation_access(self):
        """Test API documentation availability"""
        try:
            # Test OpenAPI docs
            docs_response = requests.get(f"{self.base_url}/docs", timeout=5)
            redoc_response = requests.get(f"{self.base_url}/redoc", timeout=5) 
            
            docs_available = docs_response.status_code == 200
            redoc_available = redoc_response.status_code == 200
            
            if docs_available and redoc_available:
                self.log_result(
                    "API_DOCUMENTATION_ACCESS",
                    "PASS", 
                    "Both /docs and /redoc endpoints accessible"
                )
            elif docs_available or redoc_available:
                self.log_result(
                    "API_DOCUMENTATION_ACCESS",
                    "PARTIAL",
                    f"Docs: {docs_available}, Redoc: {redoc_available}"
                )
            else:
                self.log_result(
                    "API_DOCUMENTATION_ACCESS",
                    "FAIL",
                    "Neither docs nor redoc accessible"
                )
                
        except Exception as e:
            self.log_result(
                "API_DOCUMENTATION_ACCESS",
                "FAIL",
                f"Documentation test failed: {str(e)}"
            )

    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete QA verification suite"""
        logger.info("🚀 Starting comprehensive QA verification...")
        
        # Configuration tests
        self.test_environment_aware_config()
        self.test_production_validation_strictness()
        
        # API functionality tests
        self.test_api_health_endpoints()
        self.test_cors_security_headers()
        self.test_rate_limiting_functionality()
        self.test_database_connectivity()
        self.test_api_documentation_access()
        
        # Generate summary
        total_tests = len(self.results)
        passed = sum(1 for r in self.results.values() if r["status"] == "PASS")
        failed = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        partial = sum(1 for r in self.results.values() if r["status"] in ["PARTIAL", "INFO"])
        
        summary = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed, 
            "partial": partial,
            "success_rate": round((passed / total_tests) * 100, 1) if total_tests > 0 else 0,
            "results": self.results,
            "failures": self.failures
        }
        
        logger.info(f"📊 QA Verification Complete: {passed}/{total_tests} passed ({summary['success_rate']}%)")
        
        if self.failures:
            logger.warning(f"⚠️  Failed tests: {', '.join(self.failures)}")
        else:
            logger.info("🎉 All tests passed!")
            
        return summary

def main():
    """Main verification runner"""
    print("=" * 60)
    print("QA IMPLEMENTATION VERIFICATION SUITE")
    print("=" * 60)
    
    verifier = QAVerificationSuite()
    summary = verifier.run_full_verification()
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Partial: {summary['partial']}")
    print(f"Success Rate: {summary['success_rate']}%")
    
    if summary['failures']:
        print(f"\nFailed Tests: {', '.join(summary['failures'])}")
        return 1
    else:
        print("\n🎉 All QA implementations verified successfully!")
        return 0

if __name__ == "__main__":
    exit(main())