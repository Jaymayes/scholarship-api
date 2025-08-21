#!/usr/bin/env python3
"""
Senior QA Engineer - Comprehensive Analysis and Test Execution
CRITICAL: This is READ-ONLY analysis. NO code modifications are performed.
Objective: Identify and report all errors, bugs, unexpected behavior, and vulnerabilities.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import sys
import os

class QAIssue:
    """Structured representation of a QA issue"""
    def __init__(self, issue_id: str, location: str, description: str, 
                 steps_to_reproduce: str, observed_output: str, 
                 expected_output: str, severity: str):
        self.issue_id = issue_id
        self.location = location
        self.description = description
        self.steps_to_reproduce = steps_to_reproduce
        self.observed_output = observed_output
        self.expected_output = expected_output
        self.severity = severity

class SeniorQAAnalyzer:
    """Senior QA Engineer comprehensive analysis framework"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.issues: List[QAIssue] = []
        self.test_results = {}
        
    def add_issue(self, issue_id: str, location: str, description: str, 
                  steps: str, observed: str, expected: str, severity: str):
        """Add a new issue to the tracking list"""
        issue = QAIssue(issue_id, location, description, steps, observed, expected, severity)
        self.issues.append(issue)
        print(f"🔍 [{severity}] {issue_id}: {description}")
        
    async def run_comprehensive_analysis(self):
        """Execute comprehensive QA analysis across all components"""
        print("🎯 SENIOR QA COMPREHENSIVE ANALYSIS STARTING")
        print("=" * 60)
        
        # Test categories
        await self.test_api_endpoints()
        await self.test_authentication_security()
        await self.test_rate_limiting()
        await self.test_cors_security()
        await self.test_input_validation()
        await self.test_error_handling()
        await self.test_edge_cases()
        await self.test_concurrent_requests()
        await self.analyze_code_vulnerabilities()
        await self.test_database_operations()
        
        # Generate final report
        self.generate_comprehensive_report()
        
    async def test_api_endpoints(self):
        """Test all API endpoints for basic functionality"""
        print("\n📡 Testing API Endpoints...")
        
        endpoints = [
            ("GET", "/", "Root endpoint"),
            ("GET", "/healthz", "Health check"),
            ("GET", "/api/v1/scholarships", "Scholarships listing"),
            ("GET", "/api/v1/search", "Search functionality"),
            ("GET", "/api/v1/eligibility/check?gpa=3.5&grade_level=undergraduate", "Eligibility check"),
            ("GET", "/api/v1/recommendations", "Recommendations"),
            ("GET", "/docs", "API documentation"),
            ("GET", "/metrics", "Metrics endpoint"),
            ("HEAD", "/", "HEAD method support"),
            ("OPTIONS", "/api/v1/scholarships", "CORS preflight")
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, endpoint, description in endpoints:
                try:
                    response = await client.request(method, f"{self.base_url}{endpoint}")
                    
                    # Analyze response
                    if response.status_code >= 500:
                        self.add_issue(
                            f"API-{len(self.issues)+1:03d}",
                            f"Endpoint: {method} {endpoint}",
                            f"Server error in {description}",
                            f"Send {method} request to {endpoint}",
                            f"HTTP {response.status_code}: {response.text[:200]}",
                            f"HTTP 2xx response with valid JSON/HTML",
                            "High"
                        )
                    elif response.status_code == 404 and endpoint not in ["/favicon.ico"]:
                        self.add_issue(
                            f"API-{len(self.issues)+1:03d}",
                            f"Endpoint: {method} {endpoint}",
                            f"Endpoint not found: {description}",
                            f"Send {method} request to {endpoint}",
                            f"HTTP 404: {response.text[:200]}",
                            f"HTTP 2xx response or proper documentation",
                            "Medium"
                        )
                    elif method == "OPTIONS" and response.status_code == 400:
                        # Expected for CORS with malicious origins
                        pass
                    else:
                        print(f"   ✅ {method} {endpoint}: {response.status_code}")
                        
                except Exception as e:
                    self.add_issue(
                        f"API-{len(self.issues)+1:03d}",
                        f"Endpoint: {method} {endpoint}",
                        f"Connection/timeout error in {description}",
                        f"Send {method} request to {endpoint}",
                        f"Exception: {str(e)}",
                        f"Successful HTTP response",
                        "Critical"
                    )
                    
    async def test_authentication_security(self):
        """Test authentication and authorization mechanisms"""
        print("\n🔐 Testing Authentication Security...")
        
        protected_endpoints = [
            "/api/v1/scholarships",
            "/api/v1/search", 
            "/api/v1/eligibility/check"
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in protected_endpoints:
                # Test without authentication
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    # Check if authentication is properly enforced
                    if response.status_code == 200:
                        # This might be expected if PUBLIC_READ_ENDPOINTS is enabled
                        print(f"   ℹ️  {endpoint}: Public access enabled (check if intentional)")
                    elif response.status_code != 401:
                        self.add_issue(
                            f"AUTH-{len(self.issues)+1:03d}",
                            f"Endpoint: {endpoint}",
                            "Authentication bypass vulnerability",
                            f"Access {endpoint} without Bearer token",
                            f"HTTP {response.status_code}: {response.text[:200]}",
                            "HTTP 401 Unauthorized",
                            "High"
                        )
                    
                    # Test with malformed token
                    malformed_response = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers={"Authorization": "Bearer invalid.token.here"}
                    )
                    
                    if malformed_response.status_code == 200:
                        self.add_issue(
                            f"AUTH-{len(self.issues)+1:03d}",
                            f"Endpoint: {endpoint}",
                            "Invalid JWT token accepted",
                            f"Access {endpoint} with malformed Bearer token",
                            f"HTTP {malformed_response.status_code}",
                            "HTTP 401 Unauthorized",
                            "High"
                        )
                        
                except Exception as e:
                    self.add_issue(
                        f"AUTH-{len(self.issues)+1:03d}",
                        f"Endpoint: {endpoint}",
                        "Authentication test failure",
                        f"Test authentication on {endpoint}",
                        f"Exception: {str(e)}",
                        "Proper authentication response",
                        "Medium"
                    )
                    
    async def test_rate_limiting(self):
        """Test rate limiting functionality and bypass attempts"""
        print("\n🚦 Testing Rate Limiting...")
        
        test_endpoint = "/api/v1/search"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Rapid fire requests to trigger rate limiting
            responses = []
            for i in range(25):  # Should exceed most rate limits
                try:
                    response = await client.get(f"{self.base_url}{test_endpoint}")
                    responses.append(response.status_code)
                    
                    if i > 10 and response.status_code == 429:
                        # Check if rate limiting headers are present
                        if "retry-after" not in response.headers and "ratelimit" not in str(response.headers).lower():
                            self.add_issue(
                                f"RATE-{len(self.issues)+1:03d}",
                                "Rate limiting headers",
                                "Missing rate limiting headers on 429 response",
                                "Trigger rate limiting and check response headers",
                                f"Headers: {dict(response.headers)}",
                                "Retry-After or RateLimit-* headers present",
                                "Medium"
                            )
                        break
                        
                except Exception as e:
                    self.add_issue(
                        f"RATE-{len(self.issues)+1:03d}",
                        "Rate limiting test",
                        "Rate limiting test failed with exception",
                        "Send rapid requests to trigger rate limiting",
                        f"Exception: {str(e)}",
                        "429 responses with proper headers",
                        "Medium"
                    )
                    break
            
            # Check if rate limiting was triggered
            rate_limit_triggered = any(code == 429 for code in responses)
            if not rate_limit_triggered and len(responses) > 15:
                self.add_issue(
                    f"RATE-{len(self.issues)+1:03d}",
                    "Rate limiting enforcement",
                    "Rate limiting not triggered after excessive requests",
                    "Send 25+ rapid requests to search endpoint",
                    f"All responses: {responses}",
                    "429 Too Many Requests after threshold exceeded",
                    "High"
                )
                
    async def test_cors_security(self):
        """Test CORS configuration for security vulnerabilities"""
        print("\n🌐 Testing CORS Security...")
        
        malicious_origins = [
            "https://malicious-attacker.com",
            "https://evil.com", 
            "https://phishing-site.net",
            "http://localhost:3000",  # Common dev port
            "https://random-domain.xyz"
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for origin in malicious_origins:
                try:
                    response = await client.options(
                        f"{self.base_url}/api/v1/scholarships",
                        headers={
                            "Origin": origin,
                            "Access-Control-Request-Method": "GET",
                            "Access-Control-Request-Headers": "authorization"
                        }
                    )
                    
                    # Check if malicious origin is allowed
                    if response.status_code == 200 and "access-control-allow-origin" in response.headers:
                        allowed_origin = response.headers.get("access-control-allow-origin")
                        if allowed_origin == origin or allowed_origin == "*":
                            self.add_issue(
                                f"CORS-{len(self.issues)+1:03d}",
                                "CORS configuration",
                                f"Malicious origin allowed: {origin}",
                                f"Send OPTIONS request with Origin: {origin}",
                                f"Access-Control-Allow-Origin: {allowed_origin}",
                                "400 Bad Request or origin rejection",
                                "High"
                            )
                    
                except Exception as e:
                    print(f"   ℹ️  CORS test for {origin} failed: {e}")
                    
            # Test for wildcard CORS
            try:
                response = await client.get(
                    f"{self.base_url}/",
                    headers={"Origin": "https://unknown-domain.com"}
                )
                
                if response.headers.get("access-control-allow-origin") == "*":
                    self.add_issue(
                        f"CORS-{len(self.issues)+1:03d}",
                        "CORS wildcard configuration",
                        "Wildcard CORS detected in production",
                        "Send GET request with random Origin header",
                        "Access-Control-Allow-Origin: *",
                        "Specific origin whitelist or no CORS header",
                        "High"
                    )
                    
            except Exception as e:
                print(f"   ℹ️  Wildcard CORS test failed: {e}")
                
    async def test_input_validation(self):
        """Test input validation and sanitization"""
        print("\n🔍 Testing Input Validation...")
        
        # SQL injection attempts
        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "1' OR '1'='1",
            "admin'--",
            "'; SELECT * FROM users; --"
        ]
        
        # XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
        ]
        
        # Path traversal attempts
        path_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f%65%74%63%2f%70%61%73%73%77%64"
        ]
        
        all_payloads = sql_payloads + xss_payloads + path_payloads
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for payload in all_payloads:
                try:
                    # Test in query parameter
                    response = await client.get(
                        f"{self.base_url}/api/v1/search",
                        params={"keyword": payload}
                    )
                    
                    # Check if payload is reflected or causes errors
                    response_text = response.text.lower()
                    if payload.lower() in response_text and response.status_code == 200:
                        self.add_issue(
                            f"INPUT-{len(self.issues)+1:03d}",
                            "Query parameter validation",
                            f"Potential XSS/injection vulnerability with payload: {payload[:50]}...",
                            f"Send GET /api/v1/search?keyword={payload}",
                            f"Payload reflected in response: {response.text[:200]}",
                            "Payload sanitized or rejected",
                            "High"
                        )
                    
                    if response.status_code >= 500:
                        self.add_issue(
                            f"INPUT-{len(self.issues)+1:03d}",
                            "Error handling",
                            f"Server error on malicious input: {payload[:50]}...",
                            f"Send GET /api/v1/search?keyword={payload}",
                            f"HTTP {response.status_code}: {response.text[:200]}",
                            "HTTP 400 Bad Request with sanitized error",
                            "Medium"
                        )
                        
                except Exception as e:
                    print(f"   ℹ️  Input validation test failed for {payload[:20]}: {e}")
                    
    async def test_error_handling(self):
        """Test error handling and information disclosure"""
        print("\n⚠️  Testing Error Handling...")
        
        error_test_cases = [
            ("GET", "/nonexistent-endpoint", 404),
            ("POST", "/api/v1/scholarships", 405),  # Method not allowed
            ("GET", "/api/v1/scholarships/nonexistent-id", 404),
            ("GET", "/api/v1/eligibility/check", 400),  # Missing required params
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, endpoint, expected_status in error_test_cases:
                try:
                    response = await client.request(method, f"{self.base_url}{endpoint}")
                    
                    if response.status_code != expected_status:
                        self.add_issue(
                            f"ERR-{len(self.issues)+1:03d}",
                            f"Error handling: {method} {endpoint}",
                            f"Unexpected error status code",
                            f"Send {method} request to {endpoint}",
                            f"HTTP {response.status_code}: {response.text[:200]}",
                            f"HTTP {expected_status}",
                            "Medium"
                        )
                    
                    # Check for information disclosure
                    response_text = response.text.lower()
                    sensitive_info = ["traceback", "stack trace", "exception", "internal error", "debug"]
                    
                    for info in sensitive_info:
                        if info in response_text:
                            self.add_issue(
                                f"ERR-{len(self.issues)+1:03d}",
                                f"Information disclosure: {method} {endpoint}",
                                f"Sensitive information leaked in error response",
                                f"Send {method} request to {endpoint}",
                                f"Response contains: {info}",
                                "Generic error message without sensitive details",
                                "Medium"
                            )
                            
                except Exception as e:
                    print(f"   ℹ️  Error handling test failed for {method} {endpoint}: {e}")
                    
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n🔬 Testing Edge Cases...")
        
        edge_cases = [
            # Large parameter values
            ("GET", "/api/v1/search", {"keyword": "a" * 10000}),
            ("GET", "/api/v1/eligibility/check", {"gpa": "999999"}),
            ("GET", "/api/v1/scholarships", {"limit": "999999"}),
            
            # Invalid data types
            ("GET", "/api/v1/eligibility/check", {"gpa": "not-a-number"}),
            ("GET", "/api/v1/scholarships", {"min_amount": "invalid"}),
            
            # Boundary values
            ("GET", "/api/v1/eligibility/check", {"gpa": "5.0"}),  # Above max GPA
            ("GET", "/api/v1/eligibility/check", {"gpa": "-1.0"}),  # Below min GPA
            ("GET", "/api/v1/scholarships", {"limit": "0"}),  # Zero limit
            ("GET", "/api/v1/scholarships", {"offset": "-1"}),  # Negative offset
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, endpoint, params in edge_cases:
                try:
                    response = await client.request(
                        method, 
                        f"{self.base_url}{endpoint}",
                        params=params
                    )
                    
                    if response.status_code >= 500:
                        self.add_issue(
                            f"EDGE-{len(self.issues)+1:03d}",
                            f"Edge case handling: {endpoint}",
                            f"Server error on edge case input: {params}",
                            f"Send {method} to {endpoint} with params: {params}",
                            f"HTTP {response.status_code}: {response.text[:200]}",
                            "HTTP 400 Bad Request with validation error",
                            "Medium"
                        )
                    elif response.status_code == 200:
                        # Check if invalid inputs are accepted
                        param_str = str(params)
                        if "not-a-number" in param_str or "999999" in param_str:
                            self.add_issue(
                                f"EDGE-{len(self.issues)+1:03d}",
                                f"Input validation: {endpoint}",
                                f"Invalid input accepted: {params}",
                                f"Send {method} to {endpoint} with params: {params}",
                                f"HTTP 200: Request processed successfully",
                                "HTTP 400 Bad Request with validation error",
                                "Medium"
                            )
                            
                except Exception as e:
                    print(f"   ℹ️  Edge case test failed for {endpoint}: {e}")
                    
    async def test_concurrent_requests(self):
        """Test system behavior under concurrent load"""
        print("\n🔄 Testing Concurrent Requests...")
        
        async def single_request(client, endpoint):
            try:
                response = await client.get(f"{self.base_url}{endpoint}")
                return response.status_code
            except Exception as e:
                return f"Error: {str(e)}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test concurrent requests to same endpoint
            tasks = [single_request(client, "/api/v1/scholarships") for _ in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            error_count = sum(1 for r in results if isinstance(r, Exception) or str(r).startswith("Error"))
            server_errors = sum(1 for r in results if isinstance(r, int) and r >= 500)
            
            if error_count > 5:
                self.add_issue(
                    f"CONC-{len(self.issues)+1:03d}",
                    "Concurrent request handling",
                    f"High failure rate under concurrent load: {error_count}/20 failures",
                    "Send 20 concurrent requests to /api/v1/scholarships",
                    f"Failed requests: {error_count}, Results: {results[:5]}...",
                    "Majority of requests should succeed",
                    "High"
                )
            
            if server_errors > 2:
                self.add_issue(
                    f"CONC-{len(self.issues)+1:03d}",
                    "Server stability under load",
                    f"Server errors under concurrent load: {server_errors}/20",
                    "Send 20 concurrent requests to /api/v1/scholarships",
                    f"Server errors: {server_errors}",
                    "No server errors under normal concurrent load",
                    "High"
                )
                
    async def analyze_code_vulnerabilities(self):
        """Static analysis of code for common vulnerabilities"""
        print("\n🔍 Analyzing Code Vulnerabilities...")
        
        # LSP diagnostic issues already identified
        lsp_issues = [
            {
                "file": "routers/scholarships.py",
                "lines": "312-320",
                "issue": "Argument missing for parameter 'eligibility_criteria'",
                "severity": "High"
            },
            {
                "file": "middleware/rate_limiting.py", 
                "lines": "219, 223, 227",
                "issue": "'limit' is not a known member of 'None'",
                "severity": "High"
            }
        ]
        
        for issue in lsp_issues:
            self.add_issue(
                f"CODE-{len(self.issues)+1:03d}",
                f"{issue['file']}:{issue['lines']}",
                f"Static analysis error: {issue['issue']}",
                f"Analyze {issue['file']} with Python LSP",
                f"LSP diagnostic: {issue['issue']}",
                "Clean code without static analysis errors",
                issue['severity']
            )
            
        # Additional code smell analysis
        potential_issues = [
            {
                "location": "main.py:136",
                "description": "Rate limiter fallback warning printed to stdout",
                "severity": "Low"
            },
            {
                "location": "config/settings.py:33-36", 
                "description": "Hardcoded banned secrets list may need updates",
                "severity": "Low"
            }
        ]
        
        for issue in potential_issues:
            self.add_issue(
                f"CODE-{len(self.issues)+1:03d}",
                issue['location'],
                issue['description'],
                f"Review code at {issue['location']}",
                "Code pattern that may need improvement",
                "Best practice implementation",
                issue['severity']
            )
            
    async def test_database_operations(self):
        """Test database-related operations for vulnerabilities"""
        print("\n🗄️  Testing Database Operations...")
        
        # Test endpoints that likely interact with database
        db_endpoints = [
            "/api/v1/scholarships",
            "/api/v1/search",
            "/api/v1/eligibility/check?gpa=3.5&grade_level=undergraduate"
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in db_endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    if response.status_code == 200:
                        # Check response time for potential performance issues
                        if hasattr(response, 'elapsed') and response.elapsed.total_seconds() > 5:
                            self.add_issue(
                                f"DB-{len(self.issues)+1:03d}",
                                f"Database performance: {endpoint}",
                                f"Slow database query detected",
                                f"Send GET request to {endpoint}",
                                f"Response time: {response.elapsed.total_seconds()}s",
                                "Response time under 1 second for simple queries",
                                "Medium"
                            )
                        
                        # Check for potential data leakage
                        response_text = response.text.lower()
                        sensitive_patterns = ["password", "secret", "token", "key", "hash"]
                        
                        for pattern in sensitive_patterns:
                            if pattern in response_text:
                                self.add_issue(
                                    f"DB-{len(self.issues)+1:03d}",
                                    f"Data exposure: {endpoint}",
                                    f"Potential sensitive data exposure: {pattern}",
                                    f"Send GET request to {endpoint}",
                                    f"Response contains: {pattern}",
                                    "No sensitive data in API responses",
                                    "High"
                                )
                                
                except Exception as e:
                    print(f"   ℹ️  Database test failed for {endpoint}: {e}")
                    
    def generate_comprehensive_report(self):
        """Generate the final comprehensive QA report"""
        print("\n" + "="*80)
        print("📋 SENIOR QA COMPREHENSIVE ANALYSIS REPORT")
        print("="*80)
        
        # Summary statistics
        total_issues = len(self.issues)
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
            
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(f"   Total Issues Found: {total_issues}")
        print(f"   Critical: {severity_counts['Critical']}")
        print(f"   High: {severity_counts['High']}")
        print(f"   Medium: {severity_counts['Medium']}")
        print(f"   Low: {severity_counts['Low']}")
        
        print(f"\n🔍 DETAILED FINDINGS:")
        print("-" * 80)
        
        # Sort issues by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_issues = sorted(self.issues, key=lambda x: severity_order[x.severity])
        
        for issue in sorted_issues:
            print(f"\nIssue ID: {issue.issue_id}")
            print(f"Location: {issue.location}")
            print(f"Description: {issue.description}")
            print(f"Severity: {issue.severity}")
            print(f"Steps to Reproduce: {issue.steps_to_reproduce}")
            print(f"Observed Output: {issue.observed_output}")
            print(f"Expected Output: {issue.expected_output}")
            print("-" * 40)
            
        # Save to JSON file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_issues": total_issues,
                "severity_breakdown": severity_counts
            },
            "issues": [
                {
                    "issue_id": issue.issue_id,
                    "location": issue.location,
                    "description": issue.description,
                    "steps_to_reproduce": issue.steps_to_reproduce,
                    "observed_output": issue.observed_output,
                    "expected_output": issue.expected_output,
                    "severity": issue.severity
                }
                for issue in sorted_issues
            ]
        }
        
        with open("SENIOR_QA_COMPREHENSIVE_ANALYSIS_REPORT.json", "w") as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n💾 Report saved to: SENIOR_QA_COMPREHENSIVE_ANALYSIS_REPORT.json")
        print(f"🎯 QA Analysis Complete - {total_issues} issues identified")

async def main():
    """Main execution function"""
    analyzer = SeniorQAAnalyzer()
    await analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    asyncio.run(main())