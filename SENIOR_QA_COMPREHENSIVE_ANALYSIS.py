#!/usr/bin/env python3
"""
SENIOR QA ENGINEER COMPREHENSIVE ANALYSIS SUITE
================================================================
Systematic identification of bugs, errors, and vulnerabilities
WITHOUT modifying existing code - analysis and reporting only.
"""

import pytest
import requests
import json
import time
import os
import sys
import traceback
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, '.')

class QAIssue:
    """Data class for tracking identified issues"""
    def __init__(self, issue_id: str, location: str, description: str, 
                 reproduce_steps: str, observed: str, expected: str, severity: str):
        self.issue_id = issue_id
        self.location = location
        self.description = description
        self.reproduce_steps = reproduce_steps
        self.observed = observed
        self.expected = expected
        self.severity = severity
        self.timestamp = datetime.utcnow().isoformat()

class SeniorQAAnalyzer:
    """Senior QA Engineer Analysis Suite"""
    
    def __init__(self):
        self.issues = []
        self.test_results = {}
        self.client = None
        
    def log_issue(self, issue_id: str, location: str, description: str,
                  reproduce_steps: str, observed: str, expected: str, severity: str):
        """Log a new issue"""
        issue = QAIssue(issue_id, location, description, reproduce_steps, 
                       observed, expected, severity)
        self.issues.append(issue)
        print(f"🐛 ISSUE {issue_id} [{severity}]: {description}")
        
    def setup_test_client(self):
        """Initialize test client with error handling"""
        try:
            from main import app
            self.client = TestClient(app)
            return True
        except Exception as e:
            self.log_issue(
                "SETUP-001", "main.py", 
                "Failed to initialize FastAPI test client",
                "1. Import main.py\n2. Create TestClient(app)",
                f"Exception: {str(e)}", 
                "TestClient should initialize successfully",
                "Critical"
            )
            return False
    
    def test_import_vulnerabilities(self):
        """Test for import-related issues and missing dependencies"""
        print("\n🔍 Testing Import Vulnerabilities...")
        
        critical_modules = [
            'main', 'config.settings', 'middleware.auth', 'services.scholarship_service',
            'routers.scholarships', 'routers.search', 'routers.eligibility',
            'models.scholarship', 'schemas.eligibility', 'utils.logger'
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                self.log_issue(
                    f"IMPORT-{module.replace('.', '_').upper()}", 
                    f"{module.replace('.', '/')}.py",
                    f"Critical module import failure: {module}",
                    f"1. python -c 'import {module}'",
                    f"ImportError: {str(e)}",
                    "Module should import without errors",
                    "Critical"
                )
            except Exception as e:
                self.log_issue(
                    f"IMPORT-{module.replace('.', '_').upper()}-RUNTIME", 
                    f"{module.replace('.', '/')}.py",
                    f"Runtime error during module import: {module}",
                    f"1. python -c 'import {module}'",
                    f"Exception: {str(e)}",
                    "Module should import and initialize without runtime errors",
                    "High"
                )
    
    def test_configuration_edge_cases(self):
        """Test configuration handling with extreme and invalid inputs"""
        print("\n🔍 Testing Configuration Edge Cases...")
        
        from config.settings import Settings
        
        # Test cases with various invalid/extreme configurations
        test_configs = [
            {
                'name': 'extremely_long_jwt_secret',
                'env': {'JWT_SECRET_KEY': 'x' * 10000},
                'severity': 'Medium'
            },
            {
                'name': 'unicode_jwt_secret', 
                'env': {'JWT_SECRET_KEY': '🔑密钥тест💾'},
                'severity': 'Medium'
            },
            {
                'name': 'empty_string_values',
                'env': {'API_TITLE': '', 'API_VERSION': '', 'JWT_ALGORITHM': ''},
                'severity': 'High'
            },
            {
                'name': 'extreme_port_numbers',
                'env': {'PORT': '99999'},
                'severity': 'Medium'
            },
            {
                'name': 'negative_timeouts',
                'env': {'ACCESS_TOKEN_EXPIRE_MINUTES': '-1'},
                'severity': 'High'
            },
            {
                'name': 'malformed_lists',
                'env': {'CORS_ALLOW_METHODS': '["GET",invalid,}'},
                'severity': 'Medium'
            }
        ]
        
        for config in test_configs:
            try:
                old_env = dict(os.environ)
                os.environ.update(config['env'])
                
                settings = Settings()
                
                # If this succeeds when it shouldn't, it's an issue
                if config['name'] in ['empty_string_values', 'negative_timeouts']:
                    self.log_issue(
                        f"CONFIG-{config['name'].upper()}",
                        "config/settings.py",
                        f"Configuration accepts invalid values: {config['name']}",
                        f"1. Set environment: {config['env']}\n2. Create Settings()",
                        "Configuration loaded successfully",
                        "Should reject invalid configuration values",
                        config['severity']
                    )
                
                os.environ.clear()
                os.environ.update(old_env)
                
            except Exception as e:
                # Expected for some invalid configs
                os.environ.clear() 
                os.environ.update(old_env)
                pass
    
    def test_authentication_vulnerabilities(self):
        """Test authentication system for security vulnerabilities"""
        print("\n🔍 Testing Authentication Vulnerabilities...")
        
        if not self.client:
            return
            
        # Test JWT handling edge cases
        auth_tests = [
            {
                'name': 'empty_jwt_token',
                'headers': {'Authorization': 'Bearer '},
                'expected_status': 401
            },
            {
                'name': 'malformed_jwt_token', 
                'headers': {'Authorization': 'Bearer not.a.jwt'},
                'expected_status': 401
            },
            {
                'name': 'jwt_without_bearer',
                'headers': {'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9'},
                'expected_status': 401
            },
            {
                'name': 'extremely_long_jwt',
                'headers': {'Authorization': f'Bearer {"x" * 10000}'},
                'expected_status': 401
            },
            {
                'name': 'jwt_with_null_bytes',
                'headers': {'Authorization': 'Bearer test\x00token'},
                'expected_status': 401
            }
        ]
        
        for test in auth_tests:
            try:
                response = self.client.get("/api/v1/scholarships", headers=test['headers'])
                
                if response.status_code != test['expected_status']:
                    self.log_issue(
                        f"AUTH-{test['name'].upper()}",
                        "middleware/auth.py",
                        f"Unexpected authentication behavior: {test['name']}",
                        f"1. Send GET /api/v1/scholarships\n2. Headers: {test['headers']}",
                        f"Status code: {response.status_code}",
                        f"Expected status code: {test['expected_status']}",
                        "High"
                    )
                    
            except Exception as e:
                self.log_issue(
                    f"AUTH-{test['name'].upper()}-EXCEPTION",
                    "middleware/auth.py",
                    f"Authentication test caused unexpected exception: {test['name']}",
                    f"1. Send GET /api/v1/scholarships\n2. Headers: {test['headers']}",
                    f"Exception: {str(e)}",
                    "Should handle gracefully with appropriate HTTP status",
                    "High"
                )
    
    def test_input_validation_edge_cases(self):
        """Test input validation with extreme and malicious inputs"""
        print("\n🔍 Testing Input Validation Edge Cases...")
        
        if not self.client:
            return
            
        # Test search endpoint with various problematic inputs
        search_payloads = [
            {
                'name': 'extremely_long_query',
                'payload': {'query': 'x' * 100000},
                'severity': 'High'
            },
            {
                'name': 'sql_injection_attempt',
                'payload': {'query': "'; DROP TABLE scholarships; --"},
                'severity': 'Critical'
            },
            {
                'name': 'script_injection',
                'payload': {'query': '<script>alert("xss")</script>'},
                'severity': 'High'
            },
            {
                'name': 'unicode_overflow',
                'payload': {'query': '🔥' * 1000},
                'severity': 'Medium'
            },
            {
                'name': 'null_bytes',
                'payload': {'query': 'test\x00query'},
                'severity': 'High'
            },
            {
                'name': 'negative_limits',
                'payload': {'limit': -1, 'offset': -100},
                'severity': 'High'
            },
            {
                'name': 'extreme_limits',
                'payload': {'limit': 999999, 'offset': 999999},
                'severity': 'Medium'
            },
            {
                'name': 'invalid_gpa_range',
                'payload': {'min_gpa': 5.0, 'max_amount': -1000},
                'severity': 'Medium'
            }
        ]
        
        for test in search_payloads:
            try:
                response = self.client.post("/search", json=test['payload'])
                
                # Check for unexpected behavior
                if response.status_code == 500:
                    self.log_issue(
                        f"INPUT-{test['name'].upper()}",
                        "routers/search.py",
                        f"Input validation causes server error: {test['name']}",
                        f"1. POST /search\n2. Payload: {test['payload']}",
                        f"500 Internal Server Error: {response.text}",
                        "Should handle invalid input gracefully with 4xx status",
                        test['severity']
                    )
                elif response.status_code == 200 and test['name'] in ['sql_injection_attempt', 'script_injection']:
                    self.log_issue(
                        f"INPUT-{test['name'].upper()}-ACCEPTED",
                        "routers/search.py", 
                        f"Potentially dangerous input accepted: {test['name']}",
                        f"1. POST /search\n2. Payload: {test['payload']}",
                        f"Request accepted with 200 OK",
                        "Should reject or sanitize dangerous input",
                        "Critical"
                    )
                    
            except Exception as e:
                self.log_issue(
                    f"INPUT-{test['name'].upper()}-EXCEPTION",
                    "routers/search.py",
                    f"Input validation test caused exception: {test['name']}",
                    f"1. POST /search\n2. Payload: {test['payload']}",
                    f"Exception: {str(e)}",
                    "Should handle edge case inputs without exceptions",
                    "High"
                )
    
    def test_rate_limiting_bypass(self):
        """Test rate limiting for potential bypass vulnerabilities"""
        print("\n🔍 Testing Rate Limiting Bypass Attempts...")
        
        if not self.client:
            return
            
        # Test various rate limit bypass techniques
        bypass_tests = [
            {
                'name': 'header_spoofing',
                'headers': {'X-Forwarded-For': '127.0.0.1', 'X-Real-IP': '1.2.3.4'},
                'requests': 20
            },
            {
                'name': 'user_agent_rotation',
                'headers': {},  # Will be set dynamically in test
                'requests': 15
            },
            {
                'name': 'concurrent_requests',
                'headers': {},
                'requests': 50  # Rapid fire
            }
        ]
        
        for test in bypass_tests:
            try:
                rate_limited = False
                for i in range(test['requests']):
                    if test['name'] == 'user_agent_rotation':
                        headers = {'User-Agent': f'TestBot-{i}'}
                    else:
                        headers = test['headers']
                        
                    response = self.client.get("/api/v1/scholarships", headers=headers)
                    
                    if response.status_code == 429:
                        rate_limited = True
                        break
                        
                if not rate_limited and test['requests'] > 10:
                    self.log_issue(
                        f"RATE-{test['name'].upper()}",
                        "middleware/rate_limiting.py",
                        f"Rate limiting potentially bypassed: {test['name']}",
                        f"1. Send {test['requests']} requests rapidly\n2. Headers: {test['headers']}",
                        "All requests succeeded without rate limiting",
                        "Should enforce rate limits and return 429 status",
                        "Medium"
                    )
                    
            except Exception as e:
                self.log_issue(
                    f"RATE-{test['name'].upper()}-EXCEPTION",
                    "middleware/rate_limiting.py",
                    f"Rate limiting test caused exception: {test['name']}",
                    f"1. Send {test['requests']} requests\n2. Headers: {test['headers']}",
                    f"Exception: {str(e)}",
                    "Rate limiting should handle stress testing gracefully",
                    "High"
                )
    
    def test_data_consistency_issues(self):
        """Test for data consistency and integrity issues"""
        print("\n🔍 Testing Data Consistency Issues...")
        
        try:
            from services.scholarship_service import ScholarshipService
            from services.eligibility_service import EligibilityService
            
            service = ScholarshipService()
            eligibility_service = EligibilityService()
            
            # Test data consistency
            scholarships = service.get_all_scholarships()
            
            if not scholarships:
                self.log_issue(
                    "DATA-EMPTY-SET",
                    "services/scholarship_service.py",
                    "No scholarships found in dataset",
                    "1. Create ScholarshipService\n2. Call get_all_scholarships()",
                    "Empty list returned",
                    "Should return scholarship data",
                    "High"
                )
                return
            
            # Check for data integrity issues
            for i, scholarship in enumerate(scholarships):
                if not hasattr(scholarship, 'id') or not scholarship.id:
                    self.log_issue(
                        f"DATA-MISSING-ID-{i}",
                        "data/scholarships.py",
                        f"Scholarship missing required ID field at index {i}",
                        f"1. Get scholarship at index {i}",
                        "Scholarship object without valid ID",
                        "All scholarships should have unique IDs",
                        "High"
                    )
                
                if hasattr(scholarship, 'amount') and scholarship.amount and scholarship.amount < 0:
                    self.log_issue(
                        f"DATA-NEGATIVE-AMOUNT-{scholarship.id}",
                        "data/scholarships.py",
                        f"Scholarship {scholarship.id} has negative amount",
                        f"1. Check scholarship {scholarship.id} amount field",
                        f"Amount: {scholarship.amount}",
                        "Scholarship amounts should be positive",
                        "Medium"
                    )
                        
        except Exception as e:
            self.log_issue(
                "DATA-SERVICE-EXCEPTION",
                "services/scholarship_service.py",
                "Exception accessing scholarship data",
                "1. Import ScholarshipService\n2. Call get_all_scholarships()",
                f"Exception: {str(e)}",
                "Should access scholarship data without exceptions",
                "Critical"
            )
    
    def test_error_handling_consistency(self):
        """Test error handling consistency across endpoints"""
        print("\n🔍 Testing Error Handling Consistency...")
        
        if not self.client:
            return
            
        endpoints_to_test = [
            "/api/v1/scholarships",
            "/search", 
            "/eligibility/check",
            "/api/v1/analytics/summary",
            "/nonexistent/endpoint"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.client.get(endpoint)
                
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        
                        # Check for consistent error format
                        required_fields = ['trace_id', 'code', 'message', 'status', 'timestamp']
                        missing_fields = [field for field in required_fields if field not in error_data]
                        
                        if missing_fields:
                            self.log_issue(
                                f"ERROR-FORMAT-{endpoint.replace('/', '_').upper()}",
                                "middleware/error_handlers.py",
                                f"Inconsistent error format for {endpoint}",
                                f"1. GET {endpoint}\n2. Check error response format",
                                f"Missing fields: {missing_fields}",
                                f"Error response should include: {required_fields}",
                                "Medium"
                            )
                            
                    except json.JSONDecodeError:
                        self.log_issue(
                            f"ERROR-JSON-{endpoint.replace('/', '_').upper()}",
                            "middleware/error_handlers.py", 
                            f"Non-JSON error response for {endpoint}",
                            f"1. GET {endpoint}\n2. Parse response as JSON",
                            f"Response: {response.text}",
                            "Error responses should be valid JSON",
                            "Medium"
                        )
                        
            except Exception as e:
                self.log_issue(
                    f"ERROR-TEST-{endpoint.replace('/', '_').upper()}",
                    "middleware/error_handlers.py",
                    f"Exception testing error handling for {endpoint}",
                    f"1. GET {endpoint}",
                    f"Exception: {str(e)}",
                    "Should handle endpoint testing without exceptions",
                    "High"
                )
    
    def test_performance_degradation(self):
        """Test for performance issues and potential DoS vectors"""
        print("\n🔍 Testing Performance Degradation...")
        
        if not self.client:
            return
            
        # Test response times for potential performance issues
        performance_tests = [
            {
                'name': 'large_search_query',
                'endpoint': '/search',
                'method': 'POST',
                'payload': {'query': 'scholarship ' * 1000},
                'max_time': 5.0
            },
            {
                'name': 'complex_filters',
                'endpoint': '/search', 
                'method': 'POST',
                'payload': {
                    'fields_of_study': ['Engineering'] * 50,
                    'states': ['CA'] * 50,
                    'scholarship_types': ['Merit'] * 50
                },
                'max_time': 5.0
            },
            {
                'name': 'health_check_performance',
                'endpoint': '/health',
                'method': 'GET',
                'payload': None,
                'max_time': 1.0
            }
        ]
        
        for test in performance_tests:
            try:
                start_time = time.time()
                
                if test['method'] == 'GET':
                    response = self.client.get(test['endpoint'])
                else:
                    response = self.client.post(test['endpoint'], json=test['payload'])
                    
                end_time = time.time()
                response_time = end_time - start_time
                
                if response_time > test['max_time']:
                    self.log_issue(
                        f"PERF-{test['name'].upper()}",
                        f"routers/{test['endpoint'].split('/')[1] if len(test['endpoint'].split('/')) > 1 else 'health'}.py",
                        f"Slow response time for {test['name']}: {response_time:.2f}s",
                        f"1. {test['method']} {test['endpoint']}\n2. Payload: {test['payload']}",
                        f"Response time: {response_time:.2f} seconds",
                        f"Should respond within {test['max_time']} seconds",
                        "Medium"
                    )
                    
            except Exception as e:
                self.log_issue(
                    f"PERF-{test['name'].upper()}-EXCEPTION",
                    "Performance testing",
                    f"Performance test caused exception: {test['name']}",
                    f"1. {test['method']} {test['endpoint']}\n2. Payload: {test['payload']}",
                    f"Exception: {str(e)}",
                    "Performance tests should complete without exceptions",
                    "High"
                )
    
    def test_security_headers(self):
        """Test for missing or misconfigured security headers"""
        print("\n🔍 Testing Security Headers...")
        
        if not self.client:
            return
            
        try:
            response = self.client.get("/health")
            headers = response.headers
            
            # Check for critical security headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': None  # Should be present in production
            }
            
            for header, expected in security_headers.items():
                if header not in headers:
                    self.log_issue(
                        f"SEC-HEADER-{header.replace('-', '_').upper()}",
                        "middleware/security_headers.py",
                        f"Missing security header: {header}",
                        f"1. GET /health\n2. Check response headers",
                        f"Header not present in response",
                        f"Should include {header} header",
                        "Medium"
                    )
                elif expected and isinstance(expected, list):
                    if headers[header] not in expected:
                        self.log_issue(
                            f"SEC-HEADER-{header.replace('-', '_').upper()}-VALUE",
                            "middleware/security_headers.py",
                            f"Invalid security header value: {header}",
                            f"1. GET /health\n2. Check {header} header value",
                            f"Value: {headers[header]}",
                            f"Should be one of: {expected}",
                            "Medium"
                        )
                elif expected and headers[header] != expected:
                    self.log_issue(
                        f"SEC-HEADER-{header.replace('-', '_').upper()}-VALUE",
                        "middleware/security_headers.py", 
                        f"Invalid security header value: {header}",
                        f"1. GET /health\n2. Check {header} header value",
                        f"Value: {headers[header]}",
                        f"Expected: {expected}",
                        "Medium"
                    )
                    
        except Exception as e:
            self.log_issue(
                "SEC-HEADER-TEST-EXCEPTION",
                "middleware/security_headers.py",
                "Exception testing security headers",
                "1. GET /health\n2. Check response headers",
                f"Exception: {str(e)}",
                "Should test security headers without exceptions",
                "High"
            )
    
    def run_comprehensive_analysis(self):
        """Run all QA tests and generate comprehensive report"""
        print("🚀 STARTING SENIOR QA COMPREHENSIVE ANALYSIS")
        print("=" * 60)
        
        # Initialize test client
        if not self.setup_test_client():
            print("❌ Failed to setup test client - some tests will be skipped")
        
        # Run all test suites
        self.test_import_vulnerabilities()
        self.test_configuration_edge_cases()
        self.test_authentication_vulnerabilities()
        self.test_input_validation_edge_cases()
        self.test_rate_limiting_bypass()
        self.test_data_consistency_issues()
        self.test_error_handling_consistency()
        self.test_performance_degradation()
        self.test_security_headers()
        
        # Generate comprehensive report
        self.generate_report()
    
    def generate_report(self):
        """Generate detailed QA analysis report"""
        print("\n" + "=" * 60)
        print("📊 SENIOR QA ANALYSIS REPORT")
        print("=" * 60)
        
        if not self.issues:
            print("✅ No issues identified in comprehensive analysis")
            return
            
        # Group issues by severity
        severity_groups = {}
        for issue in self.issues:
            if issue.severity not in severity_groups:
                severity_groups[issue.severity] = []
            severity_groups[issue.severity].append(issue)
        
        # Report summary
        print(f"\n📈 SUMMARY: {len(self.issues)} total issues identified")
        for severity in ['Critical', 'High', 'Medium', 'Low']:
            if severity in severity_groups:
                print(f"  {severity}: {len(severity_groups[severity])} issues")
        
        # Detailed issue reports
        for severity in ['Critical', 'High', 'Medium', 'Low']:
            if severity in severity_groups:
                print(f"\n🔥 {severity.upper()} SEVERITY ISSUES:")
                print("-" * 40)
                
                for issue in severity_groups[severity]:
                    print(f"\nIssue ID: {issue.issue_id}")
                    print(f"Location: {issue.location}")
                    print(f"Description: {issue.description}")
                    print(f"Steps to Reproduce:")
                    for step in issue.reproduce_steps.split('\n'):
                        print(f"  {step}")
                    print(f"Observed Output: {issue.observed}")
                    print(f"Expected Output: {issue.expected}")
                    print(f"Severity: {issue.severity}")
                    print(f"Timestamp: {issue.timestamp}")
                    print("-" * 40)

if __name__ == "__main__":
    analyzer = SeniorQAAnalyzer()
    analyzer.run_comprehensive_analysis()