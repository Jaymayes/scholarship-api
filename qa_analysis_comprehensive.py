#!/usr/bin/env python3
"""
Comprehensive QA Analysis Script
Performs thorough testing and vulnerability analysis without modifying existing code
"""

import os
import sys
import json
import traceback
import subprocess
import importlib.util
from typing import List, Dict, Any, Optional
from pathlib import Path
import ast
import time
import requests
from datetime import datetime

class QAAnalyzer:
    """Comprehensive QA analysis without code modification"""
    
    def __init__(self):
        self.issues = []
        self.test_results = []
        self.issue_counter = 1
        self.base_url = "http://localhost:5000"
        
    def add_issue(self, location: str, description: str, steps_to_reproduce: str, 
                  observed_output: str, expected_output: str, severity: str):
        """Add a new issue to the findings"""
        issue = {
            "issue_id": f"QA-{self.issue_counter:03d}",
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        self.issue_counter += 1
        
    def analyze_imports_and_dependencies(self):
        """Analyze import statements and dependencies for issues"""
        print("🔍 Analyzing imports and dependencies...")
        
        python_files = list(Path(".").rglob("*.py"))
        for file_path in python_files:
            if "qa_analysis" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self._check_import_availability(alias.name, str(file_path), node.lineno)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                self._check_import_availability(node.module, str(file_path), node.lineno)
                except SyntaxError as e:
                    self.add_issue(
                        f"{file_path}:{e.lineno}",
                        f"Syntax error in Python file",
                        f"Parse file {file_path}",
                        f"SyntaxError: {e.msg}",
                        "Valid Python syntax",
                        "High"
                    )
            except Exception as e:
                self.add_issue(
                    str(file_path),
                    f"Failed to analyze file",
                    f"Read and parse {file_path}",
                    f"Error: {str(e)}",
                    "Successful file analysis",
                    "Medium"
                )
    
    def _check_import_availability(self, module_name: str, file_path: str, line_no: int):
        """Check if an import is available"""
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            self.add_issue(
                f"{file_path}:{line_no}",
                f"Import error for module '{module_name}'",
                f"Import {module_name} in {file_path}",
                f"ImportError: {str(e)}",
                f"Successful import of {module_name}",
                "High"
            )
        except Exception as e:
            self.add_issue(
                f"{file_path}:{line_no}",
                f"Unexpected error importing '{module_name}'",
                f"Import {module_name} in {file_path}",
                f"Error: {str(e)}",
                f"Successful import of {module_name}",
                "Medium"
            )
    
    def test_configuration_loading(self):
        """Test configuration and settings loading"""
        print("⚙️ Testing configuration loading...")
        
        try:
            # Test settings import
            sys.path.insert(0, os.getcwd())
            from config.settings import Settings
            
            # Test with various environment configurations
            test_configs = [
                {"ENVIRONMENT": "local"},
                {"ENVIRONMENT": "development"},
                {"ENVIRONMENT": "production", "JWT_SECRET_KEY": "test" * 20},
                {}  # Default config
            ]
            
            for i, config in enumerate(test_configs):
                try:
                    # Temporarily set environment
                    original_env = {}
                    for key, value in config.items():
                        original_env[key] = os.environ.get(key)
                        os.environ[key] = value
                    
                    try:
                        settings = Settings()
                        # Test critical properties
                        _ = settings.database_url
                        _ = settings.jwt_secret_key
                        _ = settings.environment
                    except Exception as e:
                        self.add_issue(
                            "config/settings.py",
                            f"Settings initialization failed with config {i}",
                            f"Initialize Settings() with environment: {config}",
                            f"Exception: {str(e)}",
                            "Successful settings initialization",
                            "High" if "production" in str(config) else "Medium"
                        )
                    finally:
                        # Restore environment
                        for key, value in original_env.items():
                            if value is None:
                                os.environ.pop(key, None)
                            else:
                                os.environ[key] = value
                                
                except Exception as e:
                    self.add_issue(
                        "config/settings.py",
                        f"Environment setup failed for test config {i}",
                        f"Set environment variables: {config}",
                        f"Exception: {str(e)}",
                        "Successful environment setup",
                        "Medium"
                    )
        except ImportError as e:
            self.add_issue(
                "config/settings.py",
                "Cannot import Settings class",
                "from config.settings import Settings",
                f"ImportError: {str(e)}",
                "Successful import",
                "Critical"
            )
    
    def test_database_operations(self):
        """Test database-related functionality"""
        print("🗄️ Testing database operations...")
        
        try:
            sys.path.insert(0, os.getcwd())
            from database.connection import get_database_url, test_connection
            
            # Test database URL generation
            try:
                db_url = get_database_url()
                if not db_url:
                    self.add_issue(
                        "database/connection.py",
                        "Database URL is None or empty",
                        "Call get_database_url()",
                        f"Returned: {db_url}",
                        "Valid database URL string",
                        "High"
                    )
            except Exception as e:
                self.add_issue(
                    "database/connection.py:get_database_url",
                    "Database URL generation failed",
                    "Call get_database_url()",
                    f"Exception: {str(e)}",
                    "Valid database URL",
                    "High"
                )
            
            # Test database connection
            try:
                connection_result = test_connection()
                if not connection_result:
                    self.add_issue(
                        "database/connection.py:test_connection",
                        "Database connection test failed",
                        "Call test_connection()",
                        f"Returned: {connection_result}",
                        "True (successful connection)",
                        "High"
                    )
            except Exception as e:
                self.add_issue(
                    "database/connection.py:test_connection",
                    "Database connection test threw exception",
                    "Call test_connection()",
                    f"Exception: {str(e)}",
                    "Boolean result or graceful error handling",
                    "High"
                )
                
        except ImportError as e:
            self.add_issue(
                "database/connection.py",
                "Cannot import database functions",
                "Import database connection functions",
                f"ImportError: {str(e)}",
                "Successful import",
                "High"
            )
    
    def test_api_endpoints(self):
        """Test API endpoints for errors and unexpected behavior"""
        print("🌐 Testing API endpoints...")
        
        # Wait for server to be ready
        max_retries = 10
        server_ready = False
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/healthz", timeout=2)
                if response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if not server_ready:
            self.add_issue(
                "main.py",
                "API server not responding",
                f"Make GET request to {self.base_url}/healthz",
                "Connection failed or non-200 response",
                "HTTP 200 response",
                "Critical"
            )
            return
        
        # Test endpoints with various inputs
        test_cases = [
            # Health endpoints
            {"method": "GET", "path": "/healthz", "expected_status": 200},
            {"method": "GET", "path": "/health/database", "expected_status": [200, 503]},
            {"method": "GET", "path": "/health/services", "expected_status": [200, 503]},
            
            # API endpoints
            {"method": "GET", "path": "/api/v1/scholarships", "expected_status": 200},
            {"method": "GET", "path": "/search", "expected_status": [200, 422]},
            {"method": "GET", "path": "/eligibility/check", "expected_status": [200, 422]},
            
            # Edge cases
            {"method": "GET", "path": "/api/v1/scholarships?limit=-1", "expected_status": [422, 400]},
            {"method": "GET", "path": "/api/v1/scholarships?limit=99999", "expected_status": [422, 400]},
            {"method": "GET", "path": "/api/v1/scholarships?limit=abc", "expected_status": [422, 400]},
            
            # Invalid paths
            {"method": "GET", "path": "/nonexistent", "expected_status": 404},
            {"method": "POST", "path": "/api/v1/scholarships", "expected_status": [405, 422]},
            
            # SQL Injection attempts
            {"method": "GET", "path": "/api/v1/scholarships?q=' OR 1=1 --", "expected_status": [200, 422]},
            {"method": "GET", "path": "/search?q='; DROP TABLE scholarships; --", "expected_status": [200, 422]},
        ]
        
        for test_case in test_cases:
            try:
                response = requests.request(
                    test_case["method"],
                    f"{self.base_url}{test_case['path']}",
                    timeout=10
                )
                
                expected_statuses = test_case["expected_status"]
                if isinstance(expected_statuses, int):
                    expected_statuses = [expected_statuses]
                
                if response.status_code not in expected_statuses:
                    self.add_issue(
                        f"API endpoint: {test_case['path']}",
                        f"Unexpected HTTP status code",
                        f"{test_case['method']} {test_case['path']}",
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        f"HTTP {expected_statuses}",
                        "Medium"
                    )
                
                # Check for error handling
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        required_fields = ["code", "message", "status"]
                        for field in required_fields:
                            if field not in error_data:
                                self.add_issue(
                                    f"Error response: {test_case['path']}",
                                    f"Missing required field in error response",
                                    f"{test_case['method']} {test_case['path']}",
                                    f"Error response missing '{field}': {error_data}",
                                    f"Error response with '{field}' field",
                                    "Low"
                                )
                    except ValueError:
                        self.add_issue(
                            f"Error response: {test_case['path']}",
                            "Error response is not valid JSON",
                            f"{test_case['method']} {test_case['path']}",
                            f"Non-JSON response: {response.text[:100]}",
                            "Valid JSON error response",
                            "Medium"
                        )
                
            except requests.exceptions.Timeout:
                self.add_issue(
                    f"API endpoint: {test_case['path']}",
                    "Request timeout",
                    f"{test_case['method']} {test_case['path']}",
                    "Request timed out after 10 seconds",
                    "Response within reasonable time",
                    "High"
                )
            except Exception as e:
                self.add_issue(
                    f"API endpoint: {test_case['path']}",
                    "Request failed with exception",
                    f"{test_case['method']} {test_case['path']}",
                    f"Exception: {str(e)}",
                    "Successful HTTP request",
                    "High"
                )
    
    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        print("🔒 Testing security vulnerabilities...")
        
        # Test for exposed sensitive information
        sensitive_endpoints = ["/docs", "/redoc", "/openapi.json", "/_debug/config"]
        
        for endpoint in sensitive_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    # Check if this should be exposed
                    if endpoint in ["/docs", "/redoc", "/openapi.json"]:
                        # These might be intentionally exposed in development
                        self.add_issue(
                            f"Security: {endpoint}",
                            "API documentation exposed",
                            f"GET {endpoint}",
                            f"HTTP 200 - Documentation accessible",
                            "HTTP 404 in production or proper access control",
                            "Medium"
                        )
                    elif endpoint == "/_debug/config":
                        self.add_issue(
                            f"Security: {endpoint}",
                            "Debug configuration endpoint exposed",
                            f"GET {endpoint}",
                            f"HTTP 200 - Config info accessible",
                            "HTTP 404 or access control",
                            "High"
                        )
            except:
                pass  # Expected for non-existent endpoints
        
        # Test CORS configuration
        try:
            response = requests.options(
                f"{self.base_url}/api/v1/scholarships",
                headers={
                    "Origin": "https://evil.com",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=5
            )
            
            if "Access-Control-Allow-Origin" in response.headers:
                origin = response.headers["Access-Control-Allow-Origin"]
                if origin == "*":
                    self.add_issue(
                        "CORS Configuration",
                        "Wildcard CORS origin allowed",
                        "OPTIONS request with evil.com origin",
                        f"Access-Control-Allow-Origin: {origin}",
                        "Restricted CORS origins or proper validation",
                        "Medium"
                    )
        except:
            pass
        
        # Test for SQL injection protection
        sql_payloads = [
            "'; DROP TABLE scholarships; --",
            "' UNION SELECT * FROM users --",
            "1' OR '1'='1",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for payload in sql_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/scholarships",
                    params={"q": payload},
                    timeout=5
                )
                
                # Check if response suggests SQL injection vulnerability
                if response.status_code == 500:
                    self.add_issue(
                        "SQL Injection Protection",
                        "Potential SQL injection vulnerability",
                        f"GET /api/v1/scholarships?q={payload}",
                        f"HTTP 500 - Server error suggests unhandled SQL",
                        "HTTP 400/422 with input validation error",
                        "Critical"
                    )
            except:
                pass
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("🚦 Testing rate limiting...")
        
        # Test rate limiting by making rapid requests
        rapid_requests = []
        for i in range(10):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/v1/scholarships?limit=1", timeout=2)
                end_time = time.time()
                
                rapid_requests.append({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "headers": dict(response.headers)
                })
                
                if response.status_code == 429:
                    # Check rate limit headers
                    required_headers = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]
                    missing_headers = [h for h in required_headers if h not in response.headers]
                    
                    if missing_headers:
                        self.add_issue(
                            "Rate Limiting Headers",
                            f"Missing rate limit headers",
                            "Make requests until rate limited (HTTP 429)",
                            f"Missing headers: {missing_headers}",
                            f"All headers present: {required_headers}",
                            "Low"
                        )
                
                time.sleep(0.1)  # Small delay between requests
            except Exception as e:
                self.add_issue(
                    "Rate Limiting Test",
                    "Rate limiting test request failed",
                    f"Rapid request #{i+1}",
                    f"Exception: {str(e)}",
                    "Successful request or rate limit response",
                    "Medium"
                )
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("🚨 Testing error handling...")
        
        # Test with malformed requests
        error_test_cases = [
            {
                "description": "Extremely long URL",
                "method": "GET",
                "path": "/api/v1/scholarships?" + "a" * 10000,
                "expected_behavior": "Request rejected with 414 or 400"
            },
            {
                "description": "Invalid JSON in POST body",
                "method": "POST",
                "path": "/eligibility/check",
                "data": "{invalid json}",
                "expected_behavior": "400 Bad Request with JSON error"
            },
            {
                "description": "Large request body",
                "method": "POST",
                "path": "/eligibility/check",
                "data": "x" * (2 * 1024 * 1024),  # 2MB
                "expected_behavior": "413 Request Entity Too Large"
            }
        ]
        
        for test_case in error_test_cases:
            try:
                if test_case["method"] == "GET":
                    response = requests.get(f"{self.base_url}{test_case['path']}", timeout=5)
                else:
                    response = requests.post(
                        f"{self.base_url}{test_case['path']}",
                        data=test_case.get("data", ""),
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                
                # Check if error is handled appropriately
                if response.status_code == 500:
                    self.add_issue(
                        "Error Handling",
                        f"Unhandled server error: {test_case['description']}",
                        test_case['description'],
                        f"HTTP 500: {response.text[:200]}",
                        test_case['expected_behavior'],
                        "High"
                    )
                
            except requests.exceptions.Timeout:
                self.add_issue(
                    "Error Handling",
                    f"Request timeout: {test_case['description']}",
                    test_case['description'],
                    "Request timed out",
                    test_case['expected_behavior'],
                    "Medium"
                )
            except Exception as e:
                # Some exceptions might be expected (e.g., connection errors for malformed requests)
                pass
    
    def run_static_analysis(self):
        """Run static analysis tools if available"""
        print("🔍 Running static analysis...")
        
        # Try to run flake8 if available
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", ".", "--count", "--statistics"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0 and result.stdout:
                self.add_issue(
                    "Static Analysis",
                    "Flake8 code quality issues found",
                    "Run flake8 on codebase",
                    f"Flake8 output: {result.stdout[:500]}",
                    "No code quality issues",
                    "Low"
                )
        except:
            pass  # flake8 not available
        
        # Try to run bandit for security analysis
        try:
            result = subprocess.run(
                ["python", "-m", "bandit", "-r", ".", "-f", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0 and result.stdout:
                try:
                    bandit_results = json.loads(result.stdout)
                    if bandit_results.get("results"):
                        for issue in bandit_results["results"][:5]:  # Limit to first 5
                            self.add_issue(
                                f"{issue.get('filename', 'unknown')}:{issue.get('line_number', 'unknown')}",
                                f"Security issue: {issue.get('test_name', 'unknown')}",
                                "Run bandit security analysis",
                                f"Issue: {issue.get('issue_text', 'unknown')}",
                                "No security issues",
                                "High" if issue.get("issue_severity") == "HIGH" else "Medium"
                            )
                except:
                    pass
        except:
            pass  # bandit not available
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE QA ANALYSIS REPORT")
        print("="*80)
        
        # Summary
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for issue in self.issues:
            severity_counts[issue["severity"]] += 1
        
        print(f"\n📈 SUMMARY:")
        print(f"Total Issues Found: {len(self.issues)}")
        print(f"Critical: {severity_counts['Critical']}")
        print(f"High: {severity_counts['High']}")
        print(f"Medium: {severity_counts['Medium']}")
        print(f"Low: {severity_counts['Low']}")
        
        # Detailed issues
        if self.issues:
            print(f"\n🔍 DETAILED FINDINGS:")
            print("-" * 80)
            
            for issue in sorted(self.issues, key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}[x["severity"]]):
                print(f"\n{issue['issue_id']} [{issue['severity']}] - {issue['description']}")
                print(f"Location: {issue['location']}")
                print(f"Steps to Reproduce: {issue['steps_to_reproduce']}")
                print(f"Observed Output: {issue['observed_output']}")
                print(f"Expected Output: {issue['expected_output']}")
                print("-" * 40)
        else:
            print("\n✅ No issues found in the analysis!")
        
        # Save detailed report
        report_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": severity_counts,
            "total_issues": len(self.issues),
            "issues": self.issues
        }
        
        with open("qa_comprehensive_analysis_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: qa_comprehensive_analysis_report.json")
        
        return len(self.issues) == 0

def main():
    """Run comprehensive QA analysis"""
    print("🔬 Starting Comprehensive QA Analysis...")
    print("IMPORTANT: This is analysis-only - no code will be modified")
    
    analyzer = QAAnalyzer()
    
    try:
        # Run all analysis phases
        analyzer.analyze_imports_and_dependencies()
        analyzer.test_configuration_loading()
        analyzer.test_database_operations()
        analyzer.test_api_endpoints()
        analyzer.test_security_vulnerabilities()
        analyzer.test_rate_limiting()
        analyzer.test_error_handling()
        analyzer.run_static_analysis()
        
        # Generate final report
        success = analyzer.generate_report()
        
        if success:
            print("\n🎉 QA Analysis completed - No critical issues found!")
            return 0
        else:
            print("\n⚠️ QA Analysis completed - Issues found and documented!")
            return 1
            
    except Exception as e:
        print(f"\n💥 QA Analysis failed with exception: {str(e)}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())