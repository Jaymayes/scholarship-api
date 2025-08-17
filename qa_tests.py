#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Scholarship Discovery & Search API
Senior QA Engineer Analysis - Issue Identification Only
"""

import json
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import traceback
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules for testing
from models.scholarship import Scholarship, EligibilityCriteria, SearchFilters, FieldOfStudy, ScholarshipType
from models.user import UserProfile, EligibilityCheck, RecommendationRequest
from services.scholarship_service import scholarship_service
from services.eligibility_service import eligibility_service
from services.search_service import search_service
from services.analytics_service import analytics_service
from data.scholarships import MOCK_SCHOLARSHIPS

class QATestSuite:
    """Comprehensive QA test suite to identify all bugs and issues"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.issues = []
        self.test_results = []
    
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
            "severity": severity
        }
        self.issues.append(issue)
        print(f"🐛 ISSUE {issue_id}: {description} [{severity}]")
    
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None, 
                         expected_status: int = 200) -> Dict[str, Any]:
        """Test API endpoints and capture responses"""
        try:
            url = f"{self.base_url}{endpoint}"
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = {
                "success": True,
                "status_code": response.status_code,
                "response": response.json() if response.content else None,
                "expected_status": expected_status
            }
            
            if response.status_code != expected_status:
                result["success"] = False
                
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        
        return result

    def test_model_validation(self):
        """Test Pydantic model validation edge cases"""
        print("\n🔍 Testing Model Validation...")
        
        # Test 1: Invalid GPA values
        try:
            invalid_profile = UserProfile(gpa=5.0)  # Above 4.0 limit
        except Exception as e:
            self.log_issue(
                "MDL001", 
                "models/user.py:9",
                "UserProfile allows GPA values above 4.0 maximum",
                "Create UserProfile with gpa=5.0",
                f"Exception: {e}",
                "Should reject GPA > 4.0",
                "Medium"
            )
        
        # Test 2: Negative scholarship amounts
        try:
            criteria = EligibilityCriteria()
            invalid_scholarship = Scholarship(
                id="test",
                name="Test",
                organization="Test Org",
                description="Test desc",
                amount=-1000.0,  # Negative amount
                max_awards=1,
                application_deadline=datetime.utcnow() + timedelta(days=30),
                scholarship_type=ScholarshipType.MERIT_BASED,
                eligibility_criteria=criteria,
                application_url="http://test.com"
            )
        except Exception as e:
            self.log_issue(
                "MDL002",
                "models/scholarship.py:51",
                "Scholarship model accepts negative amounts",
                "Create Scholarship with amount=-1000.0",
                f"Exception: {e}",
                "Should reject negative amounts",
                "High"
            )
        
        # Test 3: Empty required fields
        try:
            empty_scholarship = Scholarship(
                id="",  # Empty ID
                name="",  # Empty name
                organization="",
                description="",
                amount=1000.0,
                max_awards=1,
                application_deadline=datetime.utcnow(),
                scholarship_type=ScholarshipType.MERIT_BASED,
                eligibility_criteria=EligibilityCriteria(),
                application_url=""
            )
        except Exception as e:
            self.log_issue(
                "MDL003",
                "models/scholarship.py:46-58",
                "Scholarship model accepts empty required string fields",
                "Create Scholarship with empty id, name, organization, description",
                f"Exception: {e}",
                "Should reject empty required fields",
                "High"
            )

    def test_eligibility_service_edge_cases(self):
        """Test eligibility service with edge cases"""
        print("\n🔍 Testing Eligibility Service Edge Cases...")
        
        # Test 1: None/null user profile
        try:
            result = eligibility_service.check_eligibility(None, "sch_001")
            self.log_issue(
                "ELG001",
                "services/eligibility_service.py:12",
                "check_eligibility accepts None user_profile without proper validation",
                "Call check_eligibility(None, 'sch_001')",
                f"Result: {result}",
                "Should raise ValidationError or handle gracefully",
                "High"
            )
        except Exception as e:
            # This is expected behavior
            pass
        
        # Test 2: Invalid scholarship ID
        test_profile = UserProfile(id="test_user", gpa=3.5)
        result = eligibility_service.check_eligibility(test_profile, "invalid_id")
        if result.eligible:
            self.log_issue(
                "ELG002",
                "services/eligibility_service.py:16-24",
                "Eligibility check returns eligible=True for non-existent scholarship",
                "Call check_eligibility with invalid scholarship ID",
                f"Result: {result.dict()}",
                "Should return eligible=False with appropriate error reason",
                "Medium"
            )
        
        # Test 3: Extreme GPA values
        extreme_profile = UserProfile(id="test", gpa=0.0)
        result = eligibility_service.check_eligibility(extreme_profile, "sch_001")
        if result.match_score < 0 or result.match_score > 1:
            self.log_issue(
                "ELG003",
                "services/eligibility_service.py:146",
                "Match score calculation can exceed bounds [0.0, 1.0]",
                "Test eligibility with extreme GPA values",
                f"Match score: {result.match_score}",
                "Match score should be clamped between 0.0 and 1.0",
                "Medium"
            )

    def test_search_service_edge_cases(self):
        """Test search service edge cases"""
        print("\n🔍 Testing Search Service Edge Cases...")
        
        # Test 1: Empty search filters
        empty_filters = SearchFilters()
        result = scholarship_service.search_scholarships(empty_filters)
        
        if result.total_count == 0:
            self.log_issue(
                "SRC001",
                "services/scholarship_service.py:29",
                "Empty search filters return no results instead of all scholarships",
                "Search with default SearchFilters()",
                f"Total count: {result.total_count}",
                "Should return all scholarships when no filters applied",
                "Medium"
            )
        
        # Test 2: Invalid pagination values
        invalid_filters = SearchFilters(offset=-1, limit=0)
        try:
            result = scholarship_service.search_scholarships(invalid_filters)
            self.log_issue(
                "SRC002",
                "services/scholarship_service.py:107-111",
                "Search accepts invalid pagination parameters",
                "Search with offset=-1, limit=0",
                f"Result: {result.dict()}",
                "Should validate pagination parameters",
                "Medium"
            )
        except Exception as e:
            # Expected behavior
            pass
        
        # Test 3: SQL injection-like inputs
        malicious_filters = SearchFilters(keyword="'; DROP TABLE scholarships; --")
        result = scholarship_service.search_scholarships(malicious_filters)
        # This should be safe with current implementation, but worth testing

    def test_api_endpoints_comprehensive(self):
        """Comprehensive API endpoint testing"""
        print("\n🔍 Testing API Endpoints...")
        
        # Test 1: Root endpoint
        result = self.test_api_endpoint("GET", "/")
        if not result["success"]:
            self.log_issue(
                "API001",
                "main.py:32",
                "Root endpoint not accessible",
                "GET /",
                f"Error: {result.get('error', 'Unknown')}",
                "Should return API information",
                "High"
            )
        
        # Test 2: Health check
        result = self.test_api_endpoint("GET", "/health")
        if not result["success"]:
            self.log_issue(
                "API002",
                "main.py:42",
                "Health check endpoint not accessible",
                "GET /health",
                f"Error: {result.get('error', 'Unknown')}",
                "Should return health status",
                "High"
            )
        
        # Test 3: Invalid scholarship ID
        result = self.test_api_endpoint("GET", "/api/v1/scholarships/invalid_id", expected_status=404)
        if result["success"] and result["status_code"] != 404:
            self.log_issue(
                "API003",
                "routers/scholarships.py:149",
                "Invalid scholarship ID doesn't return 404",
                "GET /api/v1/scholarships/invalid_id",
                f"Status: {result['status_code']}",
                "Should return 404 Not Found",
                "Medium"
            )
        
        # Test 4: Malformed eligibility check payload
        malformed_payload = {
            "user_profile": {
                "invalid_field": "value"
            },
            "scholarship_id": "sch_001"
        }
        result = self.test_api_endpoint("POST", "/api/v1/scholarships/eligibility-check", 
                                      malformed_payload, expected_status=422)
        if result["success"] and result["status_code"] != 422:
            self.log_issue(
                "API004",
                "routers/scholarships.py:169",
                "Malformed eligibility check payload doesn't return proper validation error",
                "POST eligibility check with invalid payload",
                f"Status: {result['status_code']}",
                "Should return 422 Unprocessable Entity",
                "Medium"
            )
        
        # Test 5: Bulk eligibility check with too many IDs
        large_payload = {
            "user_profile": {
                "id": "test",
                "gpa": 3.5
            },
            "scholarship_ids": [f"sch_{i:03d}" for i in range(1, 101)]  # 100 IDs
        }
        result = self.test_api_endpoint("POST", "/api/v1/scholarships/bulk-eligibility-check",
                                      large_payload, expected_status=400)
        if result["success"] and result["status_code"] != 400:
            self.log_issue(
                "API005",
                "routers/scholarships.py:208-212",
                "Bulk eligibility check doesn't enforce 50 scholarship limit",
                "POST bulk eligibility with 100 scholarship IDs",
                f"Status: {result['status_code']}",
                "Should return 400 Bad Request",
                "Medium"
            )

    def test_data_consistency(self):
        """Test data consistency and integrity"""
        print("\n🔍 Testing Data Consistency...")
        
        # Test 1: Check for duplicate scholarship IDs
        scholarship_ids = [sch.id for sch in MOCK_SCHOLARSHIPS]
        duplicates = set([x for x in scholarship_ids if scholarship_ids.count(x) > 1])
        if duplicates:
            self.log_issue(
                "DAT001",
                "data/scholarships.py",
                f"Duplicate scholarship IDs found: {duplicates}",
                "Check MOCK_SCHOLARSHIPS for duplicate IDs",
                f"Duplicates: {list(duplicates)}",
                "All scholarship IDs should be unique",
                "High"
            )
        
        # Test 2: Check for past deadlines
        current_date = datetime.utcnow()
        past_deadlines = [sch for sch in MOCK_SCHOLARSHIPS if sch.application_deadline < current_date]
        if past_deadlines:
            self.log_issue(
                "DAT002",
                "data/scholarships.py",
                f"Found {len(past_deadlines)} scholarships with past deadlines",
                "Check application_deadline fields in MOCK_SCHOLARSHIPS",
                f"Past deadlines count: {len(past_deadlines)}",
                "All scholarships should have future deadlines",
                "Low"
            )
        
        # Test 3: Check for invalid URLs
        invalid_urls = []
        for sch in MOCK_SCHOLARSHIPS:
            if not sch.application_url.startswith(('http://', 'https://')):
                invalid_urls.append(sch.id)
        if invalid_urls:
            self.log_issue(
                "DAT003",
                "data/scholarships.py",
                f"Invalid application URLs in scholarships: {invalid_urls}",
                "Check application_url fields for proper URL format",
                f"Invalid URLs in: {invalid_urls}",
                "All URLs should start with http:// or https://",
                "Medium"
            )

    def test_analytics_service(self):
        """Test analytics service edge cases"""
        print("\n🔍 Testing Analytics Service...")
        
        # Test 1: Analytics with no interactions
        summary = analytics_service.get_analytics_summary(days=1)
        if summary["total_interactions"] < 0:
            self.log_issue(
                "ANL001",
                "services/analytics_service.py:74",
                "Analytics summary returns negative interaction count",
                "Call get_analytics_summary() with no prior interactions",
                f"Total interactions: {summary['total_interactions']}",
                "Should return 0 or positive count",
                "Medium"
            )
        
        # Test 2: User analytics for non-existent user
        user_analytics = analytics_service.get_user_analytics("non_existent_user", days=30)
        if user_analytics["total_interactions"] != 0:
            self.log_issue(
                "ANL002",
                "services/analytics_service.py:153",
                "User analytics doesn't handle non-existent users properly",
                "Call get_user_analytics('non_existent_user')",
                f"Result: {user_analytics}",
                "Should return zero interactions for non-existent user",
                "Low"
            )

    def test_performance_and_limits(self):
        """Test performance and system limits"""
        print("\n🔍 Testing Performance and Limits...")
        
        # Test 1: Large keyword search
        large_keyword = "x" * 1000  # 1000 character keyword
        filters = SearchFilters(keyword=large_keyword)
        try:
            result = scholarship_service.search_scholarships(filters)
            # Check if this causes performance issues
        except Exception as e:
            self.log_issue(
                "PER001",
                "services/scholarship_service.py:37-44",
                "Large keyword search causes exception",
                "Search with 1000-character keyword",
                f"Exception: {e}",
                "Should handle large keywords gracefully",
                "Medium"
            )
        
        # Test 2: Concurrent API requests simulation
        # This would require threading, simplified for this test

    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        print("\n🔍 Testing Security Vulnerabilities...")
        
        # Test 1: Check for exposed sensitive information
        result = self.test_api_endpoint("GET", "/api/v1/scholarships/sch_001")
        if result["success"] and "password" in str(result["response"]).lower():
            self.log_issue(
                "SEC001",
                "routers/scholarships.py:149",
                "Scholarship endpoint exposes sensitive information",
                "GET /api/v1/scholarships/sch_001 and check for sensitive data",
                "Response contains sensitive information",
                "Should not expose passwords or sensitive data",
                "Critical"
            )
        
        # Test 2: CORS configuration check
        # This would require checking response headers

    def run_all_tests(self):
        """Execute all test suites"""
        print("🚀 Starting Comprehensive QA Analysis...")
        print("=" * 60)
        
        try:
            self.test_model_validation()
            self.test_eligibility_service_edge_cases()
            self.test_search_service_edge_cases()
            self.test_api_endpoints_comprehensive()
            self.test_data_consistency()
            self.test_analytics_service()
            self.test_performance_and_limits()
            self.test_security_vulnerabilities()
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            traceback.print_exc()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        print("\n" + "=" * 60)
        print("📊 QA ANALYSIS REPORT")
        print("=" * 60)
        
        if not self.issues:
            print("✅ No issues identified in the codebase!")
            return
        
        # Group by severity
        critical = [i for i in self.issues if i["severity"] == "Critical"]
        high = [i for i in self.issues if i["severity"] == "High"]
        medium = [i for i in self.issues if i["severity"] == "Medium"]
        low = [i for i in self.issues if i["severity"] == "Low"]
        
        print(f"📈 SUMMARY:")
        print(f"   Critical: {len(critical)}")
        print(f"   High:     {len(high)}")
        print(f"   Medium:   {len(medium)}")
        print(f"   Low:      {len(low)}")
        print(f"   Total:    {len(self.issues)}")
        print()
        
        # Detailed issues
        for issue in self.issues:
            print(f"🐛 {issue['issue_id']} - {issue['severity'].upper()}")
            print(f"   Location: {issue['location']}")
            print(f"   Description: {issue['description']}")
            print(f"   Steps: {issue['steps_to_reproduce']}")
            print(f"   Observed: {issue['observed_output']}")
            print(f"   Expected: {issue['expected_output']}")
            print()
        
        return self.issues


if __name__ == "__main__":
    qa_suite = QATestSuite()
    issues = qa_suite.run_all_tests()
    
    # Save detailed report to file
    with open("qa_report.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_issues": len(issues),
            "issues": issues
        }, f, indent=2)
    
    print(f"📋 Detailed report saved to qa_report.json")