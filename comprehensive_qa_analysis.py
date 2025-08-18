#!/usr/bin/env python3
"""
Comprehensive QA Analysis Script
Senior QA Engineer Analysis - Identify all bugs, errors, and vulnerabilities
DO NOT MODIFY EXISTING CODE - ANALYSIS ONLY
"""

import os
import sys
import json
import traceback
import subprocess
import importlib
import ast
from typing import List, Dict, Any
from datetime import datetime

class QAAnalyzer:
    def __init__(self):
        self.findings = []
        self.test_results = []
        self.severity_levels = ["Low", "Medium", "High", "Critical"]
        
    def add_finding(self, issue_id: str, location: str, description: str, 
                   reproduction_steps: str, observed_output: str, 
                   expected_output: str, severity: str):
        """Add a finding to the report"""
        finding = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": reproduction_steps,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.findings.append(finding)
        
    def analyze_syntax_errors(self):
        """Check for syntax errors across all Python files"""
        print("Analyzing syntax errors...")
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                self.add_finding(
                    f"SYNTAX-{len(self.findings):03d}",
                    f"{file_path}:{e.lineno}",
                    f"Syntax error: {e.msg}",
                    f"1. Open file {file_path}\n2. Go to line {e.lineno}",
                    f"SyntaxError: {e.msg}",
                    "Valid Python syntax",
                    "Critical"
                )
            except Exception as e:
                self.add_finding(
                    f"PARSE-{len(self.findings):03d}",
                    file_path,
                    f"File parsing error: {str(e)}",
                    f"1. Open file {file_path}\n2. Try to parse",
                    f"Exception: {str(e)}",
                    "Successful file parsing",
                    "High"
                )
    
    def analyze_import_errors(self):
        """Check for import errors and missing dependencies"""
        print("Analyzing import errors...")
        
        # Test core module imports
        critical_modules = [
            'main', 'config.settings', 'routers.scholarships', 
            'services.scholarship_service', 'models.scholarship'
        ]
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                self.add_finding(
                    f"IMPORT-{len(self.findings):03d}",
                    f"{module_name}.py",
                    f"Import error in critical module: {str(e)}",
                    f"1. python -c 'import {module_name}'",
                    f"ImportError: {str(e)}",
                    "Successful module import",
                    "Critical"
                )
            except Exception as e:
                self.add_finding(
                    f"MODULE-{len(self.findings):03d}",
                    f"{module_name}.py",
                    f"Module loading error: {str(e)}",
                    f"1. python -c 'import {module_name}'",
                    f"Exception: {str(e)}",
                    "Successful module loading",
                    "High"
                )
    
    def analyze_database_vulnerabilities(self):
        """Check for SQL injection and database security issues"""
        print("Analyzing database vulnerabilities...")
        
        # Check for potential SQL injection patterns
        sql_patterns = [
            r".*\+.*sql.*",
            r".*%.*sql.*",
            r".*format.*sql.*",
            r".*f\".*sql.*",
            r".*execute\(.*\+.*\)",
        ]
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    if 'sql' in line.lower() or 'query' in line.lower():
                        if any(pattern in line.lower() for pattern in ['format', '+', '%', 'f"']):
                            if 'execute' in line.lower() or 'query' in line.lower():
                                self.add_finding(
                                    f"SQL-{len(self.findings):03d}",
                                    f"{file_path}:{line_num}",
                                    "Potential SQL injection vulnerability",
                                    f"1. Review line {line_num} in {file_path}\n2. Check for string concatenation in SQL",
                                    f"Line contains: {line.strip()}",
                                    "Parameterized queries using SQLAlchemy or prepared statements",
                                    "High"
                                )
            except Exception as e:
                pass
    
    def analyze_authentication_issues(self):
        """Check for authentication and authorization vulnerabilities"""
        print("Analyzing authentication issues...")
        
        # Check for hardcoded secrets
        secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in secret_patterns:
                        if pattern in line.lower() and '=' in line and '"' in line:
                            # Skip comments and obvious examples
                            if not line.strip().startswith('#') and 'example' not in line.lower():
                                if 'your-' not in line.lower() and 'change-' not in line.lower():
                                    self.add_finding(
                                        f"AUTH-{len(self.findings):03d}",
                                        f"{file_path}:{line_num}",
                                        f"Potential hardcoded {pattern} found",
                                        f"1. Review line {line_num} in {file_path}\n2. Check if secret is hardcoded",
                                        f"Line contains: {line.strip()}",
                                        "Secrets should be loaded from environment variables",
                                        "Medium"
                                    )
            except Exception as e:
                pass
    
    def analyze_error_handling(self):
        """Check for proper error handling"""
        print("Analyzing error handling...")
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                
                # Check for bare except clauses
                for line_num, line in enumerate(lines, 1):
                    if 'except:' in line and line.strip().endswith(':'):
                        self.add_finding(
                            f"EXCEPT-{len(self.findings):03d}",
                            f"{file_path}:{line_num}",
                            "Bare except clause found",
                            f"1. Review line {line_num} in {file_path}\n2. Check exception handling",
                            f"Line contains: {line.strip()}",
                            "Specific exception types should be caught",
                            "Medium"
                        )
                
                # Check for missing try-except around risky operations
                risky_operations = ['requests.', 'json.', 'open(', 'int(', 'float(']
                in_try_block = False
                
                for line_num, line in enumerate(lines, 1):
                    if 'try:' in line:
                        in_try_block = True
                    elif 'except' in line or line.strip() == '' or not line.startswith('    '):
                        in_try_block = False
                    
                    for op in risky_operations:
                        if op in line and not in_try_block and not line.strip().startswith('#'):
                            self.add_finding(
                                f"NOEXCEPT-{len(self.findings):03d}",
                                f"{file_path}:{line_num}",
                                f"Risky operation without exception handling: {op}",
                                f"1. Review line {line_num} in {file_path}\n2. Add try-except block",
                                f"Line contains: {line.strip()}",
                                "Risky operations should be wrapped in try-except blocks",
                                "Low"
                            )
            except Exception as e:
                pass
    
    def test_api_endpoints(self):
        """Test API endpoints for errors"""
        print("Testing API endpoints...")
        
        try:
            import requests
            
            base_url = "http://localhost:5000"
            
            # Test critical endpoints
            endpoints = [
                "/health",
                "/api/v1/scholarships",
                "/api/v1/search",
                "/docs",
                "/nonexistent"  # Should return 404
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    
                    if endpoint == "/nonexistent":
                        if response.status_code != 404:
                            self.add_finding(
                                f"API-{len(self.findings):03d}",
                                f"GET {endpoint}",
                                "Non-existent endpoint should return 404",
                                f"1. curl {base_url}{endpoint}",
                                f"Status code: {response.status_code}",
                                "Status code: 404",
                                "Medium"
                            )
                    elif response.status_code >= 500:
                        self.add_finding(
                            f"API-{len(self.findings):03d}",
                            f"GET {endpoint}",
                            f"Server error on endpoint: {response.status_code}",
                            f"1. curl {base_url}{endpoint}",
                            f"Status: {response.status_code}, Body: {response.text[:200]}",
                            "Status code < 500",
                            "High"
                        )
                        
                except requests.exceptions.RequestException as e:
                    self.add_finding(
                        f"CONN-{len(self.findings):03d}",
                        f"GET {endpoint}",
                        f"Connection error: {str(e)}",
                        f"1. curl {base_url}{endpoint}",
                        f"Exception: {str(e)}",
                        "Successful HTTP response",
                        "High"
                    )
                        
        except ImportError:
            self.add_finding(
                f"DEP-{len(self.findings):03d}",
                "requirements",
                "Missing requests library for API testing",
                "1. pip install requests",
                "ImportError: No module named 'requests'",
                "Successful import of requests library",
                "Medium"
            )
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("Testing edge cases...")
        
        try:
            # Test with various input types
            from services.scholarship_service import ScholarshipService
            
            service = ScholarshipService()
            
            # Test edge cases
            edge_cases = [
                (None, "None input"),
                ("", "Empty string"),
                ("x" * 10000, "Very long string"),
                (-1, "Negative number"),
                (0, "Zero"),
                (float('inf'), "Infinity"),
                ([], "Empty list"),
                ({}, "Empty dict")
            ]
            
            for test_input, description in edge_cases:
                try:
                    # Test search functionality
                    result = service.search_scholarships(test_input)
                    # If this doesn't raise an exception, check if result is reasonable
                    if result is None:
                        self.add_finding(
                            f"EDGE-{len(self.findings):03d}",
                            "services/scholarship_service.py:search_scholarships",
                            f"Search returns None for {description}",
                            f"1. Call search_scholarships({repr(test_input)})",
                            "None",
                            "Empty list or appropriate error",
                            "Low"
                        )
                except Exception as e:
                    # Some exceptions are expected, but check for unhandled ones
                    if "TypeError" in str(e) or "AttributeError" in str(e):
                        self.add_finding(
                            f"TYPE-{len(self.findings):03d}",
                            "services/scholarship_service.py:search_scholarships",
                            f"Unhandled exception for {description}: {str(e)}",
                            f"1. Call search_scholarships({repr(test_input)})",
                            f"Exception: {str(e)}",
                            "Graceful error handling or validation",
                            "Medium"
                        )
                        
        except Exception as e:
            self.add_finding(
                f"SERVICE-{len(self.findings):03d}",
                "services/scholarship_service.py",
                f"Unable to load ScholarshipService: {str(e)}",
                "1. from services.scholarship_service import ScholarshipService",
                f"Exception: {str(e)}",
                "Successful service instantiation",
                "High"
            )
    
    def analyze_configuration_issues(self):
        """Check for configuration and environment issues"""
        print("Analyzing configuration issues...")
        
        try:
            from config.settings import settings
            
            # Check for missing required environment variables
            required_env_vars = [
                'DATABASE_URL',
                'JWT_SECRET_KEY',
                'REDIS_URL'
            ]
            
            for var in required_env_vars:
                if not os.environ.get(var):
                    self.add_finding(
                        f"CONFIG-{len(self.findings):03d}",
                        "Environment Variables",
                        f"Missing required environment variable: {var}",
                        f"1. echo ${var}\n2. Check if variable is set",
                        "Variable not set or empty",
                        f"{var} should be properly configured",
                        "High"
                    )
            
            # Check for default/insecure values
            if hasattr(settings, 'jwt_secret_key'):
                if 'your-secret-key' in settings.jwt_secret_key.lower():
                    self.add_finding(
                        f"SECURITY-{len(self.findings):03d}",
                        "config/settings.py:jwt_secret_key",
                        "Default JWT secret key detected",
                        "1. Check settings.jwt_secret_key value",
                        f"Value contains default text: {settings.jwt_secret_key[:20]}...",
                        "Unique, secure random key",
                        "Critical"
                    )
                        
        except Exception as e:
            self.add_finding(
                f"SETTINGS-{len(self.findings):03d}",
                "config/settings.py",
                f"Unable to load settings: {str(e)}",
                "1. from config.settings import settings",
                f"Exception: {str(e)}",
                "Successful settings loading",
                "Critical"
            )
    
    def run_pytest_analysis(self):
        """Run existing tests and analyze failures"""
        print("Running pytest analysis...")
        
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--tb=short', '-v'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                # Parse pytest output for specific failures
                lines = result.stdout.split('\n') + result.stderr.split('\n')
                current_test = ""
                
                for line in lines:
                    if '::' in line and 'FAILED' in line:
                        current_test = line
                    elif 'FAILED' in line and current_test:
                        self.add_finding(
                            f"TEST-{len(self.findings):03d}",
                            current_test.split()[0] if current_test else "Unknown test",
                            f"Test failure: {line.strip()}",
                            f"1. pytest {current_test.split()[0] if current_test else ''}\n2. Review test output",
                            line.strip(),
                            "Test should pass",
                            "Medium"
                        )
                        current_test = ""
                        
        except subprocess.TimeoutExpired:
            self.add_finding(
                f"TIMEOUT-{len(self.findings):03d}",
                "pytest execution",
                "Test suite timed out after 120 seconds",
                "1. python -m pytest\n2. Wait for completion",
                "Timeout after 120 seconds",
                "Tests complete within reasonable time",
                "Medium"
            )
        except Exception as e:
            self.add_finding(
                f"PYTEST-{len(self.findings):03d}",
                "pytest execution",
                f"Unable to run pytest: {str(e)}",
                "1. python -m pytest",
                f"Exception: {str(e)}",
                "Successful test execution",
                "Medium"
            )
    
    def generate_report(self):
        """Generate the final QA report"""
        print(f"\nGenerating QA Analysis Report...")
        print(f"Total findings: {len(self.findings)}")
        
        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        self.findings.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        # Generate summary
        severity_counts = {}
        for finding in self.findings:
            severity = finding["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        report = {
            "qa_analysis_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_findings": len(self.findings),
                "severity_breakdown": severity_counts,
                "analysis_scope": [
                    "Syntax errors",
                    "Import errors",
                    "Database vulnerabilities",
                    "Authentication issues",
                    "Error handling",
                    "API endpoints",
                    "Edge cases",
                    "Configuration issues",
                    "Test failures"
                ]
            },
            "findings": self.findings
        }
        
        # Save detailed report
        with open("COMPREHENSIVE_QA_FINDINGS.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        markdown_report = self.generate_markdown_report(report)
        with open("COMPREHENSIVE_QA_FINDINGS.md", "w") as f:
            f.write(markdown_report)
        
        print(f"Report saved to COMPREHENSIVE_QA_FINDINGS.json and COMPREHENSIVE_QA_FINDINGS.md")
        return report
    
    def generate_markdown_report(self, report):
        """Generate markdown version of the report"""
        md = f"""# Comprehensive QA Analysis Report

## Executive Summary

**Analysis Date:** {report['qa_analysis_summary']['timestamp']}  
**Total Findings:** {report['qa_analysis_summary']['total_findings']}

### Severity Breakdown
"""
        
        for severity, count in report['qa_analysis_summary']['severity_breakdown'].items():
            md += f"- **{severity}:** {count} issues\n"
        
        md += "\n## Detailed Findings\n\n"
        
        for finding in report['findings']:
            md += f"""### {finding['issue_id']} - {finding['severity']} Severity

**Location:** `{finding['location']}`  
**Description:** {finding['description']}

**Steps to Reproduce:**
```
{finding['steps_to_reproduce']}
```

**Observed Output:**
```
{finding['observed_output']}
```

**Expected Output:**
```
{finding['expected_output']}
```

---

"""
        
        return md
    
    def run_full_analysis(self):
        """Run the complete QA analysis"""
        print("=" * 60)
        print("COMPREHENSIVE QA ANALYSIS - SENIOR QA ENGINEER")
        print("=" * 60)
        print("OBJECTIVE: Identify all errors, bugs, and vulnerabilities")
        print("SCOPE: Complete codebase analysis")
        print("=" * 60)
        
        try:
            self.analyze_syntax_errors()
            self.analyze_import_errors()
            self.analyze_database_vulnerabilities()
            self.analyze_authentication_issues()
            self.analyze_error_handling()
            self.test_api_endpoints()
            self.test_edge_cases()
            self.analyze_configuration_issues()
            self.run_pytest_analysis()
            
            return self.generate_report()
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            traceback.print_exc()
            return None

if __name__ == "__main__":
    analyzer = QAAnalyzer()
    report = analyzer.run_full_analysis()
    
    if report:
        print("\n" + "=" * 60)
        print("QA ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Total findings: {report['qa_analysis_summary']['total_findings']}")
        for severity, count in report['qa_analysis_summary']['severity_breakdown'].items():
            print(f"{severity}: {count}")
        print("=" * 60)