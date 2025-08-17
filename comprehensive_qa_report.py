#!/usr/bin/env python3
"""
Comprehensive QA Analysis and Testing Suite
Senior QA Engineer Report Generation
"""

import os
import sys
import json
import traceback
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytest
import asyncio
from sqlalchemy import text
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    from models.database import SessionLocal, get_db
    from services.scholarship_service import ScholarshipService
    from services.eligibility_service import EligibilityService
    from models.scholarship import Scholarship
    from config.settings import settings
except ImportError as e:
    print(f"Critical Import Error: {e}")
    sys.exit(1)

class QAReportGenerator:
    """Comprehensive QA Analysis and Bug Reporting System"""
    
    def __init__(self):
        self.issues = []
        self.test_results = {}
        self.client = TestClient(app)
        self.base_url = "http://localhost:5000"
        
    def add_issue(self, issue_id: str, location: str, description: str, 
                  steps_to_reproduce: str, observed_output: str, 
                  expected_output: str, severity: str, category: str = "Bug"):
        """Add an issue to the report"""
        self.issues.append({
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_basic_connectivity(self):
        """Test basic API connectivity and health"""
        print("🔍 Testing Basic Connectivity...")
        
        try:
            # Test root endpoint
            response = self.client.get("/")
            if response.status_code != 200:
                self.add_issue(
                    "CONN-001",
                    "main.py root endpoint",
                    "Root endpoint returns non-200 status code",
                    "Send GET request to /",
                    f"Status: {response.status_code}, Response: {response.text}",
                    "Status: 200 with valid JSON response",
                    "High"
                )
            
            # Test health endpoints
            health_response = self.client.get("/healthz")
            if health_response.status_code != 200:
                self.add_issue(
                    "HEALTH-001",
                    "routers/health.py /healthz",
                    "Liveness probe endpoint failing",
                    "Send GET request to /healthz",
                    f"Status: {health_response.status_code}",
                    "Status: 200 with {'status': 'ok'}",
                    "Critical"
                )
                
        except Exception as e:
            self.add_issue(
                "CONN-002",
                "FastAPI application startup",
                "Application fails to start or respond",
                "Start FastAPI application and send basic requests",
                f"Exception: {str(e)}",
                "Application starts successfully and responds to requests",
                "Critical"
            )
    
    def test_authentication_system(self):
        """Test authentication and authorization"""
        print("🔍 Testing Authentication System...")
        
        try:
            # Test login with invalid credentials
            invalid_login = self.client.post(
                "/api/v1/auth/login-simple",
                json={"username": "invalid", "password": "invalid"}
            )
            
            if invalid_login.status_code != 401:
                self.add_issue(
                    "AUTH-001",
                    "routers/auth.py login endpoint",
                    "Invalid credentials don't return 401 status",
                    "POST to /api/v1/auth/login-simple with invalid credentials",
                    f"Status: {invalid_login.status_code}",
                    "Status: 401 Unauthorized",
                    "Medium"
                )
            
            # Test login with valid credentials
            valid_login = self.client.post(
                "/api/v1/auth/login-simple",
                json={"username": "admin", "password": "admin123"}
            )
            
            if valid_login.status_code != 200:
                self.add_issue(
                    "AUTH-002",
                    "routers/auth.py login endpoint",
                    "Valid credentials don't return 200 status",
                    "POST to /api/v1/auth/login-simple with admin/admin123",
                    f"Status: {valid_login.status_code}, Response: {valid_login.text}",
                    "Status: 200 with access_token",
                    "High"
                )
                return None
            
            token_data = valid_login.json()
            if "access_token" not in token_data:
                self.add_issue(
                    "AUTH-003",
                    "routers/auth.py login response",
                    "Login response missing access_token",
                    "Successful login should return token",
                    f"Response: {token_data}",
                    "Response includes 'access_token' field",
                    "High"
                )
                return None
                
            return token_data["access_token"]
            
        except Exception as e:
            self.add_issue(
                "AUTH-004",
                "routers/auth.py authentication system",
                "Authentication system throws unexpected exception",
                "Attempt to authenticate with API",
                f"Exception: {str(e)}\nTraceback: {traceback.format_exc()}",
                "Authentication works without exceptions",
                "Critical"
            )
            return None
    
    def test_database_integration(self):
        """Test database connectivity and operations"""
        print("🔍 Testing Database Integration...")
        
        try:
            db = SessionLocal()
            
            # Test basic database connectivity
            try:
                result = db.execute(text("SELECT 1"))
                result.fetchone()
            except Exception as e:
                self.add_issue(
                    "DB-001",
                    "models/database.py database connection",
                    "Database connection fails",
                    "Execute basic SELECT 1 query",
                    f"Exception: {str(e)}",
                    "Query executes successfully",
                    "Critical"
                )
                return
            
            # Test scholarships table
            try:
                scholarship_count = db.execute(text("SELECT COUNT(*) FROM scholarships")).scalar()
                if scholarship_count == 0:
                    self.add_issue(
                        "DB-002",
                        "data/scholarship_data.py",
                        "No scholarships found in database",
                        "Query scholarships table for count",
                        f"Count: {scholarship_count}",
                        "Count > 0 (expected 15 scholarships)",
                        "Medium"
                    )
            except Exception as e:
                self.add_issue(
                    "DB-003",
                    "models/database.py scholarships table",
                    "Scholarships table query fails",
                    "SELECT COUNT(*) FROM scholarships",
                    f"Exception: {str(e)}",
                    "Query executes successfully",
                    "High"
                )
            
            # Test interactions table
            try:
                interaction_count = db.execute(text("SELECT COUNT(*) FROM interactions")).scalar()
                print(f"Interactions table has {interaction_count} records")
            except Exception as e:
                self.add_issue(
                    "DB-004",
                    "models/interaction.py interactions table",
                    "Interactions table query fails",
                    "SELECT COUNT(*) FROM interactions",
                    f"Exception: {str(e)}",
                    "Query executes successfully",
                    "Medium"
                )
            
            db.close()
            
        except Exception as e:
            self.add_issue(
                "DB-005",
                "models/database.py SessionLocal",
                "Database session creation fails",
                "Create database session using SessionLocal()",
                f"Exception: {str(e)}",
                "Session created successfully",
                "Critical"
            )
    
    def test_scholarship_endpoints(self, token: Optional[str] = None):
        """Test scholarship-related endpoints"""
        print("🔍 Testing Scholarship Endpoints...")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # Test get all scholarships
        try:
            scholarships_response = self.client.get("/api/v1/scholarships", headers=headers)
            
            if scholarships_response.status_code != 200:
                self.add_issue(
                    "SCHOLAR-001",
                    "routers/scholarships.py get_scholarships",
                    "Get scholarships endpoint returns non-200 status",
                    "GET /api/v1/scholarships",
                    f"Status: {scholarships_response.status_code}, Response: {scholarships_response.text}",
                    "Status: 200 with scholarship list",
                    "High"
                )
            else:
                data = scholarships_response.json()
                if not isinstance(data, list):
                    self.add_issue(
                        "SCHOLAR-002",
                        "routers/scholarships.py get_scholarships response",
                        "Scholarships endpoint doesn't return a list",
                        "GET /api/v1/scholarships and check response type",
                        f"Response type: {type(data)}, Data: {data}",
                        "Response should be a list of scholarships",
                        "Medium"
                    )
                elif len(data) == 0:
                    self.add_issue(
                        "SCHOLAR-003",
                        "services/scholarship_service.py",
                        "No scholarships returned from API",
                        "GET /api/v1/scholarships",
                        "Empty list returned",
                        "List of 15 scholarships",
                        "Medium"
                    )
        
        except Exception as e:
            self.add_issue(
                "SCHOLAR-004",
                "routers/scholarships.py",
                "Scholarships endpoint throws unexpected exception",
                "GET /api/v1/scholarships",
                f"Exception: {str(e)}\nTraceback: {traceback.format_exc()}",
                "Endpoint responds without exceptions",
                "High"
            )
        
        # Test search functionality
        try:
            search_response = self.client.get(
                "/api/v1/scholarships/search",
                params={"q": "engineering", "limit": 5},
                headers=headers
            )
            
            if search_response.status_code != 200:
                self.add_issue(
                    "SEARCH-001",
                    "routers/scholarships.py search_scholarships",
                    "Search endpoint returns non-200 status",
                    "GET /api/v1/scholarships/search?q=engineering&limit=5",
                    f"Status: {search_response.status_code}",
                    "Status: 200 with search results",
                    "High"
                )
        
        except Exception as e:
            self.add_issue(
                "SEARCH-002",
                "routers/scholarships.py search endpoint",
                "Search endpoint throws unexpected exception",
                "GET /api/v1/scholarships/search?q=engineering",
                f"Exception: {str(e)}",
                "Search completes without exceptions",
                "High"
            )
        
        # Test individual scholarship retrieval
        try:
            individual_response = self.client.get(
                "/api/v1/scholarships/merit-excellence-scholarship",
                headers=headers
            )
            
            if individual_response.status_code not in [200, 404]:
                self.add_issue(
                    "SCHOLAR-005",
                    "routers/scholarships.py get_scholarship",
                    "Individual scholarship endpoint returns unexpected status",
                    "GET /api/v1/scholarships/merit-excellence-scholarship",
                    f"Status: {individual_response.status_code}",
                    "Status: 200 (found) or 404 (not found)",
                    "Medium"
                )
        
        except Exception as e:
            self.add_issue(
                "SCHOLAR-006",
                "routers/scholarships.py get_scholarship",
                "Individual scholarship endpoint throws exception",
                "GET /api/v1/scholarships/merit-excellence-scholarship",
                f"Exception: {str(e)}",
                "Endpoint responds without exceptions",
                "Medium"
            )
    
    def test_eligibility_system(self, token: Optional[str] = None):
        """Test eligibility checking functionality"""
        print("🔍 Testing Eligibility System...")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # Test eligibility check endpoint
        try:
            eligibility_payload = {
                "user_profile": {
                    "gpa": 3.5,
                    "grade_level": "undergraduate",
                    "field_of_study": "engineering",
                    "citizenship": "US",
                    "state_of_residence": "CA",
                    "age": 20,
                    "financial_need": True
                },
                "scholarship_ids": ["merit-excellence-scholarship"]
            }
            
            eligibility_response = self.client.post(
                "/api/v1/scholarships/eligibility/check",
                json=eligibility_payload,
                headers=headers
            )
            
            if eligibility_response.status_code != 200:
                self.add_issue(
                    "ELIGIBILITY-001",
                    "routers/scholarships.py check_eligibility",
                    "Eligibility check endpoint returns non-200 status",
                    f"POST /api/v1/scholarships/eligibility/check with payload: {eligibility_payload}",
                    f"Status: {eligibility_response.status_code}, Response: {eligibility_response.text}",
                    "Status: 200 with eligibility results",
                    "High"
                )
            else:
                data = eligibility_response.json()
                if not isinstance(data, dict) or "results" not in data:
                    self.add_issue(
                        "ELIGIBILITY-002",
                        "services/eligibility_service.py",
                        "Eligibility response missing 'results' field",
                        "Check eligibility response structure",
                        f"Response: {data}",
                        "Response should contain 'results' field",
                        "Medium"
                    )
        
        except Exception as e:
            self.add_issue(
                "ELIGIBILITY-003",
                "routers/scholarships.py or services/eligibility_service.py",
                "Eligibility check throws unexpected exception",
                "POST eligibility check with valid payload",
                f"Exception: {str(e)}\nTraceback: {traceback.format_exc()}",
                "Eligibility check completes without exceptions",
                "High"
            )
    
    def test_edge_cases_and_input_validation(self, token: Optional[str] = None):
        """Test edge cases and input validation"""
        print("🔍 Testing Edge Cases and Input Validation...")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # Test with extremely long query string
        try:
            long_query = "a" * 10000  # 10k character query
            long_search_response = self.client.get(
                "/api/v1/scholarships/search",
                params={"q": long_query},
                headers=headers
            )
            
            if long_search_response.status_code == 500:
                self.add_issue(
                    "EDGE-001",
                    "routers/scholarships.py search validation",
                    "Long query string causes internal server error",
                    f"Search with {len(long_query)} character query",
                    f"Status: 500, Server Error",
                    "Status: 400 (bad request) or graceful handling",
                    "Medium"
                )
        
        except Exception as e:
            self.add_issue(
                "EDGE-002",
                "routers/scholarships.py search endpoint",
                "Long query causes unexpected exception",
                "Search with very long query string",
                f"Exception: {str(e)}",
                "Graceful error handling or input validation",
                "Medium"
            )
        
        # Test with special characters
        try:
            special_chars_query = "'; DROP TABLE scholarships; --"
            sql_injection_response = self.client.get(
                "/api/v1/scholarships/search",
                params={"q": special_chars_query},
                headers=headers
            )
            
            # Should not return 500 error - should handle gracefully
            if sql_injection_response.status_code == 500:
                self.add_issue(
                    "SECURITY-001",
                    "routers/scholarships.py search input validation",
                    "Special characters in search query cause server error",
                    f"Search with SQL injection attempt: {special_chars_query}",
                    "Status: 500, Internal Server Error",
                    "Graceful handling with proper input sanitization",
                    "High"
                )
        
        except Exception as e:
            self.add_issue(
                "SECURITY-002",
                "routers/scholarships.py input validation",
                "SQL injection attempt causes unexpected exception",
                "Search with SQL injection characters",
                f"Exception: {str(e)}",
                "Proper input validation and sanitization",
                "High"
            )
        
        # Test with null/empty inputs in eligibility check
        try:
            null_eligibility_payload = {
                "user_profile": {
                    "gpa": None,
                    "grade_level": "",
                    "field_of_study": None,
                    "citizenship": "",
                    "state_of_residence": None,
                    "age": None,
                    "financial_need": None
                },
                "scholarship_ids": []
            }
            
            null_response = self.client.post(
                "/api/v1/scholarships/eligibility/check",
                json=null_eligibility_payload,
                headers=headers
            )
            
            if null_response.status_code == 500:
                self.add_issue(
                    "EDGE-003",
                    "services/eligibility_service.py null handling",
                    "Null values in eligibility check cause server error",
                    f"Eligibility check with null payload: {null_eligibility_payload}",
                    "Status: 500, Internal Server Error",
                    "Status: 400 with validation error or graceful handling",
                    "Medium"
                )
        
        except Exception as e:
            self.add_issue(
                "EDGE-004",
                "services/eligibility_service.py",
                "Null values cause unexpected exception in eligibility check",
                "Eligibility check with null/empty values",
                f"Exception: {str(e)}",
                "Proper null value handling and validation",
                "Medium"
            )
    
    def test_rate_limiting(self, token: Optional[str] = None):
        """Test rate limiting functionality"""
        print("🔍 Testing Rate Limiting...")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        try:
            # Send many requests rapidly to test rate limiting
            responses = []
            for i in range(50):  # Send 50 requests rapidly
                response = self.client.get("/api/v1/scholarships", headers=headers)
                responses.append(response.status_code)
                if response.status_code == 429:  # Rate limited
                    break
            
            # Check if rate limiting is working
            if 429 not in responses:
                self.add_issue(
                    "RATE-001",
                    "middleware/rate_limiting.py",
                    "Rate limiting not enforced under load",
                    "Send 50 rapid requests to /api/v1/scholarships",
                    f"All responses: {set(responses)}",
                    "At least some requests should return 429 (Too Many Requests)",
                    "Low"  # Low severity as it might be configured for high limits
                )
        
        except Exception as e:
            self.add_issue(
                "RATE-002",
                "middleware/rate_limiting.py",
                "Rate limiting middleware causes unexpected exception",
                "Send multiple rapid requests",
                f"Exception: {str(e)}",
                "Rate limiting works without exceptions",
                "Medium"
            )
    
    def test_observability_features(self):
        """Test observability and monitoring features"""
        print("🔍 Testing Observability Features...")
        
        # Test metrics endpoint
        try:
            metrics_response = self.client.get("/metrics")
            if metrics_response.status_code != 200:
                self.add_issue(
                    "OBS-001",
                    "observability/metrics.py metrics endpoint",
                    "Metrics endpoint not accessible",
                    "GET /metrics",
                    f"Status: {metrics_response.status_code}",
                    "Status: 200 with Prometheus metrics",
                    "Medium"
                )
            elif "# HELP" not in metrics_response.text:
                self.add_issue(
                    "OBS-002",
                    "observability/metrics.py metrics format",
                    "Metrics endpoint doesn't return Prometheus format",
                    "GET /metrics and check response format",
                    f"Response doesn't contain '# HELP'",
                    "Response should be in Prometheus format",
                    "Low"
                )
        
        except Exception as e:
            self.add_issue(
                "OBS-003",
                "observability/metrics.py",
                "Metrics endpoint throws unexpected exception",
                "GET /metrics",
                f"Exception: {str(e)}",
                "Metrics endpoint responds without exceptions",
                "Medium"
            )
        
        # Test readiness probe
        try:
            readiness_response = self.client.get("/readyz")
            if readiness_response.status_code not in [200, 503]:
                self.add_issue(
                    "OBS-004",
                    "routers/health.py readiness probe",
                    "Readiness probe returns unexpected status",
                    "GET /readyz",
                    f"Status: {readiness_response.status_code}",
                    "Status: 200 (ready) or 503 (not ready)",
                    "Medium"
                )
        
        except Exception as e:
            self.add_issue(
                "OBS-005",
                "routers/health.py",
                "Readiness probe throws unexpected exception",
                "GET /readyz",
                f"Exception: {str(e)}",
                "Readiness probe responds without exceptions",
                "Medium"
            )
        
        # Test X-Request-ID header presence
        try:
            response = self.client.get("/")
            if "X-Request-ID" not in response.headers:
                self.add_issue(
                    "OBS-006",
                    "middleware/request_id.py",
                    "X-Request-ID header missing from responses",
                    "Send any request and check response headers",
                    f"Headers: {dict(response.headers)}",
                    "Response should include X-Request-ID header",
                    "Low"
                )
        
        except Exception as e:
            self.add_issue(
                "OBS-007",
                "middleware/request_id.py",
                "Request ID middleware causes unexpected exception",
                "Send request and check for X-Request-ID header",
                f"Exception: {str(e)}",
                "Request ID middleware works without exceptions",
                "Medium"
            )
    
    def test_configuration_and_environment(self):
        """Test configuration and environment setup"""
        print("🔍 Testing Configuration and Environment...")
        
        try:
            # Test if required environment variables are set
            required_vars = ["DATABASE_URL"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.add_issue(
                    "CONFIG-001",
                    "config/settings.py environment variables",
                    "Required environment variables are missing",
                    f"Check for environment variables: {required_vars}",
                    f"Missing variables: {missing_vars}",
                    "All required environment variables should be set",
                    "High"
                )
            
            # Test settings loading
            try:
                from config.settings import settings
                if not hasattr(settings, 'database_url'):
                    self.add_issue(
                        "CONFIG-002",
                        "config/settings.py settings class",
                        "Settings object missing database_url attribute",
                        "Load settings and check for database_url",
                        "database_url attribute not found",
                        "Settings should have database_url attribute",
                        "High"
                    )
            except Exception as e:
                self.add_issue(
                    "CONFIG-003",
                    "config/settings.py",
                    "Settings loading throws exception",
                    "Import and instantiate settings",
                    f"Exception: {str(e)}",
                    "Settings load without exceptions",
                    "Critical"
                )
        
        except Exception as e:
            self.add_issue(
                "CONFIG-004",
                "Configuration system",
                "Configuration testing throws unexpected exception",
                "Test configuration and environment setup",
                f"Exception: {str(e)}",
                "Configuration testing completes without exceptions",
                "Medium"
            )
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        
        # Execute all test suites
        print("🚀 Starting Comprehensive QA Analysis...")
        
        self.test_basic_connectivity()
        token = self.test_authentication_system()
        self.test_database_integration()
        self.test_scholarship_endpoints(token)
        self.test_eligibility_system(token)
        self.test_edge_cases_and_input_validation(token)
        self.test_rate_limiting(token)
        self.test_observability_features()
        self.test_configuration_and_environment()
        
        # Generate summary statistics
        total_issues = len(self.issues)
        severity_counts = {}
        category_counts = {}
        
        for issue in self.issues:
            severity = issue['severity']
            category = issue['category']
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Generate report
        report = {
            "qa_analysis_metadata": {
                "analysis_date": datetime.now().isoformat(),
                "total_issues_found": total_issues,
                "severity_breakdown": severity_counts,
                "category_breakdown": category_counts,
                "qa_engineer": "Senior QA Engineer (Automated Analysis)",
                "analysis_scope": "Full codebase analysis with comprehensive testing"
            },
            "executive_summary": {
                "critical_issues": len([i for i in self.issues if i['severity'] == 'Critical']),
                "high_priority_issues": len([i for i in self.issues if i['severity'] == 'High']),
                "medium_priority_issues": len([i for i in self.issues if i['severity'] == 'Medium']),
                "low_priority_issues": len([i for i in self.issues if i['severity'] == 'Low']),
                "overall_system_health": "Needs Review" if total_issues > 0 else "Healthy"
            },
            "detailed_issues": self.issues,
            "recommendations": [
                "Address all Critical and High severity issues immediately",
                "Implement comprehensive input validation for all endpoints",
                "Add missing error handling for edge cases",
                "Ensure proper security measures against injection attacks",
                "Verify all environment variables are properly configured",
                "Consider implementing more robust rate limiting",
                "Add comprehensive logging for debugging purposes"
            ]
        }
        
        return report

def main():
    """Main QA analysis execution"""
    qa_generator = QAReportGenerator()
    
    try:
        report = qa_generator.generate_report()
        
        # Save report to file
        with open("comprehensive_qa_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE QA ANALYSIS REPORT")
        print("="*80)
        print(f"📊 Total Issues Found: {report['qa_analysis_metadata']['total_issues_found']}")
        print(f"🔴 Critical: {report['executive_summary']['critical_issues']}")
        print(f"🟠 High: {report['executive_summary']['high_priority_issues']}")
        print(f"🟡 Medium: {report['executive_summary']['medium_priority_issues']}")
        print(f"🟢 Low: {report['executive_summary']['low_priority_issues']}")
        print(f"💡 Overall System Health: {report['executive_summary']['overall_system_health']}")
        print("\n📋 Detailed report saved to: comprehensive_qa_report.json")
        print("="*80)
        
        # Print first few issues as examples
        if report['detailed_issues']:
            print("\n🔍 Sample Issues Found:")
            for issue in report['detailed_issues'][:3]:  # Show first 3 issues
                print(f"\n  ID: {issue['issue_id']}")
                print(f"  Severity: {issue['severity']}")
                print(f"  Location: {issue['location']}")
                print(f"  Description: {issue['description']}")
        
        return report
        
    except Exception as e:
        print(f"❌ QA Analysis failed with exception: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    report = main()
    sys.exit(0 if report else 1)