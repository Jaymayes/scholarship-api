#!/usr/bin/env python3
"""
Additional Security and Edge Case Tests
Supplementary QA testing for comprehensive coverage
"""

import json
import os
import sys
import time
from datetime import datetime

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app


class AdditionalSecurityTests:
    """Additional security-focused tests"""

    def __init__(self):
        self.client = TestClient(app)
        self.issues = []

    def log_issue(self, issue_id: str, location: str, description: str,
                  steps_to_reproduce: str, observed_output: str,
                  expected_output: str, severity: str):
        """Log identified issues"""
        issue = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.issues.append(issue)
        print(f"🐛 ISSUE {issue_id}: {description} [{severity}]")

    def test_http_method_vulnerabilities(self):
        """Test for HTTP method vulnerabilities"""
        print("Testing HTTP method vulnerabilities...")

        endpoints = ["/", "/health", "/api", "/search"]
        dangerous_methods = ["PUT", "DELETE", "PATCH", "TRACE", "OPTIONS"]

        for endpoint in endpoints:
            for method in dangerous_methods:
                try:
                    response = self.client.request(method, endpoint)
                    if response.status_code == 200:
                        self.log_issue(
                            f"HTTP-{method}-001",
                            f"Router: {endpoint}",
                            f"Endpoint accepts dangerous HTTP method: {method}",
                            f"1. Send {method} request to {endpoint}\n2. Check response",
                            f"Status: {response.status_code}",
                            "Status: 405 Method Not Allowed",
                            "Medium"
                        )
                except Exception:
                    pass

    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities"""
        print("Testing information disclosure...")

        # Test server headers
        response = self.client.get("/")
        server_header = response.headers.get("server", "").lower()
        if "fastapi" in server_header or "uvicorn" in server_header:
            self.log_issue(
                "INFO-001",
                "main.py",
                "Server header exposes technology stack",
                "1. Send GET request to /\n2. Check Server header",
                f"Server header: {response.headers.get('server', 'None')}",
                "Generic or no server header",
                "Low"
            )

        # Test error responses for version disclosure
        response = self.client.get("/nonexistent")
        if "fastapi" in response.text.lower() or "uvicorn" in response.text.lower():
            self.log_issue(
                "INFO-002",
                "middleware/error_handling.py",
                "Error responses expose technology details",
                "1. Send GET to /nonexistent\n2. Check response body",
                f"Response contains technology info: {response.text[:200]}",
                "Generic error message",
                "Low"
            )

    def test_parameter_pollution(self):
        """Test for HTTP parameter pollution"""
        print("Testing parameter pollution...")

        # Test multiple parameters with same name
        test_cases = [
            "/search?q=test1&q=test2",
            "/api/v1/scholarships?keyword=test1&keyword=test2",
            "/eligibility/check?gpa=3.0&gpa=4.0"
        ]

        for test_case in test_cases:
            try:
                response = self.client.get(test_case)
                if response.status_code == 500:
                    self.log_issue(
                        "PARAM-001",
                        f"Router: {test_case.split('?')[0]}",
                        "Server error on parameter pollution",
                        f"1. Send GET to {test_case}",
                        f"Status: {response.status_code}",
                        "Graceful handling of duplicate parameters",
                        "Medium"
                    )
            except Exception:
                pass

    def test_content_type_vulnerabilities(self):
        """Test content-type related vulnerabilities"""
        print("Testing content-type vulnerabilities...")

        # Test POST endpoints with different content types
        post_endpoints = ["/search", "/eligibility/check"]
        dangerous_content_types = [
            "application/xml",
            "text/xml",
            "application/x-www-form-urlencoded"
        ]

        for endpoint in post_endpoints:
            for content_type in dangerous_content_types:
                try:
                    headers = {"Content-Type": content_type}
                    response = self.client.post(endpoint, data="<xml>test</xml>", headers=headers)
                    if response.status_code == 200:
                        self.log_issue(
                            "CT-001",
                            f"Router: {endpoint}",
                            f"Endpoint accepts dangerous content-type: {content_type}",
                            f"1. Send POST to {endpoint} with Content-Type: {content_type}",
                            f"Status: {response.status_code}",
                            "Only accept expected content types",
                            "Medium"
                        )
                except Exception:
                    pass

    def test_timing_attacks(self):
        """Test for timing attack vulnerabilities"""
        print("Testing timing attacks...")

        # Test authentication timing
        times = []
        for i in range(5):
            start = time.time()
            self.client.get("/api/v1/scholarships",
                                     headers={"Authorization": f"Bearer invalid_token_{i}"})
            end = time.time()
            times.append(end - start)

        # Check for consistent timing (should be similar for all invalid tokens)
        if max(times) - min(times) > 0.5:  # More than 500ms difference
            self.log_issue(
                "TIME-001",
                "middleware/auth.py",
                "Authentication timing varies significantly",
                "1. Send multiple auth requests with invalid tokens\n2. Measure response times",
                f"Time variance: {max(times) - min(times):.3f}s",
                "Consistent timing for all invalid tokens",
                "Low"
            )

    def test_file_upload_vulnerabilities(self):
        """Test for file upload vulnerabilities if any exist"""
        print("Testing file upload vulnerabilities...")

        # Try to upload files to various endpoints
        endpoints = ["/", "/search", "/api/v1/scholarships"]

        for endpoint in endpoints:
            try:
                files = {"file": ("test.txt", "test content", "text/plain")}
                response = self.client.post(endpoint, files=files)
                if response.status_code == 200:
                    self.log_issue(
                        "FILE-001",
                        f"Router: {endpoint}",
                        "Endpoint accepts file uploads unexpectedly",
                        f"1. Send POST with file to {endpoint}",
                        f"Status: {response.status_code}",
                        "File uploads should be rejected",
                        "Medium"
                    )
            except Exception:
                pass

    def run_additional_tests(self):
        """Run all additional security tests"""
        print("🔒 Running Additional Security Tests...")
        print("=" * 50)

        test_methods = [
            self.test_http_method_vulnerabilities,
            self.test_information_disclosure,
            self.test_parameter_pollution,
            self.test_content_type_vulnerabilities,
            self.test_timing_attacks,
            self.test_file_upload_vulnerabilities
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed: {str(e)}")

        print("=" * 50)
        print(f"🏁 Additional Security Testing Complete. Found {len(self.issues)} additional issues.")

        return self.issues

if __name__ == "__main__":
    security_tests = AdditionalSecurityTests()
    additional_issues = security_tests.run_additional_tests()

    # Save additional findings
    with open("additional_security_findings.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "additional_issues": additional_issues
        }, f, indent=2)

    print("📋 Additional security findings saved to additional_security_findings.json")
