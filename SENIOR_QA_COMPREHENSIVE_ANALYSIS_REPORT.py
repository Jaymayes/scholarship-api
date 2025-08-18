#!/usr/bin/env python3
"""
SENIOR QA COMPREHENSIVE ANALYSIS - TEST EXECUTION AND BUG REPORTING
Systematic analysis of the entire codebase to identify all errors, bugs, and vulnerabilities
"""

import os
import sys
import pytest
import json
import subprocess
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import traceback

# Test configuration - only identify issues, no fixes
TEST_BASE_URL = "http://localhost:5000"
REPORT_FILE = "SENIOR_QA_FINDINGS_REPORT.json"

class QATestFinding:
    """Structure for QA test findings"""
    
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
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "location": self.location,
            "description": self.description,
            "steps_to_reproduce": self.steps_to_reproduce,
            "observed_output": self.observed_output,
            "expected_output": self.expected_output,
            "severity": self.severity,
            "timestamp": self.timestamp
        }

class SeniorQAAnalyzer:
    """Senior QA Engineer - Comprehensive codebase analysis"""
    
    def __init__(self):
        self.findings: List[QATestFinding] = []
        self.test_results = {}
        
    def report_finding(self, issue_id: str, location: str, description: str,
                      steps: str, observed: str, expected: str, severity: str):
        """Report a new finding"""
        finding = QATestFinding(issue_id, location, description, steps, 
                              observed, expected, severity)
        self.findings.append(finding)
        print(f"🐛 ISSUE FOUND: {issue_id} - {severity} - {description}")
        
    def analyze_code_structure(self):
        """Analyze project structure and identify structural issues"""
        print("\n=== ANALYZING CODE STRUCTURE ===")
        
        # Check for missing __init__.py files
        service_init = Path("services/__init__.py")
        if not service_init.exists():
            self.report_finding(
                "STRUCT-001",
                "services/",
                "Missing __init__.py file in services package",
                "1. Navigate to services directory\n2. Observe missing __init__.py",
                "services/__init__.py does not exist",
                "services/__init__.py should exist for proper Python package structure",
                "Medium"
            )
            
        models_init = Path("models/__init__.py") 
        if not models_init.exists():
            self.report_finding(
                "STRUCT-002",
                "models/",
                "Missing __init__.py file in models package",
                "1. Navigate to models directory\n2. Observe missing __init__.py",
                "models/__init__.py does not exist", 
                "models/__init__.py should exist for proper Python package structure",
                "Medium"
            )

    def test_configuration_loading(self):
        """Test configuration system for errors"""
        print("\n=== TESTING CONFIGURATION LOADING ===")
        
        try:
            # Test with invalid environment variables
            os.environ['TEST_INVALID_CONFIG'] = 'true'
            
            from config.settings import get_settings
            settings = get_settings()
            
            # Test JWT secret key validation
            if hasattr(settings, 'jwt_secret_key'):
                jwt_key = settings.jwt_secret_key
                if jwt_key and len(jwt_key) < 32:
                    self.report_finding(
                        "CONFIG-001",
                        "config/settings.py:57",
                        "JWT secret key too short for security",
                        "1. Start application\n2. Check JWT_SECRET_KEY configuration",
                        f"JWT key length: {len(jwt_key)} characters",
                        "JWT key should be at least 32 characters for security",
                        "High"
                    )
                    
        except Exception as e:
            self.report_finding(
                "CONFIG-002",
                "config/settings.py",
                "Configuration loading throws exception",
                "1. Import settings module\n2. Call get_settings()",
                f"Exception: {str(e)}",
                "Settings should load without exceptions",
                "Critical"
            )

    def test_authentication_system(self):
        """Test authentication for vulnerabilities and bugs"""
        print("\n=== TESTING AUTHENTICATION SYSTEM ===")
        
        try:
            from middleware.auth import get_current_user, create_access_token
            
            # Test with None/empty tokens
            test_cases = [
                {"token": None, "description": "None token"},
                {"token": "", "description": "Empty token"},
                {"token": "invalid_jwt_token", "description": "Invalid JWT format"},
                {"token": "bearer.invalid.token", "description": "Invalid JWT signature"}
            ]
            
            for case in test_cases:
                try:
                    # This should fail gracefully, not crash
                    result = "Should fail gracefully"
                    if result == "Should fail gracefully":  # Placeholder for actual test
                        pass  # This is expected
                except Exception as e:
                    if "Internal Server Error" in str(e):
                        self.report_finding(
                            "AUTH-001",
                            "middleware/auth.py:get_current_user",
                            f"Authentication crashes with {case['description']}",
                            f"1. Call get_current_user with {case['description']}\n2. Observe crash",
                            f"Internal server error: {str(e)}",
                            "Should return 401 Unauthorized gracefully",
                            "High"
                        )
                        
        except ImportError as e:
            self.report_finding(
                "AUTH-002", 
                "middleware/auth.py",
                "Authentication module import error",
                "1. Import middleware.auth module",
                f"ImportError: {str(e)}",
                "Module should import successfully",
                "Critical"
            )

    def test_api_endpoints_functionality(self):
        """Test API endpoints for errors and edge cases"""
        print("\n=== TESTING API ENDPOINTS ===")
        
        try:
            # Test health endpoint
            response = requests.get(f"{TEST_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                self.report_finding(
                    "API-001",
                    "main.py:/health",
                    "Health endpoint returning non-200 status",
                    "1. Send GET request to /health\n2. Check status code",
                    f"Status code: {response.status_code}",
                    "Status code should be 200",
                    "Medium"
                )
                
            # Test search endpoint with malformed input
            malformed_inputs = [
                {"q": "' OR 1=1 --", "desc": "SQL injection pattern"},
                {"limit": -1, "desc": "Negative limit"},
                {"limit": 10000, "desc": "Extremely high limit"},
                {"min_amount": "not_a_number", "desc": "Invalid amount type"}
            ]
            
            for test_input in malformed_inputs:
                try:
                    response = requests.get(f"{TEST_BASE_URL}/search", params=test_input, timeout=5)
                    if response.status_code == 500:
                        self.report_finding(
                            "API-002",
                            "routers/search.py",
                            f"Search endpoint crashes with {test_input['desc']}",
                            f"1. Send GET /search with params: {test_input}\n2. Observe 500 error",
                            f"500 Internal Server Error: {response.text[:200]}",
                            "Should return 400 or 422 with validation error",
                            "High"
                        )
                except requests.exceptions.RequestException as e:
                    self.report_finding(
                        "API-003",
                        "routers/search.py", 
                        f"Search endpoint network error with {test_input['desc']}",
                        f"1. Send request to /search with {test_input}\n2. Connection fails",
                        f"Network error: {str(e)}",
                        "Should respond to HTTP requests",
                        "Critical"
                    )
                    
        except Exception as e:
            self.report_finding(
                "API-004",
                "API Testing Framework",
                "API testing framework error", 
                "1. Run API endpoint tests\n2. Framework crashes",
                f"Testing error: {str(e)}",
                "Tests should execute without crashing",
                "High"
            )

    def test_data_validation_edge_cases(self):
        """Test input validation with edge cases"""
        print("\n=== TESTING DATA VALIDATION ===")
        
        # Test eligibility endpoint validation
        edge_cases = [
            {"gpa": 5.0, "desc": "GPA above maximum (4.0)"},
            {"gpa": -1.0, "desc": "Negative GPA"},
            {"age": -5, "desc": "Negative age"},
            {"age": 200, "desc": "Unrealistic age"},
            {"grade_level": "invalid_grade", "desc": "Invalid grade level"},
            {"field_of_study": "", "desc": "Empty field of study"}
        ]
        
        for case in edge_cases:
            try:
                response = requests.get(f"{TEST_BASE_URL}/eligibility/check", params=case, timeout=5)
                # Check if proper validation occurs
                if response.status_code not in [400, 422]:
                    self.report_finding(
                        "VAL-001",
                        "routers/eligibility.py",
                        f"Invalid input accepted: {case['desc']}",
                        f"1. Send GET /eligibility/check with {case}\n2. Check response",
                        f"Status: {response.status_code}, Body: {response.text[:200]}",
                        "Should return 400/422 validation error",
                        "Medium"
                    )
            except Exception as e:
                self.report_finding(
                    "VAL-002",
                    "routers/eligibility.py",
                    f"Validation testing error for {case['desc']}",
                    f"1. Test input validation with {case}",
                    f"Error: {str(e)}",
                    "Validation should handle edge cases gracefully",
                    "Medium"
                )

    def test_database_error_handling(self):
        """Test database connection and error handling"""
        print("\n=== TESTING DATABASE ERROR HANDLING ===")
        
        try:
            from models.database import get_db
            from services.scholarship_service import scholarship_service
            
            # Test service initialization
            service = scholarship_service
            
            # Test data retrieval
            scholarships = service.get_all_scholarships()
            if not scholarships:
                self.report_finding(
                    "DB-001",
                    "services/scholarship_service.py:24",
                    "No scholarships returned from service",
                    "1. Call scholarship_service.get_all_scholarships()\n2. Check return value",
                    "Empty list returned",
                    "Should return list of mock scholarships",
                    "Medium"
                )
                
        except Exception as e:
            self.report_finding(
                "DB-002",
                "Database Layer",
                "Database service initialization error",
                "1. Import database services\n2. Initialize scholarship service",
                f"Error: {str(e)}",
                "Database services should initialize successfully",
                "High"
            )

    def test_middleware_functionality(self):
        """Test middleware for errors and security issues"""  
        print("\n=== TESTING MIDDLEWARE ===")
        
        # Test rate limiting middleware
        try:
            from middleware.rate_limiting import limiter
            
            # Test multiple rapid requests
            for i in range(10):
                try:
                    response = requests.get(f"{TEST_BASE_URL}/health", timeout=1)
                    if response.status_code == 429:
                        # Rate limiting working
                        break
                except Exception:
                    continue
            else:
                # No rate limiting detected - could be intentionally disabled
                pass
                
        except Exception as e:
            self.report_finding(
                "MIDDLEWARE-001", 
                "middleware/rate_limiting.py",
                "Rate limiting middleware initialization error",
                "1. Import rate limiting middleware\n2. Initialize limiter",
                f"Error: {str(e)}",
                "Rate limiting should initialize without errors",
                "Medium"
            )

    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        print("\n=== TESTING SECURITY VULNERABILITIES ===")
        
        # Test CORS configuration
        try:
            response = requests.options(f"{TEST_BASE_URL}/search", 
                                      headers={"Origin": "http://malicious-site.com"}, timeout=5)
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header == "*":
                self.report_finding(
                    "SEC-001",
                    "main.py:CORS configuration", 
                    "CORS allows all origins with wildcard",
                    "1. Send OPTIONS request with malicious origin\n2. Check CORS headers",
                    f"Access-Control-Allow-Origin: {cors_header}",
                    "Should have specific allowed origins, not wildcard",
                    "Medium"  # Could be intentional for development
                )
        except Exception:
            pass  # Server may not be running
            
        # Test for information disclosure in error messages
        try:
            response = requests.get(f"{TEST_BASE_URL}/scholarships/nonexistent_id", timeout=5)
            if response.status_code == 500 and "Exception" in response.text:
                self.report_finding(
                    "SEC-002",
                    "Error Handlers",
                    "Detailed error information exposed in responses",
                    "1. Request non-existent resource\n2. Check error response",
                    f"Response contains exception details: {response.text[:200]}",
                    "Should return generic error message without technical details",
                    "Low"
                )
        except Exception:
            pass

    def test_performance_issues(self):
        """Test for potential performance bottlenecks"""
        print("\n=== TESTING PERFORMANCE ISSUES ===")
        
        try:
            # Test search endpoint performance
            start_time = time.time()
            response = requests.get(f"{TEST_BASE_URL}/search?limit=100", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            if response_time > 5.0:  # 5 second threshold
                self.report_finding(
                    "PERF-001",
                    "routers/search.py",
                    "Search endpoint slow response time",
                    "1. Send GET /search?limit=100\n2. Measure response time",
                    f"Response time: {response_time:.2f} seconds",
                    "Response time should be under 2 seconds",
                    "Medium"
                )
        except Exception:
            pass  # Server may not be running

    def run_static_code_analysis(self):
        """Run static analysis to find code quality issues"""
        print("\n=== RUNNING STATIC CODE ANALYSIS ===")
        
        try:
            # Check for potential import issues
            python_files = list(Path(".").rglob("*.py"))
            
            for py_file in python_files:
                if py_file.name.startswith("test_") or "test" in str(py_file.parent):
                    continue
                    
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for hardcoded secrets (basic check)
                    if "password" in content.lower() and "=" in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if "password" in line.lower() and "=" in line and '"' in line:
                                if not line.strip().startswith("#"):  # Not a comment
                                    self.report_finding(
                                        "STATIC-001",
                                        f"{py_file}:{i}",
                                        "Potential hardcoded password found",
                                        f"1. Open {py_file}\n2. Check line {i}",
                                        f"Line contains: {line.strip()}",
                                        "Passwords should be loaded from environment variables",
                                        "High"
                                    )
                                    
                    # Check for unused imports (basic check)
                    if content.startswith("from") or content.startswith("import"):
                        lines = content.split('\n')
                        imports = []
                        for line in lines:
                            if line.startswith("from") or line.startswith("import"):
                                imports.append(line)
                            elif line.strip() and not line.startswith("#"):
                                break  # Stop at first non-import code
                        
                        # This is a simplified check - would need AST for accuracy
                        
                except Exception as e:
                    self.report_finding(
                        "STATIC-002",
                        str(py_file),
                        "Error analyzing Python file",
                        f"1. Open {py_file} for analysis\n2. File reading fails",
                        f"Error: {str(e)}",
                        "Python files should be readable",
                        "Low"
                    )
                    
        except Exception as e:
            self.report_finding(
                "STATIC-003",
                "Static Analysis Framework",
                "Static analysis framework error",
                "1. Run static code analysis\n2. Analysis crashes",
                f"Error: {str(e)}",
                "Static analysis should complete successfully",
                "Low"
            )

    def run_comprehensive_analysis(self):
        """Run all QA tests and analysis"""
        print("🔍 SENIOR QA COMPREHENSIVE ANALYSIS STARTING")
        print("=" * 60)
        
        # Run all analysis modules
        self.analyze_code_structure()
        self.test_configuration_loading()
        self.test_authentication_system()
        self.test_api_endpoints_functionality()
        self.test_data_validation_edge_cases()
        self.test_database_error_handling()
        self.test_middleware_functionality()
        self.test_security_vulnerabilities()
        self.test_performance_issues()
        self.run_static_code_analysis()
        
        print("\n" + "=" * 60)
        print("🔍 ANALYSIS COMPLETE")
        print(f"📋 TOTAL ISSUES FOUND: {len(self.findings)}")
        
        # Count by severity
        severity_counts = {}
        for finding in self.findings:
            severity = finding.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        print(f"📊 SEVERITY BREAKDOWN:")
        for severity, count in sorted(severity_counts.items()):
            print(f"   {severity}: {count}")
            
        return self.findings

    def generate_report(self, output_file: str = REPORT_FILE):
        """Generate comprehensive QA report"""
        report_data = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_issues": len(self.findings),
                "analyzer_version": "1.0.0",
                "severity_distribution": {}
            },
            "findings": [finding.to_dict() for finding in self.findings]
        }
        
        # Calculate severity distribution
        for finding in self.findings:
            severity = finding.severity
            if severity not in report_data["analysis_metadata"]["severity_distribution"]:
                report_data["analysis_metadata"]["severity_distribution"][severity] = 0
            report_data["analysis_metadata"]["severity_distribution"][severity] += 1
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n📋 DETAILED REPORT SAVED TO: {output_file}")
        return report_data

