#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Senior QA Engineer Analysis
Issue Identification Only - NO CODE MODIFICATIONS
"""

import json
import requests
import asyncio
import pytest
import traceback
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi.testclient import TestClient

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules for testing
try:
    from main import app
    from models.scholarship import Scholarship, EligibilityCriteria, SearchFilters, FieldOfStudy, ScholarshipType
    from models.user import UserProfile, EligibilityCheck, RecommendationRequest
    from services.scholarship_service import scholarship_service
    from services.eligibility_service import eligibility_service
    from services.search_service import search_service
    from services.analytics_service import analytics_service
    from data.scholarships import MOCK_SCHOLARSHIPS
    from config.settings import settings
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class ComprehensiveQATestSuite:
    """Senior QA Engineer Test Suite - Comprehensive Issue Detection"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.client = TestClient(app)
        self.issues = []
        self.test_results = []
        
    def log_issue(self, issue_id: str, location: str, description: str, 
                  steps_to_reproduce: str, observed_output: str, 
                  expected_output: str, severity: str):
        """Log identified issues with standardized format"""
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

    # 1. AUTHENTICATION & AUTHORIZATION TESTS
    def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities"""
        print("Testing authentication bypass scenarios...")
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/api/v1/scholarships",
            "/api/v1/analytics/summary",
            "/api/v1/database/status"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.client.get(endpoint)
                if response.status_code == 200:
                    self.log_issue(
                        "AUTH-001",
                        f"Router: {endpoint}",
                        "Protected endpoint accessible without authentication",
                        f"1. Send GET request to {endpoint}\n2. Observe response",
                        f"Status: {response.status_code}, Response: {response.text[:200]}",
                        "Status: 401 Unauthorized",
                        "Critical"
                    )
            except Exception as e:
                self.log_issue(
                    "AUTH-002",
                    f"Router: {endpoint}",
                    f"Authentication test failed with exception: {str(e)}",
                    f"1. Send GET request to {endpoint}",
                    f"Exception: {str(e)}",
                    "Proper authentication handling",
                    "High"
                )

    def test_jwt_token_validation(self):
        """Test JWT token validation and manipulation"""
        print("Testing JWT token validation...")
        
        # Test with invalid JWT tokens
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            None
        ]
        
        for token in invalid_tokens:
            try:
                headers = {}
                if token:
                    headers["Authorization"] = token
                    
                response = self.client.get("/api/v1/scholarships", headers=headers)
                
                if response.status_code == 200:
                    self.log_issue(
                        "AUTH-003",
                        "middleware/auth.py",
                        f"Invalid JWT token accepted: {token}",
                        f"1. Set Authorization header to '{token}'\n2. Send GET to /api/v1/scholarships",
                        f"Status: {response.status_code}",
                        "Status: 401 Unauthorized",
                        "Critical"
                    )
            except Exception as e:
                pass  # Expected for some invalid tokens

    # 2. INPUT VALIDATION TESTS
    def test_sql_injection_vulnerabilities(self):
        """Test for SQL injection vulnerabilities"""
        print("Testing SQL injection vulnerabilities...")
        
        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES('admin', 'password'); --",
            "' OR 1=1 --"
        ]
        
        for payload in sql_payloads:
            try:
                # Test search endpoint
                response = self.client.get(f"/search?q={payload}")
                if "error" in response.text.lower() and ("syntax" in response.text.lower() or "sql" in response.text.lower()):
                    self.log_issue(
                        "SQL-001",
                        "routers/search.py",
                        "Potential SQL injection vulnerability in search endpoint",
                        f"1. Send GET to /search?q={payload}\n2. Check response for SQL errors",
                        f"Response contains SQL error: {response.text[:200]}",
                        "Sanitized input handling without SQL errors",
                        "Critical"
                    )
                    
                # Test scholarship search
                response = self.client.get(f"/api/v1/scholarships?keyword={payload}")
                if "error" in response.text.lower() and ("syntax" in response.text.lower() or "sql" in response.text.lower()):
                    self.log_issue(
                        "SQL-002",
                        "routers/scholarships.py",
                        "Potential SQL injection vulnerability in scholarship search",
                        f"1. Send GET to /api/v1/scholarships?keyword={payload}",
                        f"Response contains SQL error: {response.text[:200]}",
                        "Sanitized input handling without SQL errors",
                        "Critical"
                    )
            except Exception as e:
                pass

    def test_xss_vulnerabilities(self):
        """Test for XSS vulnerabilities"""
        print("Testing XSS vulnerabilities...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            try:
                # Test search with XSS payload
                response = self.client.get(f"/search?q={payload}")
                if payload in response.text and response.headers.get("content-type", "").startswith("text/html"):
                    self.log_issue(
                        "XSS-001",
                        "routers/search.py",
                        "Potential XSS vulnerability in search results",
                        f"1. Send GET to /search?q={payload}\n2. Check if payload is reflected unescaped",
                        f"Payload reflected in response: {response.text[:200]}",
                        "Properly escaped HTML output",
                        "High"
                    )
            except Exception as e:
                pass

    def test_input_size_limits(self):
        """Test input size and boundary validation"""
        print("Testing input size limits...")
        
        # Test extremely long inputs
        long_string = "A" * 10000
        very_long_string = "B" * 100000
        
        test_cases = [
            ("/search", {"q": long_string}),
            ("/search", {"q": very_long_string}),
            ("/api/v1/scholarships", {"keyword": long_string}),
        ]
        
        for endpoint, params in test_cases:
            try:
                response = self.client.get(endpoint, params=params)
                if response.status_code == 500:
                    self.log_issue(
                        "VAL-001",
                        f"Router: {endpoint}",
                        "Server error on extremely long input",
                        f"1. Send GET to {endpoint} with {len(params[list(params.keys())[0]])} character input",
                        f"Status: {response.status_code}, Error: {response.text[:200]}",
                        "Status: 400 Bad Request with proper validation error",
                        "Medium"
                    )
            except Exception as e:
                self.log_issue(
                    "VAL-002",
                    f"Router: {endpoint}",
                    f"Exception on long input: {str(e)}",
                    f"Send long input to {endpoint}",
                    f"Exception: {str(e)}",
                    "Graceful handling of long inputs",
                    "Medium"
                )

    # 3. BUSINESS LOGIC TESTS
    def test_data_consistency(self):
        """Test data consistency across services"""
        print("Testing data consistency...")
        
        try:
            # Check scholarship count consistency
            all_scholarships = scholarship_service.get_all_scholarships()
            mock_count = len(MOCK_SCHOLARSHIPS)
            service_count = len(all_scholarships)
            
            if service_count != mock_count:
                self.log_issue(
                    "DATA-001",
                    "services/scholarship_service.py",
                    "Scholarship count mismatch between mock data and service",
                    "1. Get scholarship count from service\n2. Compare with MOCK_SCHOLARSHIPS count",
                    f"Service count: {service_count}, Mock count: {mock_count}",
                    "Counts should match",
                    "High"
                )
                
            # Check for duplicate scholarship IDs
            ids = [sch.id for sch in all_scholarships]
            if len(ids) != len(set(ids)):
                self.log_issue(
                    "DATA-002",
                    "data/scholarships.py",
                    "Duplicate scholarship IDs found",
                    "1. Get all scholarship IDs\n2. Check for duplicates",
                    f"Found {len(ids) - len(set(ids))} duplicate IDs",
                    "All scholarship IDs should be unique",
                    "Critical"
                )
                
        except Exception as e:
            self.log_issue(
                "DATA-003",
                "services/scholarship_service.py",
                f"Data consistency test failed: {str(e)}",
                "Run data consistency checks",
                f"Exception: {str(e)}",
                "Successful data validation",
                "High"
            )

    def test_eligibility_logic_errors(self):
        """Test eligibility calculation logic"""
        print("Testing eligibility logic...")
        
        try:
            # Test with invalid user profiles
            invalid_profiles = [
                UserProfile(
                    user_id="test1",
                    gpa=5.0,  # Invalid GPA > 4.0
                    grade_level="graduate",
                    field_of_study=FieldOfStudy.ENGINEERING,
                    citizenship="US",
                    state="CA"
                ),
                UserProfile(
                    user_id="test2",
                    gpa=-1.0,  # Invalid negative GPA
                    grade_level="undergraduate",
                    field_of_study=FieldOfStudy.SCIENCE,
                    citizenship="US",
                    state="NY"
                )
            ]
            
            for profile in invalid_profiles:
                try:
                    # This should fail validation but let's see what happens
                    result = eligibility_service.check_eligibility("sch_001", profile)
                    if result.is_eligible:
                        self.log_issue(
                            "ELIG-001",
                            "services/eligibility_service.py",
                            f"Invalid user profile accepted as eligible (GPA: {profile.gpa})",
                            f"1. Create user profile with GPA {profile.gpa}\n2. Check eligibility",
                            f"Profile accepted, eligibility: {result.is_eligible}",
                            "Invalid profile should be rejected",
                            "High"
                        )
                except Exception as e:
                    # This is expected for validation errors
                    pass
                    
        except Exception as e:
            self.log_issue(
                "ELIG-002",
                "services/eligibility_service.py",
                f"Eligibility logic test failed: {str(e)}",
                "Test eligibility with invalid profiles",
                f"Exception: {str(e)}",
                "Proper validation handling",
                "Medium"
            )

    def test_amount_calculation_errors(self):
        """Test scholarship amount calculations and edge cases"""
        print("Testing amount calculations...")
        
        try:
            # Test search with invalid amount ranges
            response = self.client.get("/api/v1/scholarships?min_amount=-1000")
            if response.status_code == 200:
                self.log_issue(
                    "AMT-001",
                    "routers/scholarships.py",
                    "Negative minimum amount accepted",
                    "1. Send GET to /api/v1/scholarships?min_amount=-1000",
                    f"Status: {response.status_code}",
                    "Status: 400 Bad Request for negative amount",
                    "Medium"
                )
                
            # Test with min > max amount
            response = self.client.get("/api/v1/scholarships?min_amount=10000&max_amount=5000")
            if response.status_code == 200:
                data = response.json()
                if data.get("total_count", 0) > 0:
                    self.log_issue(
                        "AMT-002",
                        "services/scholarship_service.py",
                        "Search returns results when min_amount > max_amount",
                        "1. Send GET with min_amount=10000&max_amount=5000",
                        f"Returned {data.get('total_count', 0)} results",
                        "Should return 0 results or validation error",
                        "Medium"
                    )
                    
        except Exception as e:
            self.log_issue(
                "AMT-003",
                "routers/scholarships.py",
                f"Amount calculation test failed: {str(e)}",
                "Test amount validation",
                f"Exception: {str(e)}",
                "Proper amount validation",
                "Medium"
            )

    # 4. API ENDPOINT TESTS
    def test_endpoint_response_formats(self):
        """Test API endpoint response format consistency"""
        print("Testing endpoint response formats...")
        
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api", "GET"),
            ("/search", "GET"),
            ("/eligibility/check", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                else:
                    response = self.client.post(endpoint, json={})
                    
                # Check if response is valid JSON
                try:
                    data = response.json()
                except ValueError:
                    if response.status_code not in [404, 405]:  # These might return HTML
                        self.log_issue(
                            "API-001",
                            f"Router: {endpoint}",
                            "Endpoint returns non-JSON response",
                            f"1. Send {method} to {endpoint}\n2. Check response format",
                            f"Content-Type: {response.headers.get('content-type')}, Body: {response.text[:100]}",
                            "Valid JSON response",
                            "Medium"
                        )
                        
                # Check for proper error format
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        if "error" not in error_data and "detail" not in error_data:
                            self.log_issue(
                                "API-002",
                                f"Router: {endpoint}",
                                "Error response missing standard error format",
                                f"1. Send {method} to {endpoint}\n2. Check error response format",
                                f"Response: {response.text[:200]}",
                                "Standard error format with 'error' or 'detail' field",
                                "Low"
                            )
                    except ValueError:
                        pass  # Already logged above
                        
            except Exception as e:
                self.log_issue(
                    "API-003",
                    f"Router: {endpoint}",
                    f"Endpoint test failed: {str(e)}",
                    f"Test {method} {endpoint}",
                    f"Exception: {str(e)}",
                    "Successful endpoint response",
                    "High"
                )

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("Testing rate limiting...")
        
        # Send rapid requests to trigger rate limiting
        rate_limited_endpoints = [
            "/search",
            "/eligibility/check"
        ]
        
        for endpoint in rate_limited_endpoints:
            try:
                responses = []
                for i in range(50):  # Send many requests quickly
                    response = self.client.get(endpoint)
                    responses.append(response.status_code)
                    
                # Check if any requests were rate limited
                rate_limited = any(status == 429 for status in responses)
                if not rate_limited:
                    self.log_issue(
                        "RATE-001",
                        f"Router: {endpoint}",
                        "Rate limiting not triggered after 50 rapid requests",
                        f"1. Send 50 rapid GET requests to {endpoint}\n2. Check for 429 responses",
                        f"All responses: {set(responses)}",
                        "Some requests should return 429 Too Many Requests",
                        "Medium"
                    )
                    
            except Exception as e:
                self.log_issue(
                    "RATE-002",
                    f"Router: {endpoint}",
                    f"Rate limiting test failed: {str(e)}",
                    f"Test rate limiting on {endpoint}",
                    f"Exception: {str(e)}",
                    "Proper rate limiting behavior",
                    "Medium"
                )

    # 5. SECURITY TESTS
    def test_cors_configuration(self):
        """Test CORS configuration for security issues"""
        print("Testing CORS configuration...")
        
        try:
            # Test with various Origin headers
            origins_to_test = [
                "https://malicious-site.com",
                "http://localhost:3000",
                "null"
            ]
            
            for origin in origins_to_test:
                response = self.client.get("/", headers={"Origin": origin})
                cors_header = response.headers.get("Access-Control-Allow-Origin")
                
                if cors_header == "*":
                    self.log_issue(
                        "CORS-001",
                        "main.py",
                        "CORS configured to allow all origins (*)",
                        f"1. Send request with Origin: {origin}\n2. Check Access-Control-Allow-Origin header",
                        f"Access-Control-Allow-Origin: {cors_header}",
                        "Specific origins only, not wildcard",
                        "Medium"
                    )
                    break  # Only log once
                    
        except Exception as e:
            self.log_issue(
                "CORS-002",
                "main.py",
                f"CORS test failed: {str(e)}",
                "Test CORS configuration",
                f"Exception: {str(e)}",
                "Proper CORS handling",
                "Low"
            )

    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        print("Testing sensitive data exposure...")
        
        try:
            # Check error responses for sensitive information
            response = self.client.get("/api/v1/scholarships/nonexistent")
            if response.status_code >= 400:
                response_text = response.text.lower()
                sensitive_indicators = [
                    "traceback",
                    "exception",
                    "stack trace",
                    "file path",
                    "/home/",
                    "/usr/",
                    "password",
                    "secret",
                    "token"
                ]
                
                for indicator in sensitive_indicators:
                    if indicator in response_text:
                        self.log_issue(
                            "SEC-001",
                            "middleware/error_handling.py",
                            f"Error response contains sensitive information: {indicator}",
                            f"1. Send GET to /api/v1/scholarships/nonexistent\n2. Check error response",
                            f"Response contains: {indicator}",
                            "Generic error message without sensitive details",
                            "Medium"
                        )
                        
        except Exception as e:
            pass

    # 6. PERFORMANCE AND EDGE CASE TESTS
    def test_null_and_empty_inputs(self):
        """Test handling of null and empty inputs"""
        print("Testing null and empty input handling...")
        
        test_cases = [
            ("/search", {"q": ""}),
            ("/search", {"q": None}),
            ("/api/v1/scholarships", {"keyword": ""}),
            ("/eligibility/check", {"user_id": ""}),
        ]
        
        for endpoint, params in test_cases:
            try:
                response = self.client.get(endpoint, params=params)
                if response.status_code == 500:
                    self.log_issue(
                        "NULL-001",
                        f"Router: {endpoint}",
                        f"Server error on empty/null input: {params}",
                        f"1. Send GET to {endpoint} with params {params}",
                        f"Status: {response.status_code}, Response: {response.text[:200]}",
                        "Graceful handling of empty inputs",
                        "Medium"
                    )
            except Exception as e:
                self.log_issue(
                    "NULL-002",
                    f"Router: {endpoint}",
                    f"Exception on empty input: {str(e)}",
                    f"Send empty input to {endpoint}",
                    f"Exception: {str(e)}",
                    "Graceful handling of empty inputs",
                    "Medium"
                )

    def test_special_characters(self):
        """Test handling of special characters and encoding"""
        print("Testing special character handling...")
        
        special_chars = [
            "unicode: café résumé 中文",
            "symbols: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "newlines: test\nwith\nnewlines",
            "tabs: test\twith\ttabs",
            "quotes: test\"with'quotes",
        ]
        
        for test_input in special_chars:
            try:
                response = self.client.get(f"/search?q={test_input}")
                if response.status_code == 500:
                    self.log_issue(
                        "CHAR-001",
                        "routers/search.py",
                        f"Server error on special characters: {test_input[:20]}...",
                        f"1. Send GET to /search?q={test_input[:50]}",
                        f"Status: {response.status_code}",
                        "Proper handling of special characters",
                        "Low"
                    )
            except Exception as e:
                pass

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Execute all test categories"""
        print("🔍 Starting Comprehensive QA Test Suite...")
        print("=" * 60)
        
        test_methods = [
            self.test_authentication_bypass,
            self.test_jwt_token_validation,
            self.test_sql_injection_vulnerabilities,
            self.test_xss_vulnerabilities,
            self.test_input_size_limits,
            self.test_data_consistency,
            self.test_eligibility_logic_errors,
            self.test_amount_calculation_errors,
            self.test_endpoint_response_formats,
            self.test_rate_limiting,
            self.test_cors_configuration,
            self.test_sensitive_data_exposure,
            self.test_null_and_empty_inputs,
            self.test_special_characters
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed: {str(e)}")
                self.log_issue(
                    "TEST-ERROR",
                    test_method.__name__,
                    f"Test execution failed: {str(e)}",
                    f"Execute {test_method.__name__}",
                    f"Exception: {str(e)}",
                    "Successful test execution",
                    "High"
                )
        
        print("=" * 60)
        print(f"🏁 QA Testing Complete. Found {len(self.issues)} issues.")
        
        return self.issues

def main():
    """Main execution function"""
    qa_suite = ComprehensiveQATestSuite()
    issues = qa_suite.run_all_tests()
    
    # Generate comprehensive report
    report = {
        "executive_summary": {
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i["severity"] == "Critical"]),
            "high_issues": len([i for i in issues if i["severity"] == "High"]),
            "medium_issues": len([i for i in issues if i["severity"] == "Medium"]),
            "low_issues": len([i for i in issues if i["severity"] == "Low"]),
            "test_timestamp": datetime.utcnow().isoformat()
        },
        "detailed_findings": issues,
        "testing_methodology": {
            "authentication_tests": "JWT validation, bypass attempts, authorization checks",
            "security_tests": "SQL injection, XSS, CORS, sensitive data exposure",
            "input_validation": "Size limits, null values, special characters, boundary cases",
            "business_logic": "Data consistency, eligibility calculations, amount validations",
            "api_testing": "Response formats, error handling, rate limiting"
        }
    }
    
    # Save to file
    with open("comprehensive_qa_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Comprehensive QA report saved to comprehensive_qa_report.json")
    
    # Print summary
    print("\n📊 EXECUTIVE SUMMARY:")
    print(f"Total Issues Found: {report['executive_summary']['total_issues']}")
    print(f"Critical: {report['executive_summary']['critical_issues']}")
    print(f"High: {report['executive_summary']['high_issues']}")
    print(f"Medium: {report['executive_summary']['medium_issues']}")
    print(f"Low: {report['executive_summary']['low_issues']}")
    
    return issues

if __name__ == "__main__":
    main()