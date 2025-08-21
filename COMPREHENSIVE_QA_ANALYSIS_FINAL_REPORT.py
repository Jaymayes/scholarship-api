#!/usr/bin/env python3
"""
Senior QA Engineer - Comprehensive Codebase Analysis and Test Execution
OBJECTIVE: Identify and report all errors, bugs, unexpected behavior, and potential vulnerabilities
CONSTRAINT: NO MODIFICATIONS TO EXISTING CODE - ANALYSIS AND REPORTING ONLY
"""

import os
import sys
import subprocess
import json
import traceback
from pathlib import Path
import importlib.util
import ast
import re
from typing import List, Dict, Any
import time
import requests

class QAAnalysisEngine:
    def __init__(self):
        self.findings = []
        self.test_results = []
        self.current_issue_id = 1
        self.project_root = Path(".")
        
    def add_finding(self, location: str, description: str, severity: str, 
                   steps_to_reproduce: str = "", observed_output: str = "", 
                   expected_output: str = ""):
        """Add a finding to the report"""
        finding = {
            "issue_id": f"QA-{self.current_issue_id:03d}",
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity
        }
        self.findings.append(finding)
        self.current_issue_id += 1
        
    def analyze_file_structure(self):
        """Analyze project structure for potential issues"""
        print("🔍 Analyzing project structure...")
        
        # Check for critical files
        critical_files = ["main.py", "requirements.txt", "pyproject.toml"]
        for file in critical_files:
            if not (self.project_root / file).exists():
                if file != "requirements.txt":  # pyproject.toml is used instead
                    self.add_finding(
                        location=f"Project root/{file}",
                        description=f"Missing critical file: {file}",
                        severity="Medium",
                        steps_to_reproduce=f"Check for existence of {file} in project root",
                        observed_output=f"{file} not found",
                        expected_output=f"{file} should exist for proper project setup"
                    )
                    
    def analyze_python_syntax(self):
        """Analyze Python files for syntax errors"""
        print("🔍 Analyzing Python syntax...")
        
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            if ".pythonlibs" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for syntax errors
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    self.add_finding(
                        location=f"{py_file}:{e.lineno}",
                        description=f"Syntax error: {e.msg}",
                        severity="Critical",
                        steps_to_reproduce=f"Parse file {py_file}",
                        observed_output=str(e),
                        expected_output="Valid Python syntax"
                    )
                    
                # Check for common issues
                self._check_common_python_issues(py_file, content)
                
            except Exception as e:
                self.add_finding(
                    location=str(py_file),
                    description=f"Failed to analyze file: {str(e)}",
                    severity="Medium",
                    steps_to_reproduce=f"Read and parse {py_file}",
                    observed_output=str(e),
                    expected_output="File should be readable and parseable"
                )
                
    def _check_common_python_issues(self, file_path: Path, content: str):
        """Check for common Python coding issues"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for potential security issues
            if re.search(r'eval\(|exec\(', line):
                self.add_finding(
                    location=f"{file_path}:{i}",
                    description="Potential security risk: use of eval() or exec()",
                    severity="High",
                    steps_to_reproduce=f"Review line {i} in {file_path}",
                    observed_output=line.strip(),
                    expected_output="Use safer alternatives to eval/exec"
                )
                
            # Check for hardcoded credentials
            if re.search(r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                self.add_finding(
                    location=f"{file_path}:{i}",
                    description="Potential hardcoded credentials",
                    severity="High",
                    steps_to_reproduce=f"Review line {i} in {file_path}",
                    observed_output=line.strip(),
                    expected_output="Use environment variables for credentials"
                )
                
            # Check for deprecated imports
            if 'from fastapi import' in line and 'on_event' in content:
                self.add_finding(
                    location=f"{file_path}:{i}",
                    description="Deprecated FastAPI @app.on_event usage detected",
                    severity="Medium",
                    steps_to_reproduce=f"Search for on_event usage in {file_path}",
                    observed_output="@app.on_event found in file",
                    expected_output="Use lifespan context manager instead"
                )
                
    def test_api_endpoints(self):
        """Test API endpoints for functionality and errors"""
        print("🔍 Testing API endpoints...")
        
        base_url = "http://localhost:5000"
        
        # Test basic endpoints
        endpoints_to_test = [
            {"path": "/", "method": "GET", "expected_status": 200},
            {"path": "/healthz", "method": "GET", "expected_status": 200},
            {"path": "/readyz", "method": "GET", "expected_status": [200, 503]},
            {"path": "/docs", "method": "GET", "expected_status": 200},
            {"path": "/api/v1/scholarships", "method": "GET", "expected_status": 200},
            {"path": "/api/v1/search", "method": "GET", "expected_status": 200},
            {"path": "/db/status", "method": "GET", "expected_status": 200},
            {"path": "/agent/health", "method": "GET", "expected_status": 200},
            {"path": "/agent/capabilities", "method": "GET", "expected_status": 200},
            {"path": "/ai/status", "method": "GET", "expected_status": 200},
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint['path']}", timeout=10)
                expected = endpoint["expected_status"]
                
                if isinstance(expected, list):
                    if response.status_code not in expected:
                        self.add_finding(
                            location=f"API endpoint {endpoint['path']}",
                            description=f"Unexpected status code",
                            severity="Medium",
                            steps_to_reproduce=f"GET {base_url}{endpoint['path']}",
                            observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                            expected_output=f"Status code in {expected}"
                        )
                else:
                    if response.status_code != expected:
                        self.add_finding(
                            location=f"API endpoint {endpoint['path']}",
                            description=f"Unexpected status code",
                            severity="Medium",
                            steps_to_reproduce=f"GET {base_url}{endpoint['path']}",
                            observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                            expected_output=f"Status code {expected}"
                        )
                        
            except requests.exceptions.RequestException as e:
                self.add_finding(
                    location=f"API endpoint {endpoint['path']}",
                    description=f"Failed to connect to endpoint: {str(e)}",
                    severity="Critical",
                    steps_to_reproduce=f"GET {base_url}{endpoint['path']}",
                    observed_output=str(e),
                    expected_output="Successful HTTP response"
                )
                
    def test_eligibility_endpoint_edge_cases(self):
        """Test eligibility endpoint with edge cases"""
        print("🔍 Testing eligibility endpoint edge cases...")
        
        base_url = "http://localhost:5000"
        
        # Test cases with various invalid inputs
        test_cases = [
            {
                "name": "Empty request body",
                "data": {},
                "expected_status": 422
            },
            {
                "name": "Invalid GPA - too high",
                "data": {"gpa": 5.0, "field_of_study": "engineering"},
                "expected_status": 422
            },
            {
                "name": "Invalid GPA - negative",
                "data": {"gpa": -1.0, "field_of_study": "engineering"},
                "expected_status": 422
            },
            {
                "name": "Invalid field of study",
                "data": {"gpa": 3.5, "field_of_study": "invalid_field"},
                "expected_status": 422
            },
            {
                "name": "Invalid citizenship",
                "data": {"gpa": 3.5, "field_of_study": "engineering", "citizenship": "invalid_citizenship"},
                "expected_status": 422
            },
            {
                "name": "SQL injection attempt in scholarship_id",
                "data": {"gpa": 3.5, "field_of_study": "engineering", "scholarship_id": "'; DROP TABLE scholarships; --"},
                "expected_status": [200, 422]
            },
            {
                "name": "XSS attempt in string fields",
                "data": {"gpa": 3.5, "field_of_study": "engineering", "scholarship_id": "<script>alert('xss')</script>"},
                "expected_status": [200, 422]
            }
        ]
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{base_url}/api/v1/eligibility/check",
                    json=test_case["data"],
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
                
                expected = test_case["expected_status"]
                if isinstance(expected, list):
                    if response.status_code not in expected:
                        self.add_finding(
                            location="API endpoint /api/v1/eligibility/check",
                            description=f"Edge case test failed: {test_case['name']}",
                            severity="Medium",
                            steps_to_reproduce=f"POST {base_url}/api/v1/eligibility/check with data: {test_case['data']}",
                            observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                            expected_output=f"Status code in {expected}"
                        )
                else:
                    if response.status_code != expected:
                        self.add_finding(
                            location="API endpoint /api/v1/eligibility/check",
                            description=f"Edge case test failed: {test_case['name']}",
                            severity="Medium",
                            steps_to_reproduce=f"POST {base_url}/api/v1/eligibility/check with data: {test_case['data']}",
                            observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                            expected_output=f"Status code {expected}"
                        )
                        
            except requests.exceptions.RequestException as e:
                self.add_finding(
                    location="API endpoint /api/v1/eligibility/check",
                    description=f"Network error during edge case test: {test_case['name']} - {str(e)}",
                    severity="High",
                    steps_to_reproduce=f"POST {base_url}/api/v1/eligibility/check with data: {test_case['data']}",
                    observed_output=str(e),
                    expected_output="Successful HTTP response"
                )
                
    def test_database_operations(self):
        """Test database-related functionality"""
        print("🔍 Testing database operations...")
        
        base_url = "http://localhost:5000"
        
        try:
            # Test database status
            response = requests.get(f"{base_url}/db/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data.get("database", {}).get("connected"):
                    self.add_finding(
                        location="Database connection",
                        description="Database reported as not connected",
                        severity="Critical",
                        steps_to_reproduce="GET /db/status",
                        observed_output=str(data),
                        expected_output="Database should be connected: true"
                    )
                    
                # Check for reasonable scholarship count
                scholarship_count = data.get("database", {}).get("scholarships", 0)
                if scholarship_count == 0:
                    self.add_finding(
                        location="Database data",
                        description="No scholarships found in database",
                        severity="High",
                        steps_to_reproduce="GET /db/status and check scholarship count",
                        observed_output=f"Scholarship count: {scholarship_count}",
                        expected_output="Should have scholarship data loaded"
                    )
                    
        except Exception as e:
            self.add_finding(
                location="Database status endpoint",
                description=f"Failed to check database status: {str(e)}",
                severity="Critical",
                steps_to_reproduce="GET /db/status",
                observed_output=str(e),
                expected_output="Successful database status response"
            )
            
    def test_agent_bridge_functionality(self):
        """Test Agent Bridge orchestration functionality"""
        print("🔍 Testing Agent Bridge functionality...")
        
        base_url = "http://localhost:5000"
        
        try:
            # Test agent capabilities
            response = requests.get(f"{base_url}/agent/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                capabilities = data.get("capabilities", [])
                
                expected_capabilities = [
                    "scholarship_api.search",
                    "scholarship_api.eligibility_check", 
                    "scholarship_api.recommendations",
                    "scholarship_api.analytics"
                ]
                
                for expected_cap in expected_capabilities:
                    if expected_cap not in capabilities:
                        self.add_finding(
                            location="Agent Bridge capabilities",
                            description=f"Missing expected capability: {expected_cap}",
                            severity="High",
                            steps_to_reproduce="GET /agent/capabilities",
                            observed_output=f"Capabilities: {capabilities}",
                            expected_output=f"Should include {expected_cap}"
                        )
                        
            # Test agent task execution with invalid data
            invalid_task_data = {
                "task_id": "test-invalid",
                "capability": "invalid_capability",
                "parameters": {},
                "requester": "qa_test"
            }
            
            response = requests.post(
                f"{base_url}/agent/execute",
                json=invalid_task_data,
                timeout=10
            )
            
            # Should handle invalid capability gracefully
            if response.status_code not in [400, 422, 404]:
                self.add_finding(
                    location="Agent Bridge task execution",
                    description="Invalid capability not properly rejected",
                    severity="Medium",
                    steps_to_reproduce=f"POST /agent/execute with invalid capability: {invalid_task_data}",
                    observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                    expected_output="Should return 400/422/404 for invalid capability"
                )
                
        except Exception as e:
            self.add_finding(
                location="Agent Bridge endpoints",
                description=f"Failed to test Agent Bridge: {str(e)}",
                severity="High",
                steps_to_reproduce="Test Agent Bridge endpoints",
                observed_output=str(e),
                expected_output="Agent Bridge should be accessible and functional"
            )
            
    def test_ai_service_integration(self):
        """Test AI service integration and error handling"""
        print("🔍 Testing AI service integration...")
        
        base_url = "http://localhost:5000"
        
        try:
            # Test AI status
            response = requests.get(f"{base_url}/ai/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data.get("ai_service_available"):
                    self.add_finding(
                        location="AI service integration",
                        description="AI service reported as unavailable",
                        severity="Medium",  # Medium because it should gracefully degrade
                        steps_to_reproduce="GET /ai/status",
                        observed_output=str(data),
                        expected_output="AI service should be available or gracefully degrade"
                    )
                    
            # Test AI endpoints with invalid data
            invalid_scholarship_id = "invalid_id_that_does_not_exist"
            response = requests.get(f"{base_url}/api/v1/ai/scholarship-summary/{invalid_scholarship_id}", timeout=10)
            
            # Should handle invalid IDs gracefully
            if response.status_code not in [404, 422, 400]:
                self.add_finding(
                    location="AI scholarship summary endpoint",
                    description="Invalid scholarship ID not properly handled",
                    severity="Medium",
                    steps_to_reproduce=f"GET /api/v1/ai/scholarship-summary/{invalid_scholarship_id}",
                    observed_output=f"Status: {response.status_code}, Response: {response.text[:200]}",
                    expected_output="Should return 404/422/400 for invalid scholarship ID"
                )
                
        except Exception as e:
            self.add_finding(
                location="AI service endpoints",
                description=f"Failed to test AI service: {str(e)}",
                severity="Medium",
                steps_to_reproduce="Test AI service endpoints",
                observed_output=str(e),
                expected_output="AI service should be accessible with graceful degradation"
            )
            
    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        print("🔍 Testing security vulnerabilities...")
        
        base_url = "http://localhost:5000"
        
        # Test for information disclosure
        sensitive_paths = [
            "/.env",
            "/config",
            "/admin",
            "/../etc/passwd",
            "/api/v1/admin",
            "/debug",
            "/console"
        ]
        
        for path in sensitive_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code == 200 and len(response.text) > 100:
                    self.add_finding(
                        location=f"Endpoint {path}",
                        description="Potential information disclosure - sensitive path accessible",
                        severity="High",
                        steps_to_reproduce=f"GET {base_url}{path}",
                        observed_output=f"Status: 200, Content length: {len(response.text)}",
                        expected_output="Sensitive paths should return 404 or be protected"
                    )
            except:
                pass  # Expected for most paths
                
        # Test CORS configuration
        try:
            response = requests.options(f"{base_url}/api/v1/scholarships", 
                                      headers={"Origin": "http://malicious-site.com"}, 
                                      timeout=5)
            cors_header = response.headers.get("Access-Control-Allow-Origin", "")
            if cors_header == "*":
                self.add_finding(
                    location="CORS configuration",
                    description="Wildcard CORS policy detected - potential security risk",
                    severity="Medium",
                    steps_to_reproduce="OPTIONS request with malicious origin",
                    observed_output=f"Access-Control-Allow-Origin: {cors_header}",
                    expected_output="CORS should be restricted to specific domains in production"
                )
        except:
            pass
            
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("🔍 Testing rate limiting...")
        
        base_url = "http://localhost:5000"
        
        # Test rapid requests to trigger rate limiting
        rapid_requests = []
        for i in range(20):
            try:
                response = requests.get(f"{base_url}/api/v1/scholarships", timeout=2)
                rapid_requests.append(response.status_code)
            except:
                rapid_requests.append(0)
                
        # Check if rate limiting was triggered
        rate_limited = any(status == 429 for status in rapid_requests)
        if not rate_limited:
            self.add_finding(
                location="Rate limiting middleware",
                description="Rate limiting not triggered with rapid requests",
                severity="Medium",
                steps_to_reproduce="Send 20 rapid requests to /api/v1/scholarships",
                observed_output=f"Status codes: {rapid_requests}",
                expected_output="Should receive 429 (Too Many Requests) for some requests"
            )
            
    def analyze_configuration_files(self):
        """Analyze configuration files for issues"""
        print("🔍 Analyzing configuration files...")
        
        config_files = [
            "pyproject.toml",
            ".env.example", 
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Check for potential issues in config files
                    if config_file == "pyproject.toml":
                        # Check for dependency vulnerabilities (basic check)
                        if "fastapi" in content:
                            # Look for version specifications
                            if not re.search(r'fastapi\s*=\s*["\'][>=^~]', content):
                                self.add_finding(
                                    location=f"{config_file}",
                                    description="FastAPI dependency without version constraint",
                                    severity="Low",
                                    steps_to_reproduce=f"Review dependencies in {config_file}",
                                    observed_output="FastAPI dependency found without version constraint",
                                    expected_output="Dependencies should have version constraints"
                                )
                                
                except Exception as e:
                    self.add_finding(
                        location=f"{config_file}",
                        description=f"Failed to analyze configuration file: {str(e)}",
                        severity="Low",
                        steps_to_reproduce=f"Read and analyze {config_file}",
                        observed_output=str(e),
                        expected_output="Configuration file should be readable"
                    )
                    
    def run_static_analysis(self):
        """Run additional static analysis checks"""
        print("🔍 Running static analysis...")
        
        # Check for TODO/FIXME comments that might indicate incomplete code
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            if ".pythonlibs" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                        self.add_finding(
                            location=f"{py_file}:{i}",
                            description=f"Incomplete code marker found: {line.strip()}",
                            severity="Low",
                            steps_to_reproduce=f"Review line {i} in {py_file}",
                            observed_output=line.strip(),
                            expected_output="Production code should not contain TODO/FIXME markers"
                        )
                        
            except Exception as e:
                continue
                
    def generate_report(self):
        """Generate comprehensive QA report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE QA ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n🎯 EXECUTIVE SUMMARY")
        print(f"Total Issues Found: {len(self.findings)}")
        
        severity_counts = {}
        for finding in self.findings:
            severity = finding['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        print(f"Critical: {severity_counts.get('Critical', 0)}")
        print(f"High: {severity_counts.get('High', 0)}")
        print(f"Medium: {severity_counts.get('Medium', 0)}")
        print(f"Low: {severity_counts.get('Low', 0)}")
        
        print(f"\n📊 DETAILED FINDINGS")
        print("-" * 80)
        
        for finding in self.findings:
            print(f"\n🐛 {finding['issue_id']}: {finding['description']}")
            print(f"📍 Location: {finding['location']}")
            print(f"⚠️  Severity: {finding['severity']}")
            print(f"🔄 Steps to Reproduce: {finding['steps_to_reproduce']}")
            print(f"📤 Observed Output: {finding['observed_output']}")
            print(f"✅ Expected Output: {finding['expected_output']}")
            print("-" * 40)
            
        # Save detailed report to JSON
        report_data = {
            "summary": {
                "total_issues": len(self.findings),
                "severity_breakdown": severity_counts,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "findings": self.findings
        }
        
        with open("qa_comprehensive_analysis_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: qa_comprehensive_analysis_report.json")
        
        return len(self.findings), severity_counts

def main():
    """Main QA analysis execution"""
    print("🚀 Starting Comprehensive QA Analysis")
    print("⚠️  ANALYSIS ONLY - NO CODE MODIFICATIONS WILL BE MADE")
    print("="*80)
    
    qa_engine = QAAnalysisEngine()
    
    try:
        # Execute all analysis components
        qa_engine.analyze_file_structure()
        qa_engine.analyze_python_syntax()
        qa_engine.analyze_configuration_files()
        qa_engine.run_static_analysis()
        
        # API testing (requires running server)
        qa_engine.test_api_endpoints()
        qa_engine.test_eligibility_endpoint_edge_cases()
        qa_engine.test_database_operations()
        qa_engine.test_agent_bridge_functionality()
        qa_engine.test_ai_service_integration()
        qa_engine.test_security_vulnerabilities()
        qa_engine.test_rate_limiting()
        
        # Generate final report
        total_issues, severity_counts = qa_engine.generate_report()
        
        print(f"\n🎯 QA ANALYSIS COMPLETE")
        print(f"Found {total_issues} total issues across {len(severity_counts)} severity levels")
        print("Review the detailed report above and in qa_comprehensive_analysis_report.json")
        
        return total_issues
        
    except Exception as e:
        print(f"❌ QA Analysis failed with error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return -1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(0 if exit_code >= 0 else 1)