#!/usr/bin/env python3
"""
Comprehensive QA Test Suite - Senior QA Engineer Analysis
DO NOT MODIFY EXISTING CODE - IDENTIFICATION AND REPORTING ONLY
"""

import pytest
import requests
import json
import time
import asyncio
import sys
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

class QATestSuite:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.admin_token = None
        self.test_results = []
        self.issues_found = []
        
    def log_issue(self, issue_id: str, location: str, description: str, 
                  steps_to_reproduce: str, observed_output: str, 
                  expected_output: str, severity: str):
        """Log a discovered issue"""
        issue = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"[{severity}] Issue {issue_id}: {description}")
    
    def authenticate_admin(self):
        """Get admin token for authenticated tests"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                self.admin_token = response.json().get("access_token")
                return True
            else:
                self.log_issue(
                    "AUTH-001", "routers/auth.py", 
                    "Admin authentication failed during test setup",
                    "POST /api/v1/auth/login with admin credentials",
                    f"Status: {response.status_code}, Response: {response.text}",
                    "Status: 200 with valid access_token",
                    "Critical"
                )
                return False
        except Exception as e:
            self.log_issue(
                "AUTH-002", "routers/auth.py",
                f"Authentication endpoint connection failed: {str(e)}",
                "POST /api/v1/auth/login",
                f"Exception: {str(e)}",
                "Successful connection and response",
                "Critical"
            )
            return False
    
    def test_authentication_vulnerabilities(self):
        """Test authentication and authorization vulnerabilities"""
        print("\n=== Testing Authentication & Authorization ===")
        
        # Test 1: Access protected endpoints without token
        protected_endpoints = [
            "/api/v1/scholarships",
            "/api/v1/analytics/summary",
            "/api/v1/analytics/user/test123"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code != 401:
                    self.log_issue(
                        f"AUTH-{len(self.issues_found)+100}", 
                        f"routers/{endpoint.split('/')[3] if len(endpoint.split('/')) > 3 else 'unknown'}.py",
                        f"Protected endpoint accessible without authentication",
                        f"GET {endpoint} without Authorization header",
                        f"Status: {response.status_code}, Response: {response.text[:200]}",
                        "Status: 401 Unauthorized",
                        "High"
                    )
            except Exception as e:
                self.log_issue(
                    f"AUTH-{len(self.issues_found)+100}",
                    f"routers/{endpoint.split('/')[3] if len(endpoint.split('/')) > 3 else 'unknown'}.py",
                    f"Endpoint connection failed: {str(e)}",
                    f"GET {endpoint}",
                    f"Exception: {str(e)}",
                    "401 Unauthorized or valid response",
                    "Medium"
                )
        
        # Test 2: Invalid token formats
        invalid_tokens = [
            "invalid_token",
            "Bearer",
            "Bearer ",
            "Bearer invalid.jwt.token",
            "Bearer " + "a" * 1000,  # Very long token
        ]
        
        for token in invalid_tokens:
            try:
                headers = {"Authorization": token}
                response = requests.get(f"{self.base_url}/api/v1/scholarships", headers=headers)
                if response.status_code not in [401, 403]:
                    self.log_issue(
                        f"AUTH-{len(self.issues_found)+200}",
                        "middleware/auth.py",
                        "Invalid token format not properly rejected",
                        f"GET /api/v1/scholarships with Authorization: {token[:50]}...",
                        f"Status: {response.status_code}",
                        "Status: 401 or 403",
                        "Medium"
                    )
            except Exception as e:
                pass  # Connection errors are acceptable for invalid tokens
    
    def test_input_validation_vulnerabilities(self):
        """Test input validation and injection vulnerabilities"""
        print("\n=== Testing Input Validation ===")
        
        # Test 3: SQL Injection attempts
        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        for payload in sql_payloads:
            try:
                response = requests.get(f"{self.base_url}/search", params={"q": payload})
                # Check if response contains SQL error messages or unexpected data
                if any(keyword in response.text.lower() for keyword in ['error', 'sql', 'syntax', 'table', 'column']):
                    self.log_issue(
                        f"SQL-{len(self.issues_found)+300}",
                        "services/scholarship_service.py",
                        "Potential SQL injection vulnerability detected",
                        f"GET /search?q={payload}",
                        f"Response contains SQL-related keywords: {response.text[:200]}",
                        "Sanitized response without SQL error exposure",
                        "High"
                    )
            except Exception as e:
                pass
        
        # Test 4: XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert('xss')</script>",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.get(f"{self.base_url}/search", params={"q": payload})
                if payload in response.text and 'text/html' in response.headers.get('content-type', ''):
                    self.log_issue(
                        f"XSS-{len(self.issues_found)+400}",
                        "routers/search.py",
                        "Potential XSS vulnerability - unescaped user input in response",
                        f"GET /search?q={payload}",
                        f"Payload reflected in response: {response.text[:200]}",
                        "Properly escaped or sanitized output",
                        "High"
                    )
            except Exception as e:
                pass
        
        # Test 5: Oversized inputs
        large_inputs = [
            "a" * 10000,  # Very long string
            "🚀" * 5000,  # Unicode characters
            json.dumps({"key" + str(i): "value" for i in range(1000)}),  # Large JSON
        ]
        
        for large_input in large_inputs:
            try:
                response = requests.get(f"{self.base_url}/search", params={"q": large_input})
                if response.status_code == 500:
                    self.log_issue(
                        f"INPUT-{len(self.issues_found)+500}",
                        "middleware/body_limit.py or routers/search.py",
                        "Server error on large input - possible DoS vulnerability",
                        f"GET /search with {len(large_input)} character input",
                        f"Status: 500, Response: {response.text[:200]}",
                        "Graceful handling with 400 or 413 status",
                        "Medium"
                    )
            except Exception as e:
                pass
    
    def test_rate_limiting_vulnerabilities(self):
        """Test rate limiting effectiveness"""
        print("\n=== Testing Rate Limiting ===")
        
        # Test 6: Rate limit bypass attempts
        endpoints_to_test = [
            "/search",
            "/eligibility/check?gpa=3.5",
            "/db/status"
        ]
        
        for endpoint in endpoints_to_test:
            rapid_requests = 0
            successful_requests = 0
            
            start_time = time.time()
            for i in range(100):  # Send 100 requests rapidly
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=1)
                    rapid_requests += 1
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:
                        break  # Rate limit triggered
                except:
                    break
            
            duration = time.time() - start_time
            
            # If all requests succeeded, rate limiting might not be working
            if successful_requests > 60 and duration < 10:  # More than 60 requests/10 seconds
                self.log_issue(
                    f"RATE-{len(self.issues_found)+600}",
                    "middleware/rate_limiting.py",
                    f"Rate limiting not effective on {endpoint}",
                    f"Send 100 rapid requests to {endpoint}",
                    f"{successful_requests} successful requests in {duration:.2f} seconds",
                    "Rate limiting should trigger after configured limit",
                    "High"
                )
    
    def test_api_endpoint_errors(self):
        """Test API endpoints for errors and unexpected behavior"""
        print("\n=== Testing API Endpoints ===")
        
        # Test 7: Invalid HTTP methods
        endpoints = ["/search", "/eligibility/check", "/db/status"]
        invalid_methods = ["PUT", "DELETE", "PATCH"]
        
        for endpoint in endpoints:
            for method in invalid_methods:
                try:
                    response = requests.request(method, f"{self.base_url}{endpoint}")
                    if response.status_code not in [405, 404]:
                        self.log_issue(
                            f"HTTP-{len(self.issues_found)+700}",
                            f"routers/{endpoint.split('/')[1] if '/' in endpoint else 'main'}.py",
                            f"Unexpected response to invalid HTTP method",
                            f"{method} {endpoint}",
                            f"Status: {response.status_code}",
                            "Status: 405 Method Not Allowed",
                            "Low"
                        )
                except Exception as e:
                    pass
        
        # Test 8: Malformed JSON in POST requests
        malformed_json_tests = [
            '{"invalid": json}',
            '{"unclosed": "string}',
            '{invalid_key: "value"}',
            '{"nested": {"unclosed": }',
            '[]'  # Array instead of object
        ]
        
        for malformed_json in malformed_json_tests:
            try:
                response = requests.post(
                    f"{self.base_url}/eligibility/check",
                    data=malformed_json,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 500:
                    self.log_issue(
                        f"JSON-{len(self.issues_found)+800}",
                        "routers/eligibility.py",
                        "Server error on malformed JSON - improper error handling",
                        f"POST /eligibility/check with malformed JSON: {malformed_json}",
                        f"Status: 500, Response: {response.text[:200]}",
                        "Status: 400 Bad Request with proper error message",
                        "Medium"
                    )
            except Exception as e:
                pass
    
    def test_data_validation_errors(self):
        """Test data validation and edge cases"""
        print("\n=== Testing Data Validation ===")
        
        # Test 9: Boundary value testing for GPA
        invalid_gpa_values = [-1, 5.0, 999, -999, "invalid", None]
        
        for gpa in invalid_gpa_values:
            try:
                response = requests.get(f"{self.base_url}/eligibility/check", params={"gpa": gpa})
                if response.status_code not in [400, 422]:
                    self.log_issue(
                        f"VAL-{len(self.issues_found)+900}",
                        "schemas/eligibility.py or routers/eligibility.py",
                        f"Invalid GPA value not properly validated: {gpa}",
                        f"GET /eligibility/check?gpa={gpa}",
                        f"Status: {response.status_code}, Response: {response.text[:200]}",
                        "Status: 400 or 422 with validation error",
                        "Medium"
                    )
            except Exception as e:
                pass
        
        # Test 10: Date validation for deadlines
        invalid_dates = [
            "invalid-date",
            "2023-13-45",  # Invalid month/day
            "not-a-date",
            "2023/12/31",  # Wrong format
            "12-31-2023"   # Wrong format
        ]
        
        for date in invalid_dates:
            try:
                response = requests.get(f"{self.base_url}/search", params={"deadline_after": date})
                if response.status_code not in [400, 422]:
                    self.log_issue(
                        f"DATE-{len(self.issues_found)+1000}",
                        "routers/search.py",
                        f"Invalid date format not properly validated: {date}",
                        f"GET /search?deadline_after={date}",
                        f"Status: {response.status_code}",
                        "Status: 400 or 422 with validation error",
                        "Medium"
                    )
            except Exception as e:
                pass
    
    def test_security_headers(self):
        """Test security headers and configurations"""
        print("\n=== Testing Security Headers ===")
        
        # Test 11: Security headers presence
        try:
            response = requests.get(f"{self.base_url}/")
            security_headers = {
                "x-content-type-options": "nosniff",
                "x-frame-options": "DENY",
                "x-xss-protection": "1; mode=block",
                "strict-transport-security": "max-age=31536000; includeSubDomains"
            }
            
            for header, expected_value in security_headers.items():
                if header not in response.headers:
                    self.log_issue(
                        f"SEC-{len(self.issues_found)+1100}",
                        "middleware/security_headers.py",
                        f"Missing security header: {header}",
                        "GET / and check response headers",
                        f"Header {header} not present",
                        f"Header {header}: {expected_value}",
                        "Medium"
                    )
        except Exception as e:
            self.log_issue(
                "SEC-1199", "main.py",
                f"Unable to test security headers: {str(e)}",
                "GET / and check response headers",
                f"Exception: {str(e)}",
                "Successful response with security headers",
                "Medium"
            )
    
    def test_database_connections(self):
        """Test database connection and error handling"""
        print("\n=== Testing Database Connections ===")
        
        # Test 12: Database status endpoint
        try:
            response = requests.get(f"{self.base_url}/db/status")
            if response.status_code != 200:
                self.log_issue(
                    "DB-001",
                    "routers/db_status.py",
                    "Database status endpoint not responding correctly",
                    "GET /db/status",
                    f"Status: {response.status_code}, Response: {response.text}",
                    "Status: 200 with database status information",
                    "High"
                )
            else:
                # Check if response contains expected fields
                try:
                    data = response.json()
                    required_fields = ["status", "database", "environment"]
                    for field in required_fields:
                        if field not in data:
                            self.log_issue(
                                f"DB-{len(self.issues_found)+1200}",
                                "routers/db_status.py",
                                f"Database status missing required field: {field}",
                                "GET /db/status and check response structure",
                                f"Response: {json.dumps(data, indent=2)}",
                                f"Response should include '{field}' field",
                                "Medium"
                            )
                except json.JSONDecodeError:
                    self.log_issue(
                        "DB-1299",
                        "routers/db_status.py",
                        "Database status response is not valid JSON",
                        "GET /db/status",
                        f"Response: {response.text}",
                        "Valid JSON response",
                        "Medium"
                    )
        except Exception as e:
            self.log_issue(
                "DB-1298",
                "routers/db_status.py",
                f"Database status endpoint connection failed: {str(e)}",
                "GET /db/status",
                f"Exception: {str(e)}",
                "Successful response",
                "High"
            )
    
    def run_comprehensive_tests(self):
        """Run all test suites"""
        print("Starting Comprehensive QA Analysis...")
        print("=" * 50)
        
        # Authenticate first
        auth_success = self.authenticate_admin()
        
        # Run all test suites
        self.test_authentication_vulnerabilities()
        self.test_input_validation_vulnerabilities() 
        self.test_rate_limiting_vulnerabilities()
        self.test_api_endpoint_errors()
        self.test_data_validation_errors()
        self.test_security_headers()
        self.test_database_connections()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        report = {
            "qa_analysis_summary": {
                "total_issues_found": len(self.issues_found),
                "severity_breakdown": {
                    "Critical": len([i for i in self.issues_found if i["severity"] == "Critical"]),
                    "High": len([i for i in self.issues_found if i["severity"] == "High"]),
                    "Medium": len([i for i in self.issues_found if i["severity"] == "Medium"]),
                    "Low": len([i for i in self.issues_found if i["severity"] == "Low"])
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "test_environment": "Local Development (localhost:5000)"
            },
            "detailed_findings": self.issues_found
        }
        
        return report

if __name__ == "__main__":
    qa_suite = QATestSuite()
    report = qa_suite.run_comprehensive_tests()
    
    # Save report to file
    with open("comprehensive_qa_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*50}")
    print("QA ANALYSIS COMPLETE")
    print(f"{'='*50}")
    print(f"Total Issues Found: {report['qa_analysis_summary']['total_issues_found']}")
    print(f"Critical: {report['qa_analysis_summary']['severity_breakdown']['Critical']}")
    print(f"High: {report['qa_analysis_summary']['severity_breakdown']['High']}")
    print(f"Medium: {report['qa_analysis_summary']['severity_breakdown']['Medium']}")
    print(f"Low: {report['qa_analysis_summary']['severity_breakdown']['Low']}")
    print(f"\nDetailed report saved to: comprehensive_qa_report.json")