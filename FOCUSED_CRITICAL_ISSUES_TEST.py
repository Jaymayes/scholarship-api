#!/usr/bin/env python3
"""
Focused Critical Issues Testing
Senior QA Engineer - Deep dive into specific vulnerabilities and edge cases
CRITICAL: This is READ-ONLY analysis. NO code modifications are performed.
"""

import asyncio
import httpx
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any

class CriticalIssuesAnalyzer:
    """Deep dive analyzer for critical security and functional issues"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.critical_issues = []
        
    def add_critical_issue(self, issue_id: str, location: str, description: str,
                          steps: str, observed: str, expected: str, severity: str):
        """Add critical issue to tracking"""
        issue = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps,
            "observed_output": observed,
            "expected_output": expected,
            "severity": severity
        }
        self.critical_issues.append(issue)
        print(f"🚨 [{severity}] {issue_id}: {description}")
        
    async def run_focused_analysis(self):
        """Execute focused analysis on critical areas"""
        print("🎯 FOCUSED CRITICAL ISSUES ANALYSIS")
        print("="*50)
        
        await self.test_jwt_validation_bypass()
        await self.test_sql_injection_advanced()
        await self.test_business_logic_flaws()
        await self.test_sensitive_data_exposure()
        await self.test_parameter_pollution()
        await self.test_race_conditions()
        await self.test_authorization_flaws()
        await self.test_api_versioning_issues()
        await self.test_state_management_bugs()
        
        self.generate_critical_report()
        
    async def test_jwt_validation_bypass(self):
        """Test advanced JWT validation bypass techniques"""
        print("\n🔐 Testing Advanced JWT Validation Bypass...")
        
        jwt_attack_vectors = [
            # None algorithm attack
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTYzMDAwMDAwMH0.",
            
            # Empty signature
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTYzMDAwMDAwMH0.",
            
            # Modified payload
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTYzMDAwMDAwMH0.invalid_signature",
            
            # RS256 to HS256 confusion
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OSwiYWRtaW4iOnRydWV9.signature_here",
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, token in enumerate(jwt_attack_vectors):
                try:
                    response = await client.get(
                        f"{self.base_url}/api/v1/scholarships",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if response.status_code == 200:
                        self.add_critical_issue(
                            f"JWT-{i+1:03d}",
                            "JWT validation bypass",
                            f"JWT attack vector #{i+1} succeeded",
                            f"Send request with crafted JWT: {token[:50]}...",
                            f"HTTP 200: Request accepted with malicious JWT",
                            "HTTP 401 Unauthorized - JWT validation should fail",
                            "Critical"
                        )
                        
                except Exception as e:
                    print(f"   ℹ️  JWT attack vector #{i+1} test failed: {e}")
                    
    async def test_sql_injection_advanced(self):
        """Test advanced SQL injection techniques"""
        print("\n💉 Testing Advanced SQL Injection...")
        
        # Advanced SQL injection payloads
        sqli_payloads = [
            # Union-based injection
            "' UNION SELECT user,password,email FROM users--",
            "1' UNION SELECT @@version,user(),database()--",
            
            # Boolean-based blind SQL injection
            "1' AND (SELECT COUNT(*) FROM scholarships) > 0--",
            "1' AND (SELECT ASCII(SUBSTRING(user(),1,1))) > 64--",
            
            # Time-based blind SQL injection
            "1'; WAITFOR DELAY '00:00:05'--",
            "1' AND (SELECT COUNT(*) FROM scholarships WHERE SLEEP(5))--",
            
            # Error-based injection
            "1' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT user()), 0x7e))--",
            "1' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
            
            # Second-order injection
            "admin'; INSERT INTO logs VALUES('injected')--"
        ]
        
        # Test on various endpoints that might interact with database
        test_endpoints = [
            ("/api/v1/scholarships", "keyword"),
            ("/api/v1/search", "keyword"),
            ("/api/v1/eligibility/check", "field_of_study")
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint, param in test_endpoints:
                for i, payload in enumerate(sqli_payloads):
                    try:
                        params = {param: payload}
                        response = await client.get(
                            f"{self.base_url}{endpoint}",
                            params=params
                        )
                        
                        # Check for SQL error messages
                        error_indicators = [
                            "sql syntax", "mysql", "postgresql", "sqlite", "oracle",
                            "syntax error", "unexpected token", "column", "table",
                            "database error", "query failed"
                        ]
                        
                        response_lower = response.text.lower()
                        for indicator in error_indicators:
                            if indicator in response_lower:
                                self.add_critical_issue(
                                    f"SQLI-{i+1:03d}",
                                    f"SQL injection: {endpoint}",
                                    f"SQL injection vulnerability detected",
                                    f"Send {param}={payload} to {endpoint}",
                                    f"Response contains SQL error: {indicator}",
                                    "Generic error without SQL details",
                                    "Critical"
                                )
                                break
                                
                        # Check for unusual response times (blind injection)
                        if hasattr(response, 'elapsed') and response.elapsed.total_seconds() > 4:
                            if "SLEEP" in payload or "WAITFOR" in payload:
                                self.add_critical_issue(
                                    f"SQLI-{i+100:03d}",
                                    f"Time-based SQL injection: {endpoint}",
                                    f"Time-based SQL injection detected",
                                    f"Send time-delay payload to {endpoint}",
                                    f"Response delayed: {response.elapsed.total_seconds()}s",
                                    "Normal response time < 1 second",
                                    "Critical"
                                )
                                
                    except Exception as e:
                        print(f"   ℹ️  SQL injection test failed: {e}")
                        
    async def test_business_logic_flaws(self):
        """Test business logic vulnerabilities"""
        print("\n🧠 Testing Business Logic Flaws...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test negative values in critical fields
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/scholarships",
                    params={"min_amount": "-1000", "max_amount": "-500"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "scholarships" in data and len(data["scholarships"]) > 0:
                        self.add_critical_issue(
                            "BL-001",
                            "Business logic: scholarship amount validation",
                            "Negative scholarship amounts accepted",
                            "Send min_amount=-1000&max_amount=-500 to /api/v1/scholarships",
                            f"HTTP 200 with {len(data['scholarships'])} results",
                            "HTTP 400 Bad Request - negative amounts should be rejected",
                            "High"
                        )
            except Exception as e:
                print(f"   ℹ️  Business logic test 1 failed: {e}")
                
            # Test GPA validation bypass
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/eligibility/check",
                    params={"gpa": "10.0", "grade_level": "undergraduate"}
                )
                
                if response.status_code == 200:
                    self.add_critical_issue(
                        "BL-002",
                        "Business logic: GPA validation",
                        "Invalid GPA above 4.0 scale accepted",
                        "Send gpa=10.0 to eligibility check",
                        "HTTP 200: Request processed",
                        "HTTP 400 Bad Request - GPA above 4.0 should be rejected",
                        "Medium"
                    )
            except Exception as e:
                print(f"   ℹ️  Business logic test 2 failed: {e}")
                
            # Test date logic flaws
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/scholarships",
                    params={
                        "deadline_after": "2030-12-31",
                        "deadline_before": "2020-01-01"  # Before is after After
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "scholarships" in data and len(data["scholarships"]) > 0:
                        self.add_critical_issue(
                            "BL-003",
                            "Business logic: date range validation",
                            "Illogical date range accepted",
                            "Send deadline_before < deadline_after",
                            f"HTTP 200 with results",
                            "HTTP 400 Bad Request or empty results with warning",
                            "Medium"
                        )
            except Exception as e:
                print(f"   ℹ️  Business logic test 3 failed: {e}")
                
    async def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        print("\n🔍 Testing Sensitive Data Exposure...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test error responses for sensitive information
            sensitive_endpoints = [
                "/api/v1/scholarships/999999",  # Non-existent ID
                "/api/v1/eligibility/check?invalid=param",
                "/admin",  # Potential admin endpoint
                "/.env",   # Environment file
                "/config", # Configuration endpoint
                "/debug",  # Debug endpoint
            ]
            
            for endpoint in sensitive_endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    # Check for sensitive data in responses
                    sensitive_patterns = [
                        "password", "secret", "key", "token", "hash", "salt",
                        "database_url", "api_key", "private_key", "connection_string",
                        "stack trace", "traceback", "exception", "debug",
                        "config", "environment", "env"
                    ]
                    
                    response_lower = response.text.lower()
                    for pattern in sensitive_patterns:
                        if pattern in response_lower:
                            self.add_critical_issue(
                                f"DATA-{len(self.critical_issues)+1:03d}",
                                f"Data exposure: {endpoint}",
                                f"Sensitive information exposed: {pattern}",
                                f"Access {endpoint}",
                                f"Response contains: {pattern}",
                                "Generic response without sensitive data",
                                "High"
                            )
                            break
                            
                except Exception as e:
                    print(f"   ℹ️  Data exposure test failed for {endpoint}: {e}")
                    
    async def test_parameter_pollution(self):
        """Test HTTP Parameter Pollution attacks"""
        print("\n🔄 Testing HTTP Parameter Pollution...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test parameter pollution scenarios
            pollution_tests = [
                # Multiple same parameters
                "keyword=safe&keyword=<script>alert('xss')</script>",
                "gpa=3.5&gpa=999&grade_level=undergraduate",
                "limit=10&limit=9999999",
                "min_amount=100&min_amount=-1000"
            ]
            
            for test_params in pollution_tests:
                try:
                    # Manual URL construction to test parameter pollution
                    url = f"{self.base_url}/api/v1/search?{test_params}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        # Check if the dangerous parameter was processed
                        if "script" in test_params and "<script>" in response.text:
                            self.add_critical_issue(
                                f"HPP-{len(self.critical_issues)+1:03d}",
                                "Parameter pollution XSS",
                                "XSS via HTTP Parameter Pollution",
                                f"Send duplicate parameters: {test_params}",
                                "XSS payload reflected in response",
                                "Parameters sanitized or last value used safely",
                                "High"
                            )
                        elif "999" in test_params and response.text:
                            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                            if isinstance(data, dict) and data.get('total_count', 0) > 100:
                                self.add_critical_issue(
                                    f"HPP-{len(self.critical_issues)+1:03d}",
                                    "Parameter pollution bypass",
                                    "Validation bypass via parameter pollution",
                                    f"Send duplicate parameters: {test_params}",
                                    f"Large result set returned: {data.get('total_count')}",
                                    "Validation should prevent excessive results",
                                    "Medium"
                                )
                                
                except Exception as e:
                    print(f"   ℹ️  Parameter pollution test failed: {e}")
                    
    async def test_race_conditions(self):
        """Test for race condition vulnerabilities"""
        print("\n🏃 Testing Race Conditions...")
        
        async def concurrent_request(client, endpoint, params=None):
            """Helper for concurrent requests"""
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                return response.status_code, response.text[:100]
            except Exception:
                return None, None
                
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test concurrent requests to same resource
            tasks = [
                concurrent_request(client, "/api/v1/scholarships", {"limit": "1"})
                for _ in range(50)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results for inconsistencies
            valid_results = [r for r in results if isinstance(r, tuple) and r[0] is not None]
            status_codes = [r[0] for r in valid_results]
            response_bodies = [r[1] for r in valid_results]
            
            # Check for inconsistent responses
            unique_responses = set(response_bodies)
            if len(unique_responses) > 2:  # Allow for minor timing differences
                self.add_critical_issue(
                    "RACE-001",
                    "Race condition: concurrent requests",
                    "Inconsistent responses under concurrent load",
                    "Send 50 concurrent requests to /api/v1/scholarships",
                    f"Got {len(unique_responses)} different responses",
                    "Consistent responses under concurrent load",
                    "Medium"
                )
                
            # Check for unusual error patterns
            error_codes = [code for code in status_codes if code >= 400]
            if len(error_codes) > 10:
                self.add_critical_issue(
                    "RACE-002",
                    "Race condition: error handling",
                    "High error rate under concurrent load",
                    "Send 50 concurrent requests",
                    f"Got {len(error_codes)} error responses out of {len(status_codes)}",
                    "Stable error rate < 10%",
                    "Medium"
                )
                
    async def test_authorization_flaws(self):
        """Test for authorization bypass and privilege escalation"""
        print("\n🔑 Testing Authorization Flaws...")
        
        # Test endpoints that might have different access levels
        test_cases = [
            # Admin endpoints
            {"endpoint": "/admin", "expected_status": 404},
            {"endpoint": "/api/admin", "expected_status": 404},
            {"endpoint": "/api/v1/admin", "expected_status": 404},
            
            # Internal/debug endpoints
            {"endpoint": "/internal", "expected_status": 404},
            {"endpoint": "/debug", "expected_status": 404},
            {"endpoint": "/status/detailed", "expected_status": 404},
            
            # Configuration endpoints
            {"endpoint": "/config.json", "expected_status": 404},
            {"endpoint": "/api/config", "expected_status": 404},
            
            # Backup/temporary files
            {"endpoint": "/backup", "expected_status": 404},
            {"endpoint": "/tmp", "expected_status": 404},
            {"endpoint": "/.git", "expected_status": 404},
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for test in test_cases:
                try:
                    response = await client.get(f"{self.base_url}{test['endpoint']}")
                    
                    if response.status_code == 200:
                        self.add_critical_issue(
                            f"AUTHZ-{len(self.critical_issues)+1:03d}",
                            f"Authorization bypass: {test['endpoint']}",
                            f"Unauthorized access to {test['endpoint']}",
                            f"Access {test['endpoint']} without authentication",
                            f"HTTP {response.status_code}: Access granted",
                            f"HTTP {test['expected_status']} or access denied",
                            "High"
                        )
                        
                except Exception as e:
                    print(f"   ℹ️  Authorization test failed for {test['endpoint']}: {e}")
                    
    async def test_api_versioning_issues(self):
        """Test API versioning and backward compatibility issues"""
        print("\n📌 Testing API Versioning Issues...")
        
        version_tests = [
            "/api/v0/scholarships",    # Older version
            "/api/v2/scholarships",    # Newer version
            "/api/v1.1/scholarships",  # Sub-version
            "/api/v1.0/scholarships",  # Sub-version
            "/api/beta/scholarships",  # Beta version
            "/api/latest/scholarships", # Latest alias
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for version_endpoint in version_tests:
                try:
                    response = await client.get(f"{self.base_url}{version_endpoint}")
                    
                    if response.status_code == 200:
                        # Check if unintended version is accessible
                        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                        
                        if isinstance(data, dict) and 'scholarships' in data:
                            self.add_critical_issue(
                                f"VER-{len(self.critical_issues)+1:03d}",
                                f"API versioning: {version_endpoint}",
                                f"Unintended API version accessible",
                                f"Access {version_endpoint}",
                                f"HTTP 200: API version responds with data",
                                "HTTP 404 for unsupported versions",
                                "Low"
                            )
                            
                except Exception as e:
                    print(f"   ℹ️  API versioning test failed for {version_endpoint}: {e}")
                    
    async def test_state_management_bugs(self):
        """Test state management and session-related bugs"""
        print("\n🔄 Testing State Management...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test session fixation
            try:
                # First request
                response1 = await client.get(f"{self.base_url}/api/v1/scholarships")
                cookies1 = response1.cookies
                
                # Second request with same session
                response2 = await client.get(
                    f"{self.base_url}/api/v1/search",
                    cookies=cookies1
                )
                
                # Check if state persists inappropriately
                if response2.status_code == 200:
                    # Look for any session or state indicators in response
                    if "session" in response2.text.lower() or "state" in response2.text.lower():
                        self.add_critical_issue(
                            "STATE-001",
                            "State management",
                            "Potential session state leakage",
                            "Make requests and check for session persistence",
                            "Session information found in API responses",
                            "Stateless API without session leakage",
                            "Medium"
                        )
                        
            except Exception as e:
                print(f"   ℹ️  State management test failed: {e}")
                
    def generate_critical_report(self):
        """Generate focused critical issues report"""
        print("\n" + "="*60)
        print("🚨 CRITICAL ISSUES ANALYSIS REPORT")
        print("="*60)
        
        if not self.critical_issues:
            print("✅ No critical issues found in focused analysis")
            return
            
        # Severity summary
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for issue in self.critical_issues:
            severity_counts[issue["severity"]] += 1
            
        print(f"\n📊 CRITICAL FINDINGS SUMMARY:")
        print(f"   Total Critical Issues: {len(self.critical_issues)}")
        for severity, count in severity_counts.items():
            if count > 0:
                print(f"   {severity}: {count}")
                
        print(f"\n🔍 DETAILED CRITICAL FINDINGS:")
        print("-" * 60)
        
        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_issues = sorted(self.critical_issues, key=lambda x: severity_order[x["severity"]])
        
        for issue in sorted_issues:
            print(f"\nIssue ID: {issue['issue_id']}")
            print(f"Location: {issue['location']}")
            print(f"Description: {issue['description']}")
            print(f"Severity: {issue['severity']}")
            print(f"Steps to Reproduce: {issue['steps_to_reproduce']}")
            print(f"Observed Output: {issue['observed_output']}")
            print(f"Expected Output: {issue['expected_output']}")
            print("-" * 40)
            
        # Save to file
        with open("FOCUSED_CRITICAL_ISSUES_REPORT.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_critical_issues": len(self.critical_issues),
                    "severity_breakdown": severity_counts
                },
                "critical_issues": sorted_issues
            }, f, indent=2)
            
        print(f"\n💾 Critical issues report saved to: FOCUSED_CRITICAL_ISSUES_REPORT.json")

async def main():
    """Main execution"""
    analyzer = CriticalIssuesAnalyzer()
    await analyzer.run_focused_analysis()

if __name__ == "__main__":
    asyncio.run(main())