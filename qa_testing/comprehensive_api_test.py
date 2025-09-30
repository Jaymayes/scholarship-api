#!/usr/bin/env python3
"""
Comprehensive QA Testing Suite for ScholarshipAI API
Phase-gated testing with detailed reporting
"""

import requests
import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class TestPhase(Enum):
    DISCOVERY = "Phase 0: Discovery & Smoke Test"
    FUNCTIONAL = "Phase 1: Functional Correctness"
    PERFORMANCE = "Phase 2: Performance & Reliability"
    SECURITY = "Phase 3: Security & Compliance"
    COMMAND_CENTER = "Phase 4: Command Center Integration"
    REGRESSION = "Phase 5: Regression & Self-Check"

class TestStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"
    SKIP = "⏭️ SKIP"
    BLOCKED = "🚫 BLOCKED"

@dataclass
class TestResult:
    endpoint: str
    test_name: str
    status: TestStatus
    response_time_ms: float
    status_code: int
    expected_code: int
    details: str
    error: str = ""
    trace_id: str = ""

class ScholarshipAPITester:
    def __init__(self, base_url: str = "https://scholarship-api-jamarrlmayes.replit.app"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token: str = ""
        self.test_results: List[TestResult] = []
        
        # Mock user credentials
        self.test_users = {
            "admin": {"username": "admin", "password": "admin123"},
            "partner": {"username": "partner", "password": "partner123"},
            "readonly": {"username": "readonly", "password": "readonly123"}
        }
        
        # SLO Targets
        self.slo_targets = {
            "uptime_target": 99.9,
            "p95_latency_target_ms": 120,
            "p99_latency_target_ms": 200
        }
    
    def authenticate(self, user_type: str = "admin") -> bool:
        """Authenticate and obtain JWT token"""
        print(f"🔐 Authenticating as {user_type}...")
        
        user_creds = self.test_users.get(user_type)
        if not user_creds:
            print(f"❌ Unknown user type: {user_type}")
            return False
        
        try:
            # Try OAuth2 login endpoint
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data={
                    "username": user_creds["username"],
                    "password": user_creds["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                print(f"✅ Authenticated successfully as {user_type}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_endpoint(
        self, 
        method: str,
        endpoint: str,
        test_name: str,
        expected_code: int = 200,
        **kwargs
    ) -> TestResult:
        """Test a single endpoint and record results"""
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.request(method, url, **kwargs)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract trace_id if available
            trace_id = response.headers.get("x-trace-id", response.json().get("trace_id", "") if response.headers.get("content-type", "").startswith("application/json") else "")
            
            status = TestStatus.PASS if response.status_code == expected_code else TestStatus.FAIL
            details = f"Response time: {response_time_ms:.0f}ms"
            
            result = TestResult(
                endpoint=endpoint,
                test_name=test_name,
                status=status,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                expected_code=expected_code,
                details=details,
                trace_id=trace_id
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            result = TestResult(
                endpoint=endpoint,
                test_name=test_name,
                status=TestStatus.FAIL,
                response_time_ms=response_time_ms,
                status_code=0,
                expected_code=expected_code,
                details="Exception occurred",
                error=str(e)
            )
        
        self.test_results.append(result)
        return result
    
    def phase1_functional_tests(self):
        """Phase 1: Functional Correctness Testing"""
        print("\n" + "="*80)
        print("🧪 PHASE 1: FUNCTIONAL CORRECTNESS TESTING")
        print("="*80)
        
        # Health endpoints
        print("\n📊 Testing Health & Status Endpoints...")
        self.test_endpoint("GET", "/health", "Health check endpoint")
        self.test_endpoint("GET", "/api", "API info endpoint")
        
        # Authentication tests
        print("\n🔐 Testing Authentication Endpoints...")
        auth_result = self.test_endpoint(
            "POST", 
            "/api/v1/auth/login-simple",
            "Simple login endpoint",
            expected_code=200,
            json={"username": "admin", "password": "admin123"}
        )
        
        # Search tests (requires auth)
        if self.auth_token:
            print("\n🔍 Testing Search Endpoints (Authenticated)...")
            
            # Basic search
            self.test_endpoint(
                "GET",
                "/api/v1/search?q=engineering",
                "Basic search query - engineering"
            )
            
            # Search with pagination
            self.test_endpoint(
                "GET",
                "/api/v1/search?q=stem&page=1&page_size=10",
                "Search with pagination"
            )
            
            # Empty query handling
            self.test_endpoint(
                "GET",
                "/api/v1/search?q=",
                "Empty search query",
                expected_code=400
            )
            
            # Scholarships endpoint
            print("\n📚 Testing Scholarship Endpoints...")
            self.test_endpoint(
                "GET",
                "/api/v1/scholarships",
                "List all scholarships"
            )
            
            # Eligibility check
            print("\n✅ Testing Eligibility Endpoints...")
            self.test_endpoint(
                "POST",
                "/api/v1/eligibility/check",
                "Eligibility check",
                json={
                    "user_profile": {
                        "gpa": 3.5,
                        "major": "Computer Science",
                        "year": "Junior"
                    },
                    "scholarship_id": "sch_001"
                }
            )
        
        # Rate limiting test
        print("\n⏱️ Testing Rate Limiting...")
        for i in range(5):
            result = self.test_endpoint(
                "GET",
                f"/health",
                f"Rate limit test {i+1}/5"
            )
            if result.status_code == 429:
                print("✅ Rate limiting triggered as expected")
                break
    
    def phase2_performance_tests(self):
        """Phase 2: Non-functional Testing (Performance & Reliability)"""
        print("\n" + "="*80)
        print("⚡ PHASE 2: PERFORMANCE & RELIABILITY TESTING")
        print("="*80)
        
        if not self.auth_token:
            print("⚠️ Skipping performance tests - authentication required")
            return
        
        # Latency baseline
        print("\n📊 Measuring Latency Baseline...")
        latencies = []
        
        for i in range(20):
            start = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/search?q=test")
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
            
            if i % 5 == 0:
                print(f"  Request {i+1}/20: {latency_ms:.0f}ms")
        
        # Calculate percentiles
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        
        print(f"\n📈 Latency Distribution:")
        print(f"  P50: {p50:.0f}ms")
        print(f"  P95: {p95:.0f}ms (Target: ≤{self.slo_targets['p95_latency_target_ms']}ms)")
        print(f"  P99: {p99:.0f}ms (Target: ≤{self.slo_targets['p99_latency_target_ms']}ms)")
        
        p95_pass = p95 <= self.slo_targets['p95_latency_target_ms']
        print(f"  P95 SLO: {'✅ PASS' if p95_pass else '❌ FAIL'}")
        
        # Concurrent request test (light load)
        print("\n🔄 Testing Concurrent Requests (light load)...")
        print("  Simulating 5 concurrent users...")
        
        import concurrent.futures
        
        def make_request(i):
            start = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/search?q=concurrent_test_{i}")
            return time.time() - start, response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, range(10)))
        
        concurrent_latencies = [r[0] * 1000 for r in results]
        success_count = sum(1 for r in results if r[1] == 200)
        
        print(f"  Successful requests: {success_count}/10")
        print(f"  Avg latency under concurrency: {statistics.mean(concurrent_latencies):.0f}ms")
    
    def phase3_security_tests(self):
        """Phase 3: Security & Compliance Testing"""
        print("\n" + "="*80)
        print("🛡️ PHASE 3: SECURITY & COMPLIANCE TESTING")
        print("="*80)
        
        # Test without authentication
        print("\n🔐 Testing Authentication Requirements...")
        no_auth_session = requests.Session()
        
        response = no_auth_session.get(f"{self.base_url}/api/v1/search?q=test")
        if response.status_code == 403:
            print("✅ Unauthenticated request properly blocked")
        else:
            print(f"❌ Unauthenticated request allowed: {response.status_code}")
        
        # SQL Injection tests (should be blocked by WAF)
        print("\n💉 Testing SQL Injection Protection...")
        sqli_payloads = [
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT NULL--"
        ]
        
        for payload in sqli_payloads:
            response = self.session.get(
                f"{self.base_url}/api/v1/search",
                params={"q": payload}
            )
            if response.status_code == 403 and "WAF" in response.text:
                print(f"  ✅ Blocked: {payload[:20]}...")
            else:
                print(f"  ⚠️ Not blocked: {payload[:20]}...")
        
        # XSS tests
        print("\n🔗 Testing XSS Protection...")
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            response = self.session.get(
                f"{self.base_url}/api/v1/search",
                params={"q": payload}
            )
            if response.status_code == 403 or payload not in response.text:
                print(f"  ✅ XSS protected")
            else:
                print(f"  ⚠️ XSS not sanitized")
        
        # Security headers check
        print("\n🔒 Validating Security Headers...")
        response = self.session.get(f"{self.base_url}/health")
        
        required_headers = {
            "Strict-Transport-Security": "HSTS",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": "CSP"
        }
        
        for header, name in required_headers.items():
            if header in response.headers:
                print(f"  ✅ {name}: {response.headers[header][:50]}")
            else:
                print(f"  ❌ {name}: Missing")
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == TestStatus.PASS)
        failed_tests = sum(1 for r in self.test_results if r.status == TestStatus.FAIL)
        
        report = f"""
# COMPREHENSIVE QA TEST REPORT
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**API Endpoint:** {self.base_url}

## 📊 EXECUTIVE SUMMARY

**Total Tests Executed:** {total_tests}  
**Passed:** {passed_tests} ({passed_tests/total_tests*100:.1f}%)  
**Failed:** {failed_tests} ({failed_tests/total_tests*100:.1f}%)

## 🧪 DETAILED TEST RESULTS

"""
        
        for result in self.test_results:
            report += f"""
### {result.test_name}
- **Endpoint:** `{result.endpoint}`
- **Status:** {result.status.value}
- **Response Time:** {result.response_time_ms:.0f}ms
- **Status Code:** {result.status_code} (Expected: {result.expected_code})
- **Details:** {result.details}
"""
            if result.trace_id:
                report += f"- **Trace ID:** {result.trace_id}\n"
            if result.error:
                report += f"- **Error:** {result.error}\n"
        
        return report
    
    def run_all_phases(self):
        """Execute all test phases"""
        
        print("\n" + "="*80)
        print("🚀 STARTING COMPREHENSIVE API TESTING")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate("admin"):
            print("❌ Authentication failed - aborting tests")
            return
        
        # Run test phases
        self.phase1_functional_tests()
        self.phase2_performance_tests()
        self.phase3_security_tests()
        
        # Generate and save report
        report = self.generate_report()
        
        with open("test_results_report.md", "w") as f:
            f.write(report)
        
        print("\n" + "="*80)
        print("✅ TESTING COMPLETE")
        print("="*80)
        print(f"\n📊 Report saved to: qa_testing/test_results_report.md")
        
        # Print summary
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == TestStatus.PASS)
        print(f"\n📈 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

if __name__ == "__main__":
    tester = ScholarshipAPITester()
    tester.run_all_phases()
