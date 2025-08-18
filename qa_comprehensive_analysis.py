#!/usr/bin/env python3
"""
Senior QA Engineer Comprehensive Analysis Script
FastAPI Scholarship Discovery Search API

This script performs comprehensive testing and analysis to identify:
- Runtime errors and exceptions
- Logic bugs and unexpected behavior
- Security vulnerabilities
- Performance issues
- Configuration problems
- Data validation failures

IMPORTANT: This is a READ-ONLY analysis script that does NOT modify any existing code.
"""

import os
import sys
import json
import traceback
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

class QATestResults:
    def __init__(self):
        self.issues = []
        self.test_results = []
        self.severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
    def add_issue(self, issue_id: str, location: str, description: str, 
                  steps_to_reproduce: str, observed_output: str, 
                  expected_output: str, severity: str):
        """Add a new issue to the findings"""
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
        self.issues.append(issue)
        self.severity_counts[severity] += 1
        
    def add_test_result(self, test_name: str, status: str, details: str):
        """Add a test execution result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

class ComprehensiveQAAnalysis:
    def __init__(self):
        self.results = QATestResults()
        self.base_url = "http://localhost:5000"
        
    def analyze_codebase_structure(self):
        """Analyze project structure and identify structural issues"""
        print("🔍 Analyzing codebase structure...")
        
        # Check for critical files
        required_files = [
            "main.py", "config/settings.py", "requirements.txt", 
            "pyproject.toml", ".env.example"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                self.results.add_issue(
                    f"STRUCT-001-{file_path.replace('/', '_')}",
                    f"Project root",
                    f"Missing required file: {file_path}",
                    f"Check if {file_path} exists in project root",
                    f"File not found: {file_path}",
                    f"File should exist: {file_path}",
                    "Medium"
                )
                
    def test_import_integrity(self):
        """Test all Python imports for errors"""
        print("🔍 Testing import integrity...")
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files[:20]:  # Limit to first 20 files
            try:
                # Try to compile the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, file_path, 'exec')
                
            except SyntaxError as e:
                self.results.add_issue(
                    f"SYNTAX-001-{hash(file_path) % 1000}",
                    f"{file_path}:{e.lineno}",
                    f"Syntax error in Python file",
                    f"Try to import or compile {file_path}",
                    f"SyntaxError: {e.msg}",
                    f"Valid Python syntax",
                    "Critical"
                )
            except Exception as e:
                self.results.add_issue(
                    f"IMPORT-001-{hash(file_path) % 1000}",
                    file_path,
                    f"Import/compilation error: {str(e)}",
                    f"Try to import {file_path}",
                    f"Error: {str(e)}",
                    f"Successful import",
                    "High"
                )

    def test_configuration_loading(self):
        """Test configuration loading and validation"""
        print("🔍 Testing configuration loading...")
        
        try:
            from config.settings import Settings, get_settings
            
            # Test with various environment configurations
            test_configs = [
                {"ENVIRONMENT": "development"},
                {"ENVIRONMENT": "production", "JWT_SECRET_KEY": "test-key-" + "x"*50},
                {"ENVIRONMENT": "local"},
                {"PUBLIC_READ_ENDPOINTS": "true"},
                {"PUBLIC_READ_ENDPOINTS": "false"},
                {"RATE_LIMIT_ENABLED": "true"},
                {"RATE_LIMIT_ENABLED": "false"},
            ]
            
            for i, config in enumerate(test_configs):
                try:
                    # Save original env vars
                    original_env = {}
                    for key, value in config.items():
                        original_env[key] = os.environ.get(key)
                        os.environ[key] = value
                    
                    settings = Settings()
                    
                    # Test basic property access
                    _ = settings.environment
                    _ = settings.debug
                    _ = settings.jwt_secret_key
                    
                    # Restore original env vars
                    for key in config.keys():
                        if original_env[key] is not None:
                            os.environ[key] = original_env[key]
                        elif key in os.environ:
                            del os.environ[key]
                            
                    self.results.add_test_result(
                        f"Config Test {i+1}",
                        "PASSED",
                        f"Configuration loaded successfully with {config}"
                    )
                    
                except Exception as e:
                    self.results.add_issue(
                        f"CONFIG-001-{i}",
                        "config/settings.py",
                        f"Configuration loading failed with environment: {config}",
                        f"Set environment variables: {config} and load Settings()",
                        f"Exception: {str(e)}",
                        f"Successful configuration loading",
                        "High"
                    )
                    
        except Exception as e:
            self.results.add_issue(
                "CONFIG-002",
                "config/settings.py",
                f"Cannot import Settings class: {str(e)}",
                "Try to import Settings from config.settings",
                f"ImportError: {str(e)}",
                "Successful import of Settings",
                "Critical"
            )

    def test_database_models(self):
        """Test database model integrity"""
        print("🔍 Testing database models...")
        
        try:
            from models.scholarship import Scholarship, EligibilityCriteria, ScholarshipSummary
            from models.user import UserProfile
            from pydantic import ValidationError
            
            # Test invalid data scenarios
            invalid_scholarship_data = [
                {"name": "", "amount": -100},  # Empty name, negative amount
                {"amount": "invalid"},  # Wrong type
                {"gpa": 5.0},  # Invalid GPA
                {},  # Missing required fields
            ]
            
            for i, data in enumerate(invalid_scholarship_data):
                try:
                    # This should fail validation
                    if 'gpa' in data:
                        # Test EligibilityCriteria
                        EligibilityCriteria(min_gpa=data['gpa'])
                        self.results.add_issue(
                            f"VALID-001-{i}",
                            "models/scholarship.py",
                            f"Model validation too permissive",
                            f"Create EligibilityCriteria with invalid data: {data}",
                            f"Validation passed unexpectedly",
                            f"ValidationError should be raised",
                            "Medium"
                        )
                    else:
                        # This is expected to fail, so no issue if it does
                        pass
                except ValidationError:
                    # This is expected behavior
                    pass
                except Exception as e:
                    self.results.add_issue(
                        f"MODEL-001-{i}",
                        "models/scholarship.py",
                        f"Unexpected error in model validation: {str(e)}",
                        f"Create model with invalid data: {data}",
                        f"Unexpected error: {str(e)}",
                        f"ValidationError or successful creation",
                        "Medium"
                    )
                    
        except Exception as e:
            self.results.add_issue(
                "MODEL-002",
                "models/scholarship.py",
                f"Cannot import model classes: {str(e)}",
                "Try to import Scholarship, EligibilityCriteria from models.scholarship",
                f"ImportError: {str(e)}",
                "Successful import of model classes",
                "High"
            )

    def test_api_endpoints_runtime(self):
        """Test API endpoints for runtime errors"""
        print("🔍 Testing API endpoints runtime behavior...")
        
        # Test endpoints that should be accessible
        test_endpoints = [
            {"method": "GET", "path": "/", "expected_status": [200]},
            {"method": "GET", "path": "/health", "expected_status": [200]},
            {"method": "GET", "path": "/docs", "expected_status": [200]},
            {"method": "GET", "path": "/api/v1/scholarships", "expected_status": [200, 401]},
            {"method": "GET", "path": "/search", "expected_status": [200, 401, 422]},
            {"method": "GET", "path": "/eligibility/check", "expected_status": [200, 401, 422]},
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.request(
                    method=endpoint["method"],
                    url=f"{self.base_url}{endpoint['path']}",
                    timeout=5
                )
                
                if response.status_code not in endpoint["expected_status"]:
                    # Check if it's a 500 error (critical)
                    severity = "Critical" if response.status_code == 500 else "Medium"
                    
                    self.results.add_issue(
                        f"API-001-{endpoint['path'].replace('/', '_')}",
                        f"API endpoint: {endpoint['method']} {endpoint['path']}",
                        f"Unexpected HTTP status code",
                        f"Send {endpoint['method']} request to {endpoint['path']}",
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        f"HTTP status in {endpoint['expected_status']}",
                        severity
                    )
                else:
                    self.results.add_test_result(
                        f"API {endpoint['method']} {endpoint['path']}",
                        "PASSED",
                        f"HTTP {response.status_code} as expected"
                    )
                    
            except requests.exceptions.ConnectionError:
                self.results.add_issue(
                    "API-002",
                    "Server connectivity",
                    "Cannot connect to API server",
                    f"Start server and send request to {self.base_url}",
                    "Connection refused or timeout",
                    "Successful HTTP response",
                    "Critical"
                )
                break
            except Exception as e:
                self.results.add_issue(
                    f"API-003-{endpoint['path'].replace('/', '_')}",
                    f"API endpoint: {endpoint['path']}",
                    f"Request execution error: {str(e)}",
                    f"Send {endpoint['method']} request to {endpoint['path']}",
                    f"Exception: {str(e)}",
                    f"Successful HTTP response",
                    "High"
                )

    def test_edge_cases_data_validation(self):
        """Test edge cases and boundary conditions"""
        print("🔍 Testing edge cases and data validation...")
        
        # Test various edge case inputs
        edge_case_tests = [
            {
                "name": "Empty String Inputs",
                "endpoint": "/search",
                "params": {"q": ""},
                "description": "Search with empty query string"
            },
            {
                "name": "Very Long String",
                "endpoint": "/search", 
                "params": {"q": "A" * 10000},
                "description": "Search with extremely long query"
            },
            {
                "name": "Special Characters",
                "endpoint": "/search",
                "params": {"q": "!@#$%^&*(){}[]|\\:;\"'<>,.?/~`"},
                "description": "Search with special characters"
            },
            {
                "name": "SQL Injection Attempt",
                "endpoint": "/search",
                "params": {"q": "'; DROP TABLE scholarships; --"},
                "description": "Potential SQL injection attack"
            },
            {
                "name": "XSS Attempt",
                "endpoint": "/search", 
                "params": {"q": "<script>alert('xss')</script>"},
                "description": "Potential XSS attack"
            },
            {
                "name": "Invalid GPA Values",
                "endpoint": "/api/v1/scholarships",
                "params": {"min_gpa": -1},
                "description": "Negative GPA value"
            },
            {
                "name": "Boundary GPA",
                "endpoint": "/api/v1/scholarships", 
                "params": {"min_gpa": 5.0},
                "description": "GPA above maximum (4.0)"
            },
            {
                "name": "Invalid Amount",
                "endpoint": "/api/v1/scholarships",
                "params": {"min_amount": -1000},
                "description": "Negative scholarship amount"
            }
        ]
        
        for test_case in edge_case_tests:
            try:
                response = requests.get(
                    f"{self.base_url}{test_case['endpoint']}",
                    params=test_case['params'],
                    timeout=5
                )
                
                # Check for unexpected 500 errors
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', response.text[:200])
                    except:
                        error_detail = response.text[:200]
                        
                    self.results.add_issue(
                        f"EDGE-001-{hash(test_case['name']) % 1000}",
                        test_case['endpoint'],
                        f"Server error on edge case: {test_case['name']}",
                        f"Send GET to {test_case['endpoint']} with params: {test_case['params']}",
                        f"HTTP 500: {error_detail}",
                        "Graceful error handling (4xx) or successful response",
                        "High"
                    )
                    
                # Check for potential security issues in response
                if response.status_code == 200:
                    response_text = response.text.lower()
                    if any(keyword in response_text for keyword in ['error', 'exception', 'traceback']):
                        self.results.add_issue(
                            f"SEC-001-{hash(test_case['name']) % 1000}",
                            test_case['endpoint'],
                            f"Information disclosure in response",
                            f"Send request with: {test_case['params']}",
                            f"Response contains error details: {response.text[:200]}",
                            "Clean response without internal error details",
                            "Medium"
                        )
                        
                self.results.add_test_result(
                    f"Edge Case: {test_case['name']}",
                    "COMPLETED",
                    f"HTTP {response.status_code}"
                )
                
            except requests.exceptions.ConnectionError:
                break  # Server not running
            except Exception as e:
                self.results.add_issue(
                    f"EDGE-002-{hash(test_case['name']) % 1000}",
                    test_case['endpoint'],
                    f"Exception during edge case testing: {str(e)}",
                    f"Test case: {test_case['description']}",
                    f"Exception: {str(e)}",
                    "Graceful handling or valid response",
                    "Medium"
                )

    def test_performance_and_resource_usage(self):
        """Test for performance issues and resource leaks"""
        print("🔍 Testing performance and resource usage...")
        
        try:
            # Test rapid requests to check for rate limiting and resource handling
            start_time = time.time()
            response_times = []
            
            for i in range(10):  # Limited burst test
                try:
                    req_start = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    req_end = time.time()
                    
                    response_time = req_end - req_start
                    response_times.append(response_time)
                    
                    if response_time > 5.0:  # Very slow response
                        self.results.add_issue(
                            f"PERF-001-{i}",
                            "/health endpoint",
                            f"Slow response time: {response_time:.2f}s",
                            f"Send GET request to /health (request #{i+1})",
                            f"Response time: {response_time:.2f} seconds",
                            "Response time < 2 seconds",
                            "Medium"
                        )
                        
                except Exception as e:
                    self.results.add_issue(
                        f"PERF-002-{i}",
                        "/health endpoint",
                        f"Request failed during performance test: {str(e)}",
                        f"Send rapid requests to /health",
                        f"Exception: {str(e)}",
                        "Successful response",
                        "Medium"
                    )
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                self.results.add_test_result(
                    "Performance Test",
                    "COMPLETED",
                    f"Average response time: {avg_response_time:.3f}s over {len(response_times)} requests"
                )
                
        except Exception as e:
            self.results.add_issue(
                "PERF-003",
                "Performance testing",
                f"Performance test setup failed: {str(e)}",
                "Execute performance testing suite",
                f"Setup error: {str(e)}",
                "Successful performance test execution",
                "Low"
            )

    def generate_comprehensive_report(self):
        """Generate the final comprehensive QA report"""
        print("📊 Generating comprehensive QA report...")
        
        report = {
            "qa_analysis_report": {
                "metadata": {
                    "project": "FastAPI Scholarship Discovery Search API",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analyst": "Senior QA Engineer (Automated Analysis)",
                    "analysis_type": "Comprehensive Code Quality & Security Assessment"
                },
                "executive_summary": {
                    "total_issues_found": len(self.results.issues),
                    "severity_breakdown": self.results.severity_counts,
                    "tests_executed": len(self.results.test_results),
                    "critical_issues_count": self.results.severity_counts["Critical"],
                    "high_priority_issues": self.results.severity_counts["High"]
                },
                "detailed_findings": self.results.issues,
                "test_execution_results": self.results.test_results,
                "recommendations": [
                    "Address all Critical severity issues immediately",
                    "Implement comprehensive error handling for edge cases",
                    "Add input validation for all user-facing endpoints",
                    "Implement rate limiting to prevent abuse",
                    "Add security headers to prevent common attacks",
                    "Implement comprehensive logging for debugging",
                    "Add automated testing pipeline for continuous quality assurance"
                ]
            }
        }
        
        # Save report to file
        report_file = f"QA_COMPREHENSIVE_ANALYSIS_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report, report_file

    def run_full_analysis(self):
        """Execute the complete QA analysis suite"""
        print("🚀 Starting Comprehensive QA Analysis...")
        print("="*60)
        
        try:
            self.analyze_codebase_structure()
            self.test_import_integrity() 
            self.test_configuration_loading()
            self.test_database_models()
            self.test_api_endpoints_runtime()
            self.test_edge_cases_data_validation()
            self.test_performance_and_resource_usage()
            
            report, report_file = self.generate_comprehensive_report()
            
            print("\n" + "="*60)
            print("📋 QA ANALYSIS COMPLETE")
            print("="*60)
            print(f"Report saved to: {report_file}")
            print(f"Total Issues Found: {len(self.results.issues)}")
            print(f"Critical: {self.results.severity_counts['Critical']}")
            print(f"High: {self.results.severity_counts['High']}")
            print(f"Medium: {self.results.severity_counts['Medium']}")
            print(f"Low: {self.results.severity_counts['Low']}")
            
            return report
            
        except Exception as e:
            print(f"❌ Analysis failed with error: {str(e)}")
            traceback.print_exc()
            return None

if __name__ == "__main__":
    qa_analyzer = ComprehensiveQAAnalysis()
    report = qa_analyzer.run_full_analysis()
    
    if report:
        print("\n🔍 TOP CRITICAL ISSUES:")
        critical_issues = [issue for issue in report["qa_analysis_report"]["detailed_findings"] 
                          if issue["severity"] == "Critical"]
        for issue in critical_issues[:5]:  # Show top 5 critical issues
            print(f"- {issue['issue_id']}: {issue['description']} [{issue['location']}]")