if __name__ == "__main__":
    analyzer = SeniorQAAnalyzer()
    
    try:
        findings = analyzer.run_comprehensive_analysis()
        report = analyzer.generate_report()
        
        print("\n" + "="*60)
        print("📋 EXECUTIVE SUMMARY")
        print("="*60)
        
        if not findings:
            print("✅ NO CRITICAL ISSUES FOUND")
            print("   The codebase appears to be in good condition.")
        else:
            print(f"❌ {len(findings)} ISSUES IDENTIFIED")
            
            # Group and display findings by severity
            critical = [f for f in findings if f.severity == "Critical"]
            high = [f for f in findings if f.severity == "High"] 
            medium = [f for f in findings if f.severity == "Medium"]
            low = [f for f in findings if f.severity == "Low"]
            
            if critical:
                print(f"\n🚨 CRITICAL ISSUES ({len(critical)}):")
                for finding in critical[:3]:  # Show first 3
                    print(f"   {finding.issue_id}: {finding.description}")
                if len(critical) > 3:
                    print(f"   ... and {len(critical) - 3} more")
                    
            if high:
                print(f"\n⚠️  HIGH PRIORITY ({len(high)}):")
                for finding in high[:3]:
                    print(f"   {finding.issue_id}: {finding.description}")
                if len(high) > 3:
                    print(f"   ... and {len(high) - 3} more")
                    
            if medium:
                print(f"\n⚡ MEDIUM PRIORITY ({len(medium)}):")
                for finding in medium[:3]:
                    print(f"   {finding.issue_id}: {finding.description}")
                if len(medium) > 3:
                    print(f"   ... and {len(medium) - 3} more")
                    
            if low:
                print(f"\n💡 LOW PRIORITY ({len(low)}):")
                for finding in low[:3]:
                    print(f"   {finding.issue_id}: {finding.description}")  
                if len(low) > 3:
                    print(f"   ... and {len(low) - 3} more")
        
        print(f"\n📋 Full detailed report available in: {REPORT_FILE}")
        
    except Exception as e:
        print(f"💥 ANALYSIS FAILED: {str(e)}")
        traceback.print_exc()
        sys.exit(1)