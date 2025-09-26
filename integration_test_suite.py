"""
Integration test suite for Scholarship API and Auto Command Center communication
Validates inbound calls, outbound events, and cross-service functionality
"""

import time
import uuid
from datetime import datetime

import requests

# Test configuration
BASE_URL = "http://localhost:5000"
ACC_WEBHOOK_URL = "https://webhook.site/unique-id"  # Replace with actual ACC endpoint
API_KEY = "test-api-key"
WEBHOOK_SECRET = "test-webhook-secret"

class IntegrationTestSuite:
    """Comprehensive integration test suite"""

    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.application_id = None
        self.scholarship_id = None

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append((test_name, success, details))

    def test_1_healthcheck(self):
        """Test 1: Health check endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/healthz")
            success = response.status_code == 200

            if success:
                data = response.json()
                details = f"Status: {data.get('status', 'unknown')}"
            else:
                details = f"HTTP {response.status_code}: {response.text[:100]}"

            self.log_test("Health Check", success, details)
            return success

        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {e}")
            return False

    def test_2_openapi_spec(self):
        """Test 2: OpenAPI specification availability"""
        try:
            response = self.session.get(f"{BASE_URL}/openapi.json")
            success = response.status_code == 200

            if success:
                data = response.json()
                path_count = len(data.get('paths', {}))
                details = f"Found {path_count} API endpoints"
            else:
                details = f"HTTP {response.status_code} (may be disabled)"

            self.log_test("OpenAPI Specification", success, details)
            return success

        except Exception as e:
            self.log_test("OpenAPI Specification", False, f"Exception: {e}")
            return False

    def test_3_list_scholarships(self):
        """Test 3: List scholarships endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/api/v1/scholarships?limit=5")
            success = response.status_code == 200

            if success:
                data = response.json()
                scholarships = data.get('items', data.get('scholarships', []))
                count = len(scholarships)
                details = f"Retrieved {count} scholarships"

                # Store first scholarship ID for later tests
                if scholarships:
                    self.scholarship_id = scholarships[0].get('id')

            else:
                details = f"HTTP {response.status_code}: {response.text[:100]}"

            self.log_test("List Scholarships", success, details)
            return success

        except Exception as e:
            self.log_test("List Scholarships", False, f"Exception: {e}")
            return False

    def test_4_cors_preflight(self):
        """Test 4: CORS preflight check"""
        try:
            headers = {
                'Origin': 'https://auto-com-center-jamarrlmayes.replit.app',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type, Authorization'
            }

            response = self.session.options(f"{BASE_URL}/api/v1/scholarships", headers=headers)
            success = response.status_code in [200, 204]

            if success:
                allow_origin = response.headers.get('Access-Control-Allow-Origin', '')
                details = f"CORS origin: {allow_origin}"
            else:
                details = f"HTTP {response.status_code}: CORS may not be configured"

            self.log_test("CORS Preflight", success, details)
            return success

        except Exception as e:
            self.log_test("CORS Preflight", False, f"Exception: {e}")
            return False

    def test_5_agent_capabilities(self):
        """Test 5: Agent Bridge capabilities"""
        try:
            response = self.session.get(f"{BASE_URL}/agent/capabilities")
            success = response.status_code == 200

            if success:
                data = response.json()
                capabilities = data.get('capabilities', [])
                details = f"Agent capabilities: {len(capabilities)} actions available"
            else:
                details = f"HTTP {response.status_code}: Agent Bridge not available"

            self.log_test("Agent Capabilities", success, details)
            return success

        except Exception as e:
            self.log_test("Agent Capabilities", False, f"Exception: {e}")
            return False

    def test_6_agent_health(self):
        """Test 6: Agent Bridge health check"""
        try:
            response = self.session.get(f"{BASE_URL}/agent/health")
            success = response.status_code == 200

            if success:
                data = response.json()
                agent_status = data.get('status', 'unknown')
                cc_configured = data.get('command_center_configured', False)
                details = f"Agent status: {agent_status}, CC configured: {cc_configured}"
            else:
                details = f"HTTP {response.status_code}: Agent health unavailable"

            self.log_test("Agent Health", success, details)
            return success

        except Exception as e:
            self.log_test("Agent Health", False, f"Exception: {e}")
            return False

    def test_7_search_functionality(self):
        """Test 7: Search functionality"""
        try:
            params = {
                'q': 'engineering',
                'limit': 3,
                'min_amount': 1000
            }

            response = self.session.get(f"{BASE_URL}/api/v1/search", params=params)
            success = response.status_code == 200

            if success:
                data = response.json()
                results = data.get('items', [])
                total = data.get('total', 0)
                details = f"Search returned {len(results)} of {total} results"
            else:
                details = f"HTTP {response.status_code}: {response.text[:100]}"

            self.log_test("Search Functionality", success, details)
            return success

        except Exception as e:
            self.log_test("Search Functionality", False, f"Exception: {e}")
            return False

    def test_8_eligibility_check(self):
        """Test 8: Eligibility checking"""
        try:
            payload = {
                "student_profile": {
                    "gpa": 3.5,
                    "field_of_study": "engineering",
                    "graduation_year": 2025,
                    "citizenship": "US"
                },
                "scholarship_id": self.scholarship_id or "test_scholarship"
            }

            response = self.session.post(f"{BASE_URL}/api/v1/eligibility/check", json=payload)
            success = response.status_code == 200

            if success:
                data = response.json()
                eligible = data.get('eligible', False)
                score = data.get('score', 0)
                details = f"Eligibility: {eligible}, Score: {score}"
            else:
                details = f"HTTP {response.status_code}: {response.text[:100]}"

            self.log_test("Eligibility Check", success, details)
            return success

        except Exception as e:
            self.log_test("Eligibility Check", False, f"Exception: {e}")
            return False

    def test_9_invalid_payload(self):
        """Test 9: Invalid payload handling"""
        try:
            # Send invalid payload to search endpoint
            invalid_payload = {
                "invalid_field": "test",
                "malformed_data": {"nested": {"too": {"deep": "structure"}}}
            }

            response = self.session.post(f"{BASE_URL}/api/v1/search", json=invalid_payload)
            success = response.status_code in [400, 422, 405]  # Expected error codes

            if success:
                data = response.json()
                error_code = data.get('code', 'UNKNOWN')
                details = f"Correctly rejected with error: {error_code}"
            else:
                details = f"Unexpected status {response.status_code}: should reject invalid payload"

            self.log_test("Invalid Payload Handling", success, details)
            return success

        except Exception as e:
            self.log_test("Invalid Payload Handling", False, f"Exception: {e}")
            return False

    def test_10_rate_limiting(self):
        """Test 10: Rate limiting headers and behavior"""
        try:
            response = self.session.get(f"{BASE_URL}/api/v1/search?q=test")
            success = response.status_code == 200

            # Check for rate limiting headers
            rate_headers = [
                'X-RateLimit-Limit',
                'X-RateLimit-Remaining',
                'X-RateLimit-Reset',
                'Retry-After'
            ]

            found_headers = [h for h in rate_headers if h in response.headers]

            if found_headers:
                details = f"Rate limit headers found: {', '.join(found_headers)}"
            else:
                details = "No rate limit headers (may use in-memory fallback)"

            self.log_test("Rate Limiting", success, details)
            return success

        except Exception as e:
            self.log_test("Rate Limiting", False, f"Exception: {e}")
            return False

    def test_11_agent_task_auth(self):
        """Test 11: Agent task authentication (should fail without JWT)"""
        try:
            task = {
                "task_id": str(uuid.uuid4()),
                "action": "scholarship_api.search",
                "payload": {
                    "query": "test search",
                    "filters": {},
                    "pagination": {"page": 1, "size": 5}
                },
                "reply_to": "http://example.com/callback",
                "trace_id": str(uuid.uuid4()),
                "requested_by": "integration_test"
            }

            response = self.session.post(f"{BASE_URL}/agent/task", json=task)
            success = response.status_code == 401  # Should be unauthorized

            if success:
                details = "Correctly rejected unauthorized task request"
            else:
                details = f"Unexpected status {response.status_code}: should require authentication"

            self.log_test("Agent Task Authentication", success, details)
            return success

        except Exception as e:
            self.log_test("Agent Task Authentication", False, f"Exception: {e}")
            return False

    def test_12_performance_check(self):
        """Test 12: Basic performance check"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/api/v1/search?q=engineering&limit=10")
            end_time = time.time()

            response_time = end_time - start_time
            success = response.status_code == 200 and response_time < 5.0  # Under 5 seconds

            if success:
                details = f"Response time: {response_time:.3f}s (acceptable)"
            else:
                details = f"Response time: {response_time:.3f}s (too slow or failed)"

            self.log_test("Performance Check", success, details)
            return success

        except Exception as e:
            self.log_test("Performance Check", False, f"Exception: {e}")
            return False

    def run_all_tests(self):
        """Execute all integration tests"""
        print("🚀 Running Scholarship API Integration Test Suite")
        print("=" * 60)
        print(f"Target API: {BASE_URL}")
        print(f"Test timestamp: {datetime.now().isoformat()}")
        print("=" * 60)

        tests = [
            ("Health Check", self.test_1_healthcheck),
            ("OpenAPI Spec", self.test_2_openapi_spec),
            ("List Scholarships", self.test_3_list_scholarships),
            ("CORS Preflight", self.test_4_cors_preflight),
            ("Agent Capabilities", self.test_5_agent_capabilities),
            ("Agent Health", self.test_6_agent_health),
            ("Search Functionality", self.test_7_search_functionality),
            ("Eligibility Check", self.test_8_eligibility_check),
            ("Invalid Payload", self.test_9_invalid_payload),
            ("Rate Limiting", self.test_10_rate_limiting),
            ("Agent Task Auth", self.test_11_agent_task_auth),
            ("Performance Check", self.test_12_performance_check)
        ]

        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {e}")

            time.sleep(0.5)  # Brief pause between tests

        # Summary
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST RESULTS")
        print("=" * 60)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if details and not success:
                print(f"    └─ {details}")

        print(f"\n📈 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

        if passed == total:
            print("🎉 All integration tests passed! API ready for production.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Review failed tests before deployment.")
        else:
            print("❌ Multiple test failures. Requires investigation.")

        # Recommendations
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)

        if passed < total:
            print("• Review failed tests and fix underlying issues")
            print("• Test with real Command Center environment variables")
            print("• Verify CORS configuration for production origins")

        print("• Configure Command Center integration:")
        print("  - Set COMMAND_CENTER_URL environment variable")
        print("  - Set SHARED_SECRET for JWT authentication")
        print("  - Test with real ACC webhook endpoints")
        print("• Monitor performance under realistic load")
        print("• Set up health check monitoring in production")

        return passed, total


def main():
    """Run integration test suite"""
    suite = IntegrationTestSuite()
    passed, total = suite.run_all_tests()

    # Exit with appropriate code
    exit_code = 0 if passed == total else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
