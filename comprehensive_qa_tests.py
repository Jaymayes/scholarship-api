#!/usr/bin/env python3
"""
Comprehensive QA Testing Suite
Runtime verification of identified issues without modifying code
"""

import json
import time

import requests


class QARuntimeVerification:
    """Runtime verification of QA findings"""

    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []

    def verify_issue_qa_001_middleware_order(self):
        """Verify QA-001: Security middleware positioning"""
        try:
            # Test if security headers are present
            response = requests.get(f"{self.base_url}/healthz", timeout=5)

            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block"
            }

            missing_headers = []
            for header, expected in security_headers.items():
                if header not in response.headers:
                    missing_headers.append(header)
                elif isinstance(expected, list):
                    if response.headers[header] not in expected:
                        missing_headers.append(f"{header} (wrong value)")
                elif response.headers[header] != expected:
                    missing_headers.append(f"{header} (wrong value)")

            self.test_results.append({
                "issue_id": "QA-001",
                "test": "Security headers presence",
                "status": "PASS" if not missing_headers else "FAIL",
                "details": f"Missing/incorrect headers: {missing_headers}" if missing_headers else "All security headers present"
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "QA-001",
                "test": "Security headers presence",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def verify_issue_qa_004_authentication(self):
        """Verify QA-004: Authentication on scholarships endpoints"""
        try:
            # Test without authentication
            response = requests.get(f"{self.base_url}/api/v1/scholarships", timeout=5)

            if response.status_code == 401:
                status = "CONFIRMED"
                details = "Authentication properly required (401 Unauthorized)"
            elif response.status_code == 200:
                status = "ISSUE_CONFIRMED"
                details = "Endpoint accessible without authentication"
            else:
                status = "UNEXPECTED"
                details = f"Unexpected status code: {response.status_code}"

            self.test_results.append({
                "issue_id": "QA-004",
                "test": "Scholarships endpoint authentication",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "QA-004",
                "test": "Scholarships endpoint authentication",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def verify_issue_qa_005_search_authentication(self):
        """Verify QA-005: Authentication on search endpoints"""
        try:
            # Test search endpoint without authentication
            response = requests.get(f"{self.base_url}/search", timeout=5)

            if response.status_code == 401:
                status = "CONFIRMED"
                details = "Authentication properly required (401 Unauthorized)"
            elif response.status_code in [200, 422]:  # 422 for missing params is acceptable
                status = "ISSUE_CONFIRMED"
                details = f"Endpoint accessible without authentication (HTTP {response.status_code})"
            else:
                status = "UNEXPECTED"
                details = f"Unexpected status code: {response.status_code}"

            self.test_results.append({
                "issue_id": "QA-005",
                "test": "Search endpoint authentication",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "QA-005",
                "test": "Search endpoint authentication",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def verify_docs_exposure(self):
        """Additional test: Check if API docs are exposed"""
        try:
            docs_endpoints = ["/docs", "/redoc", "/openapi.json"]
            exposed_docs = []

            for endpoint in docs_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    exposed_docs.append(endpoint)

            if exposed_docs:
                status = "WARNING"
                details = f"API documentation exposed: {exposed_docs}"
            else:
                status = "PASS"
                details = "API documentation properly protected"

            self.test_results.append({
                "issue_id": "ADDITIONAL-001",
                "test": "API documentation exposure",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "ADDITIONAL-001",
                "test": "API documentation exposure",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def test_input_validation(self):
        """Test input validation robustness"""
        try:
            # Test with invalid JSON
            response = requests.post(
                f"{self.base_url}/eligibility/check",
                data='{"invalid": json}',
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 422:
                try:
                    error_data = response.json()
                    if "VALIDATION_ERROR" in error_data.get("code", ""):
                        status = "PASS"
                        details = "Input validation working correctly"
                    else:
                        status = "PARTIAL"
                        details = "Validation works but error format could be improved"
                except:
                    status = "PARTIAL"
                    details = "Validation works but response is not JSON"
            else:
                status = "FAIL"
                details = f"Unexpected response to invalid JSON: {response.status_code}"

            self.test_results.append({
                "issue_id": "QA-003/QA-006",
                "test": "Input validation",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "QA-003/QA-006",
                "test": "Input validation",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def test_error_handling(self):
        """Test error handling and response format"""
        try:
            # Test 404 handling
            response = requests.get(f"{self.base_url}/nonexistent-endpoint", timeout=5)

            if response.status_code == 404:
                try:
                    error_data = response.json()
                    required_fields = ["trace_id", "code", "message", "status", "timestamp"]
                    missing_fields = [f for f in required_fields if f not in error_data]

                    if not missing_fields:
                        status = "PASS"
                        details = "Unified error format implemented correctly"
                    else:
                        status = "PARTIAL"
                        details = f"Error format missing fields: {missing_fields}"
                except:
                    status = "FAIL"
                    details = "404 response is not JSON formatted"
            else:
                status = "UNEXPECTED"
                details = f"Expected 404, got {response.status_code}"

            self.test_results.append({
                "issue_id": "ERROR-HANDLING",
                "test": "Unified error format",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "ERROR-HANDLING",
                "test": "Unified error format",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        try:
            # Make rapid requests to trigger rate limiting
            responses = []
            for _i in range(15):
                response = requests.get(f"{self.base_url}/healthz", timeout=2)
                responses.append(response.status_code)
                if response.status_code == 429:
                    break
                time.sleep(0.1)

            if 429 in responses:
                status = "PASS"
                details = "Rate limiting is active"
            else:
                status = "INFO"
                details = "Rate limiting not triggered (may be configured for higher limits)"

            self.test_results.append({
                "issue_id": "RATE-LIMITING",
                "test": "Rate limiting functionality",
                "status": status,
                "details": details
            })

        except Exception as e:
            self.test_results.append({
                "issue_id": "RATE-LIMITING",
                "test": "Rate limiting functionality",
                "status": "ERROR",
                "details": f"Test failed: {str(e)}"
            })

    def run_all_tests(self):
        """Run all runtime verification tests"""
        print("🧪 Running QA Runtime Verification Tests...")
        print("=" * 60)

        # Check if service is available
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            if response.status_code != 200:
                print(f"❌ Service not available at {self.base_url}")
                return False
        except:
            print(f"❌ Cannot connect to service at {self.base_url}")
            return False

        print("✅ Service is available, running tests...\n")

        # Run all verification tests
        self.verify_issue_qa_001_middleware_order()
        self.verify_issue_qa_004_authentication()
        self.verify_issue_qa_005_search_authentication()
        self.verify_docs_exposure()
        self.test_input_validation()
        self.test_error_handling()
        self.test_rate_limiting()

        # Generate report
        print("📊 RUNTIME VERIFICATION RESULTS:")
        print("-" * 60)

        status_counts = {"PASS": 0, "FAIL": 0, "WARNING": 0, "ERROR": 0, "INFO": 0, "CONFIRMED": 0, "ISSUE_CONFIRMED": 0, "PARTIAL": 0, "UNEXPECTED": 0}

        for result in self.test_results:
            status = result["status"]
            status_counts[status] += 1

            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARNING": "⚠️",
                "ERROR": "💥",
                "INFO": "ℹ️",
                "CONFIRMED": "✅",
                "ISSUE_CONFIRMED": "🔍",
                "PARTIAL": "🔄",
                "UNEXPECTED": "❓"
            }.get(status, "❓")

            print(f"{status_icon} {result['issue_id']}: {result['test']}")
            print(f"   Status: {status}")
            print(f"   Details: {result['details']}\n")

        print("📈 SUMMARY:")
        for status, count in status_counts.items():
            if count > 0:
                print(f"  {status}: {count}")

        # Save results
        with open("qa_runtime_verification.json", "w") as f:
            json.dump({
                "timestamp": time.time(),
                "base_url": self.base_url,
                "results": self.test_results,
                "summary": status_counts
            }, f, indent=2)

        print("\n📄 Results saved to: qa_runtime_verification.json")

        return True

def main():
    """Run runtime verification"""
    verifier = QARuntimeVerification()
    success = verifier.run_all_tests()

    if success:
        print("\n✅ Runtime verification completed successfully")
        return 0
    print("\n❌ Runtime verification failed")
    return 1

if __name__ == "__main__":
    exit(main())
