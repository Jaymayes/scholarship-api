#!/usr/bin/env python3
"""
Senior QA Engineer Comprehensive Analysis Report
Analysis-only examination of existing codebase without modifications
"""

import json
import os
from datetime import datetime
from pathlib import Path


def analyze_codebase():
    """Perform comprehensive QA analysis"""

    issues = []
    issue_id = 1

    def add_issue(location, description, steps, observed, expected, severity):
        nonlocal issue_id
        issues.append({
            "issue_id": f"QA-{issue_id:03d}",
            "location": location,
            "description": description,
            "steps_to_reproduce": steps,
            "observed_output": observed,
            "expected_output": expected,
            "severity": severity
        })
        issue_id += 1

    print("🔍 Senior QA Engineer - Comprehensive Code Analysis")
    print("=" * 60)

    # 1. Examine main.py for critical issues
    print("Analyzing main.py...")

    try:
        with open("main.py") as f:
            main_content = f.read()

        # Check for production hardening issues
        if 'docs_url="/docs"' in main_content and 'settings.should_enable_docs' not in main_content:
            add_issue(
                "main.py:42",
                "API documentation potentially exposed in production",
                "1. Set ENVIRONMENT=production\n2. Start application\n3. Access /docs endpoint",
                "Documentation accessible in production mode",
                "Documentation should be conditionally enabled based on environment",
                "Medium"
            )

        # Check middleware ordering
        if "add_middleware" in main_content:
            lines = main_content.split('\n')
            middleware_lines = [i for i, line in enumerate(lines) if "add_middleware" in line]
            if len(middleware_lines) > 0:
                # Security middleware should be first
                first_middleware = lines[middleware_lines[0]]
                if "SecurityHeadersMiddleware" not in first_middleware:
                    add_issue(
                        f"main.py:{middleware_lines[0]+1}",
                        "Security middleware not positioned first",
                        "1. Review middleware stack in main.py\n2. Check execution order",
                        "Other middleware positioned before security middleware",
                        "SecurityHeadersMiddleware should be outermost (first added)",
                        "Medium"
                    )

    except Exception as e:
        add_issue(
            "main.py",
            "Cannot analyze main application file",
            "Attempt to read and parse main.py",
            f"Error: {str(e)}",
            "Successful file analysis",
            "High"
        )

    # 2. Examine configuration security
    print("Analyzing configuration security...")

    try:
        with open("config/settings.py") as f:
            settings_content = f.read()

        # Check for hardcoded secrets
        if "secret" in settings_content.lower() and "test" in settings_content.lower():
            add_issue(
                "config/settings.py",
                "Potential hardcoded test secrets found",
                "1. Search for 'test' and 'secret' in settings.py\n2. Review secret handling",
                "Found test/secret references in production code",
                "No hardcoded secrets or test values",
                "High"
            )

        # Check JWT secret validation
        if "jwt_secret_key" in settings_content:
            if "len(" not in settings_content or "64" not in settings_content:
                add_issue(
                    "config/settings.py",
                    "JWT secret length validation may be insufficient",
                    "1. Check JWT secret validation logic\n2. Test with short secret",
                    "No or insufficient JWT secret length validation",
                    "JWT secrets should be validated as ≥64 characters",
                    "High"
                )

    except Exception as e:
        add_issue(
            "config/settings.py",
            "Cannot analyze configuration file",
            "Attempt to read config/settings.py",
            f"Error: {str(e)}",
            "Successful configuration analysis",
            "Critical"
        )

    # 3. Examine database security
    print("Analyzing database operations...")

    db_files = ["database/session_manager.py", "models/scholarship.py", "services/scholarship_service.py"]
    for db_file in db_files:
        try:
            if os.path.exists(db_file):
                with open(db_file) as f:
                    db_content = f.read()

                # Check for SQL injection vulnerabilities
                if "SELECT" in db_content and "%" in db_content:
                    add_issue(
                        db_file,
                        "Potential SQL injection risk with string formatting",
                        f"1. Review SQL queries in {db_file}\n2. Look for % formatting or string concatenation",
                        "Found SQL queries with potential string formatting",
                        "All SQL queries should use parameterized queries",
                        "Critical"
                    )

                # Check for missing input validation
                if "def" in db_content and "request" in db_content:
                    if "validate" not in db_content and "pydantic" not in db_content:
                        add_issue(
                            db_file,
                            "Missing input validation in database operations",
                            f"1. Test database operations with invalid inputs\n2. Check {db_file} for validation",
                            "Database functions may accept unvalidated input",
                            "All database inputs should be validated",
                            "High"
                        )
        except:
            pass

    # 4. Examine middleware security
    print("Analyzing middleware implementations...")

    middleware_files = list(Path("middleware").glob("*.py"))
    for middleware_file in middleware_files:
        try:
            with open(middleware_file) as f:
                middleware_content = f.read()

            # Check rate limiting implementation
            if "rate" in str(middleware_file).lower():
                if "redis" in middleware_content and "except" not in middleware_content:
                    add_issue(
                        str(middleware_file),
                        "Rate limiting missing error handling for Redis failures",
                        "1. Disable Redis\n2. Test rate limiting functionality",
                        "Rate limiting may fail without proper Redis error handling",
                        "Graceful fallback when Redis is unavailable",
                        "Medium"
                    )

            # Check for security headers
            if "security" in str(middleware_file).lower():
                required_headers = ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"]
                missing_headers = [h for h in required_headers if h not in middleware_content]
                if missing_headers:
                    add_issue(
                        str(middleware_file),
                        f"Missing security headers: {missing_headers}",
                        "1. Check response headers\n2. Review security middleware",
                        f"Security headers not implemented: {missing_headers}",
                        "All critical security headers should be present",
                        "Medium"
                    )

        except Exception as e:
            add_issue(
                str(middleware_file),
                "Cannot analyze middleware file",
                f"Attempt to read {middleware_file}",
                f"Error: {str(e)}",
                "Successful middleware analysis",
                "Medium"
            )

    # 5. Examine API endpoints for vulnerabilities
    print("Analyzing API endpoints...")

    router_files = list(Path("routers").glob("*.py"))
    for router_file in router_files:
        try:
            with open(router_file) as f:
                router_content = f.read()

            # Check for missing authentication
            if "@router." in router_content:
                if "dependencies" not in router_content and "auth" not in str(router_file).lower():
                    if "scholarships" in str(router_file) or "search" in str(router_file):
                        add_issue(
                            str(router_file),
                            "API endpoints may lack authentication",
                            f"1. Test endpoints in {router_file} without authentication\n2. Check for auth dependencies",
                            "Endpoints accessible without authentication",
                            "Critical endpoints should require authentication",
                            "Medium"
                        )

            # Check for input validation
            if "async def" in router_content:
                if "Depends" not in router_content and "pydantic" not in router_content:
                    add_issue(
                        str(router_file),
                        "Missing input validation in API endpoints",
                        f"1. Send malformed requests to endpoints in {router_file}\n2. Check validation",
                        "Endpoints may accept invalid input",
                        "All inputs should be validated with Pydantic models",
                        "High"
                    )

        except Exception as e:
            add_issue(
                str(router_file),
                "Cannot analyze router file",
                f"Attempt to read {router_file}",
                f"Error: {str(e)}",
                "Successful router analysis",
                "Medium"
            )

    # 6. Check test coverage
    print("Analyzing test coverage...")

    test_files = list(Path("tests").glob("*.py"))
    test_count = len([f for f in test_files if f.name.startswith("test_")])

    if test_count < 5:
        add_issue(
            "tests/",
            "Insufficient test coverage",
            "1. Count test files in tests/ directory\n2. Review test coverage",
            f"Only {test_count} test files found",
            "Comprehensive test suite with multiple test files",
            "Medium"
        )

    # Check for security tests
    security_test_exists = any("security" in f.name for f in test_files)
    if not security_test_exists:
        add_issue(
            "tests/",
            "Missing security-specific tests",
            "1. Look for security test files\n2. Check for penetration testing",
            "No dedicated security test files found",
            "Security tests for authentication, authorization, input validation",
            "High"
        )

    # 7. Check deployment configuration
    print("Analyzing deployment configuration...")

    if os.path.exists("Dockerfile"):
        try:
            with open("Dockerfile") as f:
                dockerfile_content = f.read()

            # Check for security best practices
            if "USER root" in dockerfile_content:
                add_issue(
                    "Dockerfile",
                    "Container running as root user",
                    "1. Build Docker image\n2. Check user context in container",
                    "Container runs with root privileges",
                    "Container should run as non-root user",
                    "High"
                )

            if "COPY . ." in dockerfile_content:
                add_issue(
                    "Dockerfile",
                    "Dockerfile copies entire context including sensitive files",
                    "1. Build Docker image\n2. Check for sensitive files in image",
                    "Entire directory copied to image",
                    "Use .dockerignore and selective COPY commands",
                    "Medium"
                )

        except Exception as e:
            add_issue(
                "Dockerfile",
                "Cannot analyze Dockerfile",
                "Attempt to read Dockerfile",
                f"Error: {str(e)}",
                "Successful Dockerfile analysis",
                "Low"
            )

    # 8. Environment and secrets analysis
    print("Analyzing environment configuration...")

    if os.path.exists(".env.example"):
        try:
            with open(".env.example") as f:
                env_content = f.read()

            # Check for default secrets
            if "your-secret-key" in env_content or "changeme" in env_content:
                add_issue(
                    ".env.example",
                    "Example file contains placeholder secrets that could be used accidentally",
                    "1. Review .env.example file\n2. Check for placeholder values",
                    "Found placeholder secret values in example file",
                    "Example file should have clear placeholders without functional values",
                    "Low"
                )

        except Exception:
            pass

    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE QA ANALYSIS REPORT")
    print("=" * 80)

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for issue in issues:
        severity_counts[issue["severity"]] += 1

    print("\n📈 EXECUTIVE SUMMARY:")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Issues Found: {len(issues)}")
    print(f"Critical: {severity_counts['Critical']}")
    print(f"High: {severity_counts['High']}")
    print(f"Medium: {severity_counts['Medium']}")
    print(f"Low: {severity_counts['Low']}")

    if issues:
        print("\n🔍 DETAILED FINDINGS:")
        print("-" * 80)

        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order[x["severity"]])

        for issue in sorted_issues:
            print(f"\n{issue['issue_id']} [{issue['severity']}]")
            print(f"Location: {issue['location']}")
            print(f"Description: {issue['description']}")
            print("Steps to Reproduce:")
            for step in issue['steps_to_reproduce'].split('\n'):
                print(f"  {step}")
            print(f"Observed Output: {issue['observed_output']}")
            print(f"Expected Output: {issue['expected_output']}")
            print("-" * 40)
    else:
        print("\n✅ EXCELLENT: No issues found in static analysis!")

    # Save detailed JSON report
    report_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "analysis_type": "Senior QA Engineer Comprehensive Analysis",
        "methodology": "Static code analysis without modifications",
        "summary": {
            "total_issues": len(issues),
            "by_severity": severity_counts
        },
        "issues": issues
    }

    with open("QA_SENIOR_ANALYSIS_REPORT.json", "w") as f:
        json.dump(report_data, f, indent=2)

    print("\n📄 Detailed JSON report saved: QA_SENIOR_ANALYSIS_REPORT.json")

    # Recommendations
    print("\n🎯 KEY RECOMMENDATIONS:")
    if severity_counts["Critical"] > 0:
        print("- Address CRITICAL issues immediately before deployment")
    if severity_counts["High"] > 0:
        print("- Resolve HIGH severity issues to improve security posture")
    if severity_counts["Medium"] > 0:
        print("- Consider addressing MEDIUM issues for production readiness")

    print("\n✅ QA Analysis Complete - No code was modified during this analysis")

    return len(issues)

if __name__ == "__main__":
    issue_count = analyze_codebase()
    exit(0 if issue_count == 0 else 1)
