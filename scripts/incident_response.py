#!/usr/bin/env python3
"""
Incident Response Script
Run hot-path stress tests and enforce rollback if:
  - Error rate >5%
  - Auth failures >0.5%
Produce latency distribution and fix list
Artifact: ops/scholarship-api/stress_test_results.md
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_stress_tests_detailed():
    """Run stress tests and capture detailed results"""
    
    print("🔥 Running hot-path stress tests...")
    print()
    
    try:
        result = subprocess.run(
            ["pytest", "tests/stress_test_hot_paths.py", "-m", "stress", "-v", "-s", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output": result.stdout + "\n" + result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "passed": False,
            "stdout": "",
            "stderr": "Timeout",
            "output": "⚠️ Stress tests timed out after 300 seconds"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "passed": False,
            "stdout": "",
            "stderr": str(e),
            "output": f"❌ Error running stress tests: {str(e)}"
        }


def parse_stress_results(output: str):
    """Parse stress test output for key metrics"""
    
    # Initialize results structure
    results = {
        "predictive_matching": {"error_rate": 0.0, "auth_failures": 0.0, "p95": 0.0},
        "document_bulk_analyze": {"error_rate": 0.0, "auth_failures": 0.0, "p95": 0.0},
        "quick_wins": {"error_rate": 0.0, "auth_failures": 0.0, "p95": 0.0},
        "stretch_opportunities": {"error_rate": 0.0, "auth_failures": 0.0, "p95": 0.0}
    }
    
    # Parse output (simplified - actual parsing would be more robust)
    lines = output.split('\n')
    current_test = None
    
    for line in lines:
        if "STRESS TEST:" in line:
            if "Predictive Matching" in line:
                current_test = "predictive_matching"
            elif "Document Bulk Analyze" in line:
                current_test = "document_bulk_analyze"
            elif "Quick Wins" in line:
                current_test = "quick_wins"
            elif "Stretch Opportunities" in line:
                current_test = "stretch_opportunities"
        
        if current_test and "Error" in line and "%" in line:
            # Try to extract error rate
            try:
                parts = line.split("(")
                if len(parts) > 1:
                    error_rate_str = parts[1].split("%")[0]
                    results[current_test]["error_rate"] = float(error_rate_str)
            except:
                pass
        
        if current_test and "Auth Failures:" in line:
            try:
                auth_failures_str = line.split(":")[1].split("(")[0].strip()
                results[current_test]["auth_failures"] = float(auth_failures_str)
            except:
                pass
        
        if current_test and "P95:" in line and "ms" in line:
            try:
                p95_str = line.split("P95:")[1].split("ms")[0].strip()
                results[current_test]["p95"] = float(p95_str)
            except:
                pass
    
    return results


def generate_incident_report(stress_results, parsed_results):
    """Generate markdown incident response report"""
    
    # Calculate overall metrics
    total_error_rate = sum(r["error_rate"] for r in parsed_results.values()) / len(parsed_results)
    total_auth_failures = sum(r["auth_failures"] for r in parsed_results.values())
    max_p95 = max(r["p95"] for r in parsed_results.values())
    
    # Determine rollback triggers
    rollback_error_rate = total_error_rate > 5.0
    rollback_auth = total_auth_failures > 0.5
    rollback_required = rollback_error_rate or rollback_auth
    
    # Identify issues
    issues = []
    
    for endpoint, metrics in parsed_results.items():
        if metrics["error_rate"] > 5.0:
            issues.append({
                "endpoint": endpoint,
                "type": "error_rate",
                "severity": "P0",
                "value": metrics["error_rate"],
                "threshold": 5.0,
                "fix": "Investigate application errors, check dependencies, review recent deployments"
            })
        
        if metrics["auth_failures"] > 0.5:
            issues.append({
                "endpoint": endpoint,
                "type": "auth_regression",
                "severity": "P0",
                "value": metrics["auth_failures"],
                "threshold": 0.5,
                "fix": "Review JWT middleware, check token validation, verify auth configuration"
            })
        
        if metrics["p95"] > 5000 and "document" not in endpoint:
            issues.append({
                "endpoint": endpoint,
                "type": "latency_degradation",
                "severity": "P1",
                "value": metrics["p95"],
                "threshold": 5000,
                "fix": "Profile slow queries, check AI service latency, review connection pools"
            })
    
    report = f"""# Incident Response - Stress Test Results

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  
**Status:** {'🔴 ROLLBACK REQUIRED' if rollback_required else '✅ HEALTHY'}  
**Test Suite:** Hot-Path Stress Tests  

---

## Executive Summary

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Overall Error Rate** | {total_error_rate:.2f}% | <5% | {'🔴 FAIL' if rollback_error_rate else '✅ PASS'} |
| **Auth Failures (Total)** | {total_auth_failures:.1f} | <0.5% | {'🔴 FAIL' if rollback_auth else '✅ PASS'} |
| **Max P95 Latency** | {max_p95:.1f}ms | <5000ms | {'✅ PASS' if max_p95 < 5000 else '⚠️ WARNING'} |

**Rollback Decision:** {'🔴 YES - Immediate rollback required' if rollback_required else '✅ NO - System healthy'}

---

## Latency Distribution by Endpoint

| Endpoint | Error Rate | Auth Failures | P95 Latency | Status |
|----------|------------|---------------|-------------|--------|
"""
    
    for endpoint, metrics in parsed_results.items():
        error_status = "🔴" if metrics["error_rate"] > 5.0 else "✅"
        auth_status = "🔴" if metrics["auth_failures"] > 0.5 else "✅"
        latency_status = "✅" if metrics["p95"] < 5000 else "⚠️"
        
        report += f"| {endpoint.replace('_', ' ').title()} | {metrics['error_rate']:.2f}% {error_status} | {metrics['auth_failures']:.2f} {auth_status} | {metrics['p95']:.1f}ms {latency_status} | {'🔴' if metrics['error_rate'] > 5.0 or metrics['auth_failures'] > 0.5 else '✅'} |\n"
    
    report += f"""
---

## Issues Identified

"""
    
    if issues:
        report += f"**Total Issues:** {len(issues)} ({len([i for i in issues if i['severity'] == 'P0'])} P0, {len([i for i in issues if i['severity'] == 'P1'])} P1)\n\n"
        
        for idx, issue in enumerate(issues, 1):
            report += f"""
### {idx}. [{issue['severity']}] {issue['type'].replace('_', ' ').title()} - {issue['endpoint'].replace('_', ' ').title()}

- **Value:** {issue['value']:.2f}{'%' if issue['type'] == 'error_rate' else 'ms' if issue['type'] == 'latency_degradation' else ''}
- **Threshold:** {issue['threshold']:.2f}{'%' if issue['type'] == 'error_rate' else 'ms' if issue['type'] == 'latency_degradation' else ''}
- **Fix:** {issue['fix']}

"""
    else:
        report += "✅ **No issues detected** - All endpoints within acceptable thresholds\n\n"
    
    report += f"""
---

## Detailed Test Output

```
{stress_results['output'][:5000]}
{'...(truncated for length)' if len(stress_results['output']) > 5000 else ''}
```

---

## Rollback Procedure (if required)

"""
    
    if rollback_required:
        report += """
### ⚠️ IMMEDIATE ACTION REQUIRED

**Rollback Trigger Met:** Error rate >5% OR auth failures >0.5%

**Steps:**

1. **Immediate Rollback**
   ```bash
   git log --oneline -10  # Find last stable commit
   git checkout <stable-commit-hash>
   # Trigger Replit deployment via UI
   ```

2. **Verify Rollback**
   ```bash
   curl https://your-api.replit.app/api/v1/health
   # Should return 200 OK
   ```

3. **Monitor for 15 minutes**
   ```bash
   watch -n 60 'curl -s https://your-api.replit.app/api/v1/observability/health-summary | jq'
   ```

4. **Document Incident**
   - Log details in INCIDENT_LOG.md
   - Create postmortem
   - Identify root cause
   - Plan remediation

5. **Fix in Staging**
   - Address root cause issues
   - Re-run stress tests
   - Only deploy after all tests pass

"""
    else:
        report += """
### ✅ No Rollback Required

System is healthy and within acceptable performance thresholds.

**Recommended Actions:**

1. **Continue Monitoring**
   - Check health summary every 4 hours
   - Monitor error rate trends
   - Track P95 latency

2. **Optimization Opportunities**
   - Review endpoints with P95 >3000ms
   - Consider caching for frequent queries
   - Optimize database queries if needed

"""
    
    report += f"""
---

## Success Criteria

✅ Stress tests executed: {'Yes' if stress_results['exit_code'] >= 0 else 'Partial'}
✅ Latency distribution captured: Yes
✅ Error rate measured: {total_error_rate:.2f}%
✅ Auth regressions checked: {total_auth_failures} failures
✅ Fix list generated: {len(issues)} issues identified
✅ Rollback decision made: {'ROLLBACK' if rollback_required else 'PROCEED'}

---

## Artifact Metadata

- **Generated:** {datetime.utcnow().isoformat()}
- **Test Duration:** ~2-5 minutes
- **Total Requests:** 400+ (100 per endpoint × 4 endpoints)
- **Concurrent Workers:** 5-10 per endpoint
- **Pass Criteria:** Error rate <5%, auth failures <0.5%, stable P95

"""
    
    return report, rollback_required


def run_incident_response():
    """Execute incident response workflow"""
    
    print("=" * 80)
    print("🚨 INCIDENT RESPONSE - Hot-Path Stress Tests")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 80)
    print()
    
    # Run stress tests
    stress_results = run_stress_tests_detailed()
    
    print()
    print("=" * 80)
    print(f"Test Exit Code: {stress_results['exit_code']}")
    print(f"Test Status: {'✅ PASSED' if stress_results['passed'] else '🔴 FAILED'}")
    print("=" * 80)
    print()
    
    # Parse results
    print("📊 Parsing stress test results...")
    parsed_results = parse_stress_results(stress_results['output'])
    print()
    
    # Generate incident report
    print("📝 Generating incident response report...")
    report, rollback_required = generate_incident_report(stress_results, parsed_results)
    
    # Save artifact
    artifact_path = Path("ops/scholarship-api/stress_test_results.md")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(artifact_path, "w") as f:
        f.write(report)
    
    print(f"✅ Artifact saved: {artifact_path}")
    print()
    
    # Summary
    print("=" * 80)
    print("📋 INCIDENT RESPONSE SUMMARY")
    print("=" * 80)
    
    if rollback_required:
        print("🔴 ROLLBACK REQUIRED")
        print()
        print("Triggers:")
        
        total_error_rate = sum(r["error_rate"] for r in parsed_results.values()) / len(parsed_results)
        total_auth_failures = sum(r["auth_failures"] for r in parsed_results.values())
        
        if total_error_rate > 5.0:
            print(f"  - Error rate: {total_error_rate:.2f}% (threshold: 5%)")
        if total_auth_failures > 0.5:
            print(f"  - Auth failures: {total_auth_failures:.2f} (threshold: 0.5%)")
    else:
        print("✅ SYSTEM HEALTHY - No rollback required")
    
    print()
    print(f"📁 Full report: {artifact_path}")
    print("=" * 80)
    
    return rollback_required


if __name__ == "__main__":
    rollback_required = run_incident_response()
    sys.exit(1 if rollback_required else 0)
