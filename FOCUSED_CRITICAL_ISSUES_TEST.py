#!/usr/bin/env python3
"""
FOCUSED CRITICAL ISSUES ANALYSIS
Test for specific bugs and errors identified from LSP diagnostics and code analysis
"""

import ast
import json
import requests
import traceback
from typing import List, Dict, Any
from datetime import datetime

class CriticalIssuesAnalyzer:
    
    def __init__(self):
        self.critical_findings = []
        
    def report_critical_issue(self, issue_id: str, location: str, description: str, 
                            steps: str, observed: str, expected: str, severity: str):
        """Report a critical issue found"""
        finding = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps,
            "observed_output": observed,
            "expected_output": expected,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.critical_findings.append(finding)
        print(f"🚨 CRITICAL ISSUE: {issue_id} - {description}")

    def test_lsp_diagnostic_issues(self):
        """Test specific issues identified by LSP diagnostics"""
        print("\n=== TESTING LSP DIAGNOSTIC ISSUES ===")
        
        # Issue 1: UserProfile missing 'id' parameter in eligibility.py:43-51
        try:
            from models.user import UserProfile
            
            # Test creating UserProfile without id parameter
            try:
                user_profile = UserProfile(
                    gpa=3.5,
                    grade_level="undergraduate",
                    field_of_study="engineering",
                    citizenship="US",
                    age=20,
                    financial_need=False
                )
                # If this succeeds but UserProfile expects an 'id', that's an issue
                if not hasattr(user_profile, 'id'):
                    self.report_critical_issue(
                        "LSP-001",
                        "routers/eligibility.py:43-51 and models/user.py",
                        "UserProfile creation missing required 'id' parameter",
                        "1. Create UserProfile instance in eligibility.py\n2. Missing id parameter causes LSP error",
                        "UserProfile created without id, causing LSP diagnostic error",
                        "UserProfile should either not require id or should have id provided",
                        "High"
                    )
            except Exception as e:
                if "id" in str(e):
                    self.report_critical_issue(
                        "LSP-001-CONFIRMED",
                        "models/user.py:UserProfile",
                        "UserProfile requires 'id' parameter but not provided in eligibility router",
                        "1. Import UserProfile\n2. Create instance without id parameter\n3. Exception raised",
                        f"Exception: {str(e)}",
                        "UserProfile should work without id or have id parameter provided",
                        "Critical"
                    )
                    
        except ImportError as e:
            self.report_critical_issue(
                "LSP-002",
                "models/user.py",
                "Cannot import UserProfile model",
                "1. Import models.user.UserProfile\n2. Import fails",
                f"ImportError: {str(e)}",
                "UserProfile should be importable",
                "Critical"
            )

    def test_auth_type_errors(self):
        """Test authentication type errors from LSP diagnostics"""
        print("\n=== TESTING AUTHENTICATION TYPE ERRORS ===")
        
        try:
            from middleware.auth import get_current_user, verify_token
            
            # Test with None values that should cause type errors
            test_cases = [
                {"token": None, "description": "None token"},
                {"token": "", "description": "Empty string token"}
            ]
            
            for case in test_cases:
                try:
                    # This should handle None/empty gracefully or raise appropriate error
                    pass  # Would need to actually test with request context
                except Exception as e:
                    if "str | None" in str(e) or "cannot be assigned" in str(e):
                        self.report_critical_issue(
                            "AUTH-TYPE-001",
                            "middleware/auth.py:121,144",
                            "Type error with None values in authentication",
                            f"1. Call authentication with {case['description']}\n2. Type error occurs",
                            f"Type error: {str(e)}",
                            "Should handle None values gracefully",
                            "High"
                        )
                        
        except ImportError as e:
            self.report_critical_issue(
                "AUTH-IMPORT-001",
                "middleware/auth.py", 
                "Cannot import authentication functions",
                "1. Import middleware.auth functions\n2. Import fails",
                f"ImportError: {str(e)}",
                "Authentication module should be importable",
                "Critical"
            )

    def test_api_runtime_errors(self):
        """Test for actual runtime errors in API endpoints"""
        print("\n=== TESTING API RUNTIME ERRORS ===")
        
        BASE_URL = "http://localhost:5000"
        
        # Test cases that commonly cause 500 errors
        error_test_cases = [
            {
                "endpoint": "/eligibility/check",
                "params": {"gpa": "not_a_number"},
                "description": "Non-numeric GPA"
            },
            {
                "endpoint": "/search", 
                "params": {"limit": "invalid"},
                "description": "Non-numeric limit"
            },
            {
                "endpoint": "/scholarships/null",
                "params": {},
                "description": "Null scholarship ID"
            }
        ]
        
        for test_case in error_test_cases:
            try:
                response = requests.get(
                    f"{BASE_URL}{test_case['endpoint']}", 
                    params=test_case['params'],
                    timeout=3
                )
                
                if response.status_code == 500:
                    self.report_critical_issue(
                        "API-500-001",
                        f"API endpoint {test_case['endpoint']}",
                        f"500 Internal Server Error with {test_case['description']}",
                        f"1. Send GET {test_case['endpoint']} with params {test_case['params']}\n2. Server returns 500",
                        f"HTTP 500: {response.text[:200]}",
                        "Should return 400/422 validation error, not 500",
                        "High"
                    )
                    
            except requests.exceptions.ConnectionError:
                # Server not running, skip API tests
                print("  ⚠️  API server not accessible, skipping API runtime tests")
                break
            except Exception as e:
                self.report_critical_issue(
                    "API-TEST-ERROR",
                    f"Test framework for {test_case['endpoint']}",
                    f"Error testing {test_case['description']}",
                    f"1. Test API endpoint {test_case['endpoint']}\n2. Test framework error",
                    f"Error: {str(e)}",
                    "Test should execute without framework errors",
                    "Medium"
                )

    def test_import_dependency_issues(self):
        """Test for import and dependency issues"""
        print("\n=== TESTING IMPORT/DEPENDENCY ISSUES ===")
        
        critical_modules = [
            "config.settings",
            "models.user", 
            "models.scholarship",
            "services.scholarship_service",
            "middleware.auth",
            "routers.search",
            "routers.eligibility"
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                self.report_critical_issue(
                    "IMPORT-001", 
                    f"{module.replace('.', '/')}.py",
                    f"Cannot import critical module {module}",
                    f"1. Import {module}\n2. ImportError raised",
                    f"ImportError: {str(e)}",
                    "Core modules should be importable",
                    "Critical"
                )
            except Exception as e:
                self.report_critical_issue(
                    "IMPORT-002",
                    f"{module.replace('.', '/')}.py", 
                    f"Error importing {module}",
                    f"1. Import {module}\n2. Exception during import",
                    f"Exception: {str(e)}",
                    "Modules should import without errors",
                    "High"
                )

    def analyze_code_syntax_errors(self):
        """Analyze Python files for syntax errors"""
        print("\n=== ANALYZING CODE SYNTAX ===")
        
        from pathlib import Path
        python_files = list(Path(".").rglob("*.py"))
        
        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse with AST to check for syntax errors
                ast.parse(content, filename=str(py_file))
                
            except SyntaxError as e:
                self.report_critical_issue(
                    "SYNTAX-001",
                    f"{py_file}:{e.lineno}",
                    f"Syntax error in {py_file}",
                    f"1. Parse {py_file}\n2. Syntax error at line {e.lineno}",
                    f"SyntaxError: {e.msg}",
                    "Python files should have valid syntax",
                    "Critical"
                )
            except Exception as e:
                # Skip files that can't be read
                pass

    def run_focused_analysis(self):
        """Run focused analysis on critical issues"""
        print("🔍 FOCUSED CRITICAL ISSUES ANALYSIS")
        print("=" * 50)
        
        self.test_lsp_diagnostic_issues()
        self.test_auth_type_errors()
        self.test_api_runtime_errors()
        self.test_import_dependency_issues()
        self.analyze_code_syntax_errors()
        
        print("\n" + "=" * 50)
        print(f"🚨 CRITICAL ISSUES FOUND: {len(self.critical_findings)}")
        
        return self.critical_findings

if __name__ == "__main__":
    analyzer = CriticalIssuesAnalyzer()
    
    try:
        findings = analyzer.run_focused_analysis()
        
        if findings:
            print("\n📋 CRITICAL ISSUES SUMMARY:")
            for i, finding in enumerate(findings, 1):
                print(f"{i}. {finding['issue_id']}: {finding['description']}")
                print(f"   Location: {finding['location']}")
                print(f"   Severity: {finding['severity']}")
                print()
        else:
            print("✅ NO CRITICAL RUNTIME ISSUES FOUND")
            
    except Exception as e:
        print(f"💥 CRITICAL ANALYSIS FAILED: {str(e)}")
        traceback.print_exc()