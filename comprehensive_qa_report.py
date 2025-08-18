#!/usr/bin/env python3
"""
Comprehensive QA Analysis Report Generator
Senior QA Engineer Analysis - Bug Detection and Vulnerability Assessment
"""

import requests
import json
import time
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os

@dataclass
class QAIssue:
    """Data class for tracking QA issues"""
    issue_id: str
    location: str
    description: str
    steps_to_reproduce: str
    observed_output: str
    expected_output: str
    severity: str  # Low, Medium, High, Critical
    category: str  # Bug, Security, Performance, Logic, etc.

class ComprehensiveQAAnalyzer:
    """Senior QA Engineer - Comprehensive Bug Detection System"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.issues: List[QAIssue] = []
        self.test_results = {}
        self.start_time = datetime.now()
        
    def add_issue(self, issue_id: str, location: str, description: str, 
                  steps: str, observed: str, expected: str, severity: str, category: str = "Bug"):
        """Add a new issue to the report"""
        issue = QAIssue(
            issue_id=issue_id,
            location=location,
            description=description,
            steps_to_reproduce=steps,
            observed_output=observed,
            expected_output=expected,
            severity=severity,
            category=category
        )
        self.issues.append(issue)

    def test_server_availability(self):
        """Test if server is accessible"""
        print("🔍 Testing server availability...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                self.add_issue(
                    "SERV-001",
                    "main.py:95-105",
                    "Root endpoint returns unexpected status code",
                    "1. Send GET request to / \n2. Check status code",
                    f"Status: {response.status_code}",
                    "Status: 200",
                    "High",
                    "Server"
                )
        except requests.exceptions.ConnectionError:
            self.add_issue(
                "SERV-002",
                "main.py or server configuration",
                "Server is not accessible",
                "1. Start server\n2. Send GET request to /",
                "Connection refused",
                "Successful connection",
                "Critical",
                "Server"
            )
            return False
        except Exception as e:
            self.add_issue(
                "SERV-003",
                "main.py",
                f"Unexpected error accessing server: {str(e)}",
                "1. Send GET request to /",
                str(e),
                "Successful response",
                "High",
                "Server"
            )
        return True

    def test_api_documentation(self):
        """Test OpenAPI documentation endpoints"""
        print("📚 Testing API documentation...")
        
        # Test /docs endpoint
        try:
            response = requests.get(f"{self.base_url}/docs")
            if response.status_code != 200:
                self.add_issue(
                    "DOC-001",
                    "FastAPI auto-generated docs",
                    "API documentation endpoint not accessible",
                    "1. Navigate to /docs\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 200 with Swagger UI",
                    "Medium",
                    "Documentation"
                )
        except Exception as e:
            self.add_issue(
                "DOC-002",
                "FastAPI configuration",
                f"Error accessing API docs: {str(e)}",
                "1. Navigate to /docs",
                str(e),
                "Swagger UI loads successfully",
                "Medium",
                "Documentation"
            )

    def test_search_functionality(self):
        """Comprehensive search endpoint testing"""
        print("🔍 Testing search functionality...")
        
        # Test basic search
        try:
            response = requests.get(f"{self.base_url}/search?q=engineering")
            if response.status_code != 200:
                self.add_issue(
                    "SEARCH-001",
                    "routers/search.py",
                    "Basic search query fails",
                    "1. Send GET /search?q=engineering\n2. Check response",
                    f"Status: {response.status_code}, Response: {response.text}",
                    "Status: 200 with search results",
                    "High",
                    "Search"
                )
            else:
                data = response.json()
                if "items" not in data:
                    self.add_issue(
                        "SEARCH-002",
                        "services/search_service.py or routers/search.py",
                        "Search response missing 'items' field",
                        "1. Send GET /search?q=engineering\n2. Check response structure",
                        f"Response keys: {list(data.keys())}",
                        "Response should contain 'items' field",
                        "Medium",
                        "Search"
                    )
        except Exception as e:
            self.add_issue(
                "SEARCH-003",
                "routers/search.py",
                f"Search endpoint throws exception: {str(e)}",
                "1. Send GET /search?q=engineering",
                str(e),
                "Successful search response",
                "High",
                "Search"
            )

        # Test empty search query
        try:
            response = requests.get(f"{self.base_url}/search?q=")
            if response.status_code == 500:
                self.add_issue(
                    "SEARCH-004",
                    "services/search_service.py",
                    "Empty search query causes server error",
                    "1. Send GET /search?q=\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 200 with empty results or 400 with validation error",
                    "Medium",
                    "Input Validation"
                )
        except Exception as e:
            self.add_issue(
                "SEARCH-005",
                "routers/search.py",
                f"Empty search causes exception: {str(e)}",
                "1. Send GET /search?q=",
                str(e),
                "Graceful handling of empty search",
                "Medium",
                "Input Validation"
            )

        # Test malicious input
        malicious_inputs = [
            "'; DROP TABLE scholarships; --",
            "<script>alert('xss')</script>",
            "../../../../etc/passwd",
            "\\x00\\x01\\x02",
            "A" * 10000  # Very long input
        ]
        
        for malicious_input in malicious_inputs:
            try:
                response = requests.get(f"{self.base_url}/search", params={"q": malicious_input})
                if response.status_code == 500:
                    self.add_issue(
                        f"SEARCH-SEC-{hash(malicious_input) % 1000:03d}",
                        "services/search_service.py or routers/search.py",
                        f"Malicious input causes server error: {malicious_input[:50]}...",
                        f"1. Send GET /search?q={malicious_input[:50]}...\n2. Check response",
                        f"Status: {response.status_code}",
                        "Status: 200 with sanitized results or 400 with validation error",
                        "High",
                        "Security"
                    )
            except Exception as e:
                self.add_issue(
                    f"SEARCH-SEC-EXC-{hash(malicious_input) % 1000:03d}",
                    "routers/search.py",
                    f"Malicious input causes exception: {str(e)}",
                    f"1. Send GET /search?q={malicious_input[:50]}...",
                    str(e),
                    "Graceful error handling",
                    "High",
                    "Security"
                )

    def test_eligibility_functionality(self):
        """Test eligibility checking endpoints"""
        print("🎯 Testing eligibility functionality...")
        
        # Test eligibility check without parameters
        try:
            response = requests.get(f"{self.base_url}/eligibility/check")
            if response.status_code != 422:  # Expected validation error
                self.add_issue(
                    "ELIG-001",
                    "routers/eligibility.py",
                    "Eligibility check without required parameters doesn't return validation error",
                    "1. Send GET /eligibility/check\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 422 with validation error",
                    "Medium",
                    "Input Validation"
                )
        except Exception as e:
            self.add_issue(
                "ELIG-002",
                "routers/eligibility.py",
                f"Eligibility endpoint throws exception: {str(e)}",
                "1. Send GET /eligibility/check",
                str(e),
                "Validation error response",
                "Medium",
                "Eligibility"
            )

        # Test POST eligibility with invalid JSON
        try:
            response = requests.post(
                f"{self.base_url}/eligibility/check",
                json={"invalid": "data"}
            )
            if response.status_code == 500:
                self.add_issue(
                    "ELIG-003",
                    "routers/eligibility.py",
                    "Invalid JSON for eligibility check causes server error",
                    "1. Send POST /eligibility/check with invalid JSON\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 422 with validation error",
                    "Medium",
                    "Input Validation"
                )
        except Exception as e:
            self.add_issue(
                "ELIG-004",
                "routers/eligibility.py",
                f"Invalid eligibility JSON causes exception: {str(e)}",
                "1. Send POST /eligibility/check with invalid JSON",
                str(e),
                "Validation error response",
                "Medium",
                "Eligibility"
            )

    def test_ai_functionality(self):
        """Test AI-powered endpoints"""
        print("🤖 Testing AI functionality...")
        
        # Test AI status
        try:
            response = requests.get(f"{self.base_url}/ai/status")
            if response.status_code != 200:
                self.add_issue(
                    "AI-001",
                    "routers/ai.py",
                    "AI status endpoint not accessible",
                    "1. Send GET /ai/status\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 200 with AI service status",
                    "Medium",
                    "AI"
                )
        except Exception as e:
            self.add_issue(
                "AI-002",
                "routers/ai.py",
                f"AI status endpoint throws exception: {str(e)}",
                "1. Send GET /ai/status",
                str(e),
                "AI service status response",
                "Medium",
                "AI"
            )

        # Test AI search enhancement with missing data
        try:
            response = requests.post(f"{self.base_url}/ai/enhance-search", json={})
            if response.status_code == 500:
                self.add_issue(
                    "AI-003",
                    "routers/ai.py",
                    "AI search enhancement with empty JSON causes server error",
                    "1. Send POST /ai/enhance-search with empty JSON\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 422 with validation error",
                    "Medium",
                    "Input Validation"
                )
        except Exception as e:
            self.add_issue(
                "AI-004",
                "routers/ai.py",
                f"AI search enhancement throws exception: {str(e)}",
                "1. Send POST /ai/enhance-search with empty JSON",
                str(e),
                "Validation error response",
                "Medium",
                "AI"
            )

        # Test AI with very long input
        try:
            long_query = "A" * 50000  # Very long query
            response = requests.post(
                f"{self.base_url}/ai/enhance-search",
                json={"query": long_query}
            )
            if response.status_code == 500:
                self.add_issue(
                    "AI-005",
                    "services/openai_service.py",
                    "Very long AI query causes server error",
                    f"1. Send POST /ai/enhance-search with 50k character query\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 400 with length validation error or 200 with truncated processing",
                    "Medium",
                    "Input Validation"
                )
        except Exception as e:
            self.add_issue(
                "AI-006",
                "services/openai_service.py",
                f"Long AI query causes exception: {str(e)}",
                "1. Send POST /ai/enhance-search with very long query",
                str(e),
                "Graceful handling of long input",
                "Medium",
                "AI"
            )

    def test_database_endpoints(self):
        """Test database-related endpoints"""
        print("🗄️ Testing database functionality...")
        
        # Test database status
        try:
            response = requests.get(f"{self.base_url}/db/status")
            if response.status_code != 200:
                self.add_issue(
                    "DB-001",
                    "routers/database.py",
                    "Database status endpoint not accessible",
                    "1. Send GET /db/status\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 200 with database status",
                    "High",
                    "Database"
                )
        except Exception as e:
            self.add_issue(
                "DB-002",
                "routers/database.py",
                f"Database status throws exception: {str(e)}",
                "1. Send GET /db/status",
                str(e),
                "Database status response",
                "High",
                "Database"
            )

        # Test SQL injection attempts
        sql_injections = [
            "1'; DROP TABLE scholarships; --",
            "1' OR '1'='1",
            "'; UNION SELECT * FROM users; --"
        ]
        
        for injection in sql_injections:
            try:
                response = requests.get(f"{self.base_url}/scholarships/{injection}")
                if response.status_code == 500:
                    self.add_issue(
                        f"DB-SQL-{hash(injection) % 1000:03d}",
                        "services/scholarship_service.py or models/",
                        f"SQL injection attempt causes server error: {injection}",
                        f"1. Send GET /scholarships/{injection}\n2. Check response",
                        f"Status: {response.status_code}",
                        "Status: 404 or 400 with safe error handling",
                        "Critical",
                        "Security"
                    )
            except Exception as e:
                self.add_issue(
                    f"DB-SQL-EXC-{hash(injection) % 1000:03d}",
                    "services/scholarship_service.py",
                    f"SQL injection causes exception: {str(e)}",
                    f"1. Send GET /scholarships/{injection}",
                    str(e),
                    "Safe error handling",
                    "Critical",
                    "Security"
                )

    def test_authentication_security(self):
        """Test authentication and security"""
        print("🔐 Testing authentication and security...")
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/api/v1/scholarships",
            "/api/v1/analytics/summary"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.add_issue(
                        f"AUTH-{hash(endpoint) % 1000:03d}",
                        "middleware/auth.py",
                        f"Protected endpoint accessible without authentication: {endpoint}",
                        f"1. Send GET {endpoint} without Authorization header\n2. Check response",
                        f"Status: {response.status_code} (accessible)",
                        "Status: 401 Unauthorized",
                        "Critical",
                        "Security"
                    )
            except Exception as e:
                self.add_issue(
                    f"AUTH-EXC-{hash(endpoint) % 1000:03d}",
                    "middleware/auth.py",
                    f"Authentication check throws exception: {str(e)}",
                    f"1. Send GET {endpoint} without auth",
                    str(e),
                    "401 Unauthorized response",
                    "High",
                    "Security"
                )

        # Test with invalid JWT token
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(f"{self.base_url}/api/v1/scholarships", headers=headers)
            if response.status_code == 500:
                self.add_issue(
                    "AUTH-002",
                    "middleware/auth.py",
                    "Invalid JWT token causes server error",
                    "1. Send request with Authorization: Bearer invalid_token_here\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 401 with token validation error",
                    "High",
                    "Security"
                )
        except Exception as e:
            self.add_issue(
                "AUTH-003",
                "middleware/auth.py",
                f"Invalid JWT token causes exception: {str(e)}",
                "1. Send request with invalid JWT token",
                str(e),
                "401 Unauthorized response",
                "High",
                "Security"
            )

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("⏱️ Testing rate limiting...")
        
        # Test rate limiting by making rapid requests
        try:
            responses = []
            for i in range(50):  # Make 50 rapid requests
                response = requests.get(f"{self.base_url}/search?q=test{i}")
                responses.append(response.status_code)
                if response.status_code == 429:
                    break
            
            # Check if rate limiting kicked in
            if 429 not in responses:
                self.add_issue(
                    "RATE-001",
                    "middleware/rate_limiting.py",
                    "Rate limiting not functioning - no 429 status after 50 rapid requests",
                    "1. Make 50 rapid GET requests to /search\n2. Check for 429 status",
                    f"All responses: {set(responses)}",
                    "At least one 429 Too Many Requests response",
                    "Medium",
                    "Security"
                )
        except Exception as e:
            self.add_issue(
                "RATE-002",
                "middleware/rate_limiting.py",
                f"Rate limiting test causes exception: {str(e)}",
                "1. Make rapid requests to test rate limiting",
                str(e),
                "Rate limiting responses",
                "Medium",
                "Rate Limiting"
            )

    def test_error_handling(self):
        """Test error handling across endpoints"""
        print("⚠️ Testing error handling...")
        
        # Test 404 handling
        try:
            response = requests.get(f"{self.base_url}/nonexistent-endpoint")
            if response.status_code != 404:
                self.add_issue(
                    "ERR-001",
                    "middleware/error_handlers.py",
                    "Non-existent endpoint doesn't return 404",
                    "1. Send GET /nonexistent-endpoint\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 404",
                    "Low",
                    "Error Handling"
                )
            
            # Check if error response has proper structure
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    required_fields = ["message", "status", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in error_data]
                    if missing_fields:
                        self.add_issue(
                            "ERR-002",
                            "middleware/error_handlers.py",
                            f"404 error response missing required fields: {missing_fields}",
                            "1. Send GET /nonexistent-endpoint\n2. Check error response structure",
                            f"Response fields: {list(error_data.keys())}",
                            f"Should include: {required_fields}",
                            "Low",
                            "Error Handling"
                        )
                except ValueError:
                    self.add_issue(
                        "ERR-003",
                        "middleware/error_handlers.py",
                        "404 error response is not valid JSON",
                        "1. Send GET /nonexistent-endpoint\n2. Parse JSON response",
                        "Non-JSON response",
                        "Valid JSON error response",
                        "Medium",
                        "Error Handling"
                    )
        except Exception as e:
            self.add_issue(
                "ERR-004",
                "middleware/error_handlers.py",
                f"Error handling test causes exception: {str(e)}",
                "1. Send GET /nonexistent-endpoint",
                str(e),
                "404 error response",
                "Medium",
                "Error Handling"
            )

    def test_input_validation(self):
        """Test input validation across endpoints"""
        print("✅ Testing input validation...")
        
        # Test various invalid inputs
        invalid_inputs = [
            {"endpoint": "/search", "params": {"limit": -1}, "expected_issue": "Negative limit accepted"},
            {"endpoint": "/search", "params": {"limit": "invalid"}, "expected_issue": "Non-numeric limit accepted"},
            {"endpoint": "/search", "params": {"offset": -1}, "expected_issue": "Negative offset accepted"},
            {"endpoint": "/scholarships/", "params": {}, "expected_issue": "Empty scholarship ID accepted"}
        ]
        
        for test_case in invalid_inputs:
            try:
                response = requests.get(f"{self.base_url}{test_case['endpoint']}", params=test_case['params'])
                if response.status_code == 200:
                    self.add_issue(
                        f"VAL-{hash(str(test_case)) % 1000:03d}",
                        "Input validation",
                        test_case['expected_issue'],
                        f"1. Send GET {test_case['endpoint']} with params {test_case['params']}\n2. Check response",
                        f"Status: {response.status_code} (accepted invalid input)",
                        "Status: 422 with validation error",
                        "Medium",
                        "Input Validation"
                    )
            except Exception as e:
                pass  # Expected for some invalid inputs

    def test_performance_edge_cases(self):
        """Test performance and edge cases"""
        print("⚡ Testing performance edge cases...")
        
        # Test very large response handling
        try:
            response = requests.get(f"{self.base_url}/search?limit=10000")
            if response.status_code == 500:
                self.add_issue(
                    "PERF-001",
                    "services/search_service.py",
                    "Very large limit causes server error",
                    "1. Send GET /search?limit=10000\n2. Check response",
                    f"Status: {response.status_code}",
                    "Status: 200 with results or 400 with limit validation",
                    "Medium",
                    "Performance"
                )
        except Exception as e:
            self.add_issue(
                "PERF-002",
                "services/search_service.py",
                f"Large limit causes exception: {str(e)}",
                "1. Send GET /search?limit=10000",
                str(e),
                "Graceful handling of large limits",
                "Medium",
                "Performance"
            )

    def test_cors_security(self):
        """Test CORS configuration"""
        print("🌐 Testing CORS security...")
        
        try:
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET"
            }
            response = requests.options(f"{self.base_url}/search", headers=headers)
            
            # Check CORS headers
            cors_headers = response.headers.get("Access-Control-Allow-Origin", "")
            if cors_headers == "*":
                self.add_issue(
                    "CORS-001",
                    "main.py CORS configuration",
                    "CORS allows all origins (*) which is a security risk",
                    "1. Send OPTIONS request with malicious origin\n2. Check CORS headers",
                    f"Access-Control-Allow-Origin: {cors_headers}",
                    "Specific allowed origins, not wildcard",
                    "High",
                    "Security"
                )
        except Exception as e:
            self.add_issue(
                "CORS-002",
                "CORS configuration",
                f"CORS test causes exception: {str(e)}",
                "1. Send OPTIONS request to test CORS",
                str(e),
                "CORS headers response",
                "Medium",
                "Security"
            )

    def run_comprehensive_analysis(self):
        """Run all QA tests and generate comprehensive report"""
        print("🚀 Starting Comprehensive QA Analysis")
        print("=" * 80)
        
        if not self.test_server_availability():
            print("❌ Server not available - stopping analysis")
            return
        
        # Run all test categories
        test_methods = [
            self.test_api_documentation,
            self.test_search_functionality,
            self.test_eligibility_functionality,
            self.test_ai_functionality,
            self.test_database_endpoints,
            self.test_authentication_security,
            self.test_rate_limiting,
            self.test_error_handling,
            self.test_input_validation,
            self.test_performance_edge_cases,
            self.test_cors_security
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.1)  # Brief pause between tests
            except Exception as e:
                self.add_issue(
                    f"TEST-{hash(test_method.__name__) % 1000:03d}",
                    test_method.__name__,
                    f"Test method failed with exception: {str(e)}",
                    f"1. Run {test_method.__name__}",
                    str(e),
                    "Successful test execution",
                    "High",
                    "Test Framework"
                )
        
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive QA report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Categorize issues by severity
        critical_issues = [i for i in self.issues if i.severity == "Critical"]
        high_issues = [i for i in self.issues if i.severity == "High"]
        medium_issues = [i for i in self.issues if i.severity == "Medium"]
        low_issues = [i for i in self.issues if i.severity == "Low"]
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE QA ANALYSIS REPORT")
        print("=" * 80)
        print(f"Analysis Duration: {duration}")
        print(f"Total Issues Found: {len(self.issues)}")
        print(f"Critical: {len(critical_issues)} | High: {len(high_issues)} | Medium: {len(medium_issues)} | Low: {len(low_issues)}")
        print("\n" + "=" * 80)
        
        # Generate detailed report
        report_data = {
            "analysis_metadata": {
                "timestamp": self.start_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "total_issues": len(self.issues)
            },
            "summary": {
                "critical": len(critical_issues),
                "high": len(high_issues),
                "medium": len(medium_issues),
                "low": len(low_issues)
            },
            "issues": []
        }
        
        # Print and collect detailed issues
        for severity, issues in [("Critical", critical_issues), ("High", high_issues), 
                               ("Medium", medium_issues), ("Low", low_issues)]:
            if issues:
                print(f"\n🚨 {severity.upper()} SEVERITY ISSUES:")
                print("-" * 50)
                
                for issue in issues:
                    print(f"\nIssue ID: {issue.issue_id}")
                    print(f"Location: {issue.location}")
                    print(f"Category: {issue.category}")
                    print(f"Description: {issue.description}")
                    print(f"Steps to Reproduce:\n{issue.steps_to_reproduce}")
                    print(f"Observed Output: {issue.observed_output}")
                    print(f"Expected Output: {issue.expected_output}")
                    print("-" * 30)
                    
                    # Add to JSON report
                    report_data["issues"].append({
                        "issue_id": issue.issue_id,
                        "location": issue.location,
                        "description": issue.description,
                        "steps_to_reproduce": issue.steps_to_reproduce,
                        "observed_output": issue.observed_output,
                        "expected_output": issue.expected_output,
                        "severity": issue.severity,
                        "category": issue.category
                    })
        
        # Save JSON report
        with open("comprehensive_qa_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: comprehensive_qa_report.json")
        print("=" * 80)
        
        return report_data

def main():
    """Run comprehensive QA analysis"""
    analyzer = ComprehensiveQAAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()