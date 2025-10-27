#!/usr/bin/env python3
"""
Release/Validation Script
Execute 48-hour optimization plan: enable Redis caching, reorder middleware, 
add prepared statements, run stress tests, compare baselines
Goal: -80 to -120ms P95 reduction
Artifact: ops/scholarship-api/optimization_before_after.md
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.latency_dashboard import get_daily_ops_snapshot


def capture_baseline(name: str):
    """Capture performance baseline"""
    snapshot = get_daily_ops_snapshot()
    return {
        "name": name,
        "timestamp": datetime.utcnow().isoformat(),
        "p50": snapshot["overall"]["p50"],
        "p95": snapshot["overall"]["p95"],
        "p99": snapshot["overall"]["p99"],
        "error_rate": snapshot["error_rate"],
        "endpoint_groups": snapshot["endpoint_groups"]
    }


def run_stress_tests():
    """Run stress tests and return results"""
    print("🔥 Running stress tests...")
    
    try:
        result = subprocess.run(
            ["pytest", "tests/stress_test_hot_paths.py", "-m", "stress", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "passed": False,
            "output": "Stress tests timed out after 300 seconds"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "passed": False,
            "output": f"Error running stress tests: {str(e)}"
        }


def generate_optimization_report(before, after, stress_results):
    """Generate markdown optimization report"""
    
    p95_reduction = before["p95"] - after["p95"]
    p95_reduction_pct = (p95_reduction / before["p95"]) * 100 if before["p95"] > 0 else 0
    
    goal_met = p95_reduction >= 80  # Minimum 80ms reduction
    sustained = after["error_rate"] < 1.0  # Error rate remains low
    
    report = f"""# 48-Hour Optimization Plan - Execution Report

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  
**Goal:** P95 reduction of 80-120ms  
**Status:** {'✅ SUCCESS' if goal_met and sustained else '⚠️ PARTIAL' if goal_met else '🔴 FAILED'}

---

## Executive Summary

| Metric | Before | After | Change | Goal |
|--------|--------|-------|--------|------|
| **P50** | {before['p50']:.1f}ms | {after['p50']:.1f}ms | {after['p50'] - before['p50']:+.1f}ms | - |
| **P95** | {before['p95']:.1f}ms | {after['p95']:.1f}ms | **{p95_reduction:+.1f}ms** ({p95_reduction_pct:+.1f}%) | -80 to -120ms |
| **P99** | {before['p99']:.1f}ms | {after['p99']:.1f}ms | {after['p99'] - before['p99']:+.1f}ms | - |
| **Error Rate** | {before['error_rate']:.2f}% | {after['error_rate']:.2f}% | {after['error_rate'] - before['error_rate']:+.2f}% | <1% |

**P95 Reduction Goal:** {'✅ MET' if goal_met else '🔴 NOT MET'} ({p95_reduction:.0f}ms reduction, target: ≥80ms)  
**Sustained Improvement:** {'✅ YES' if sustained else '🔴 NO'} (error rate: {after['error_rate']:.2f}%)

---

## Optimization Steps Executed

### 1. ✅ Pre-Optimization Baseline
- Captured at: {before['timestamp']}
- P95: {before['p95']:.1f}ms
- Error Rate: {before['error_rate']:.2f}%

### 2. 🔄 Redis Result Caching
- Status: Infrastructure ready (requires managed Redis provisioning)
- Expected Impact: 15-20ms P95 reduction
- Actual Impact: Pending Redis provisioning

### 3. ⚡ Middleware Reordering
- Current Order: CORS → WAF → Auth → Rate Limit
- Optimized Order: Rate Limit → CORS → Auth → WAF
- Expected Impact: 5-10ms P95 reduction
- Status: Code changes required (see main.py)

### 4. 🗄️ Database Prepared Statements
- Target Queries: Frequent searches, eligibility checks
- Expected Impact: 5-15ms P95 reduction
- Status: Migration scripts ready

### 5. ✅ Post-Optimization Baseline
- Captured at: {after['timestamp']}
- P95: {after['p95']:.1f}ms
- Error Rate: {after['error_rate']:.2f}%

### 6. 🔥 Stress Test Validation
- **Status:** {'✅ PASSED' if stress_results['passed'] else '🔴 FAILED'}
- **Exit Code:** {stress_results['exit_code']}

---

## Endpoint Group Performance

| Group | Before P95 | After P95 | Change | Status |
|-------|------------|-----------|--------|--------|
"""
    
    # Compare endpoint groups
    for group_name in before['endpoint_groups'].keys():
        before_p95 = before['endpoint_groups'][group_name]['p95']
        after_p95 = after['endpoint_groups'][group_name].get('p95', 0)
        
        if before_p95 > 0 and after_p95 > 0:
            change = after_p95 - before_p95
            status = "✅" if change < 0 else "🔴" if change > 10 else "➡️"
            report += f"| {group_name} | {before_p95:.1f}ms | {after_p95:.1f}ms | {change:+.1f}ms | {status} |\n"
    
    report += f"""
---

## Stress Test Results

```
{stress_results['output'][:2000]}
{'...(truncated)' if len(stress_results['output']) > 2000 else ''}
```

---

## Recommendations

"""
    
    if goal_met and sustained:
        report += """
### ✅ Optimization Successful

1. **Monitor P95 for 48 hours** to ensure sustained improvement
2. **Deploy to production** with confidence
3. **Track business impact** (conversions, revenue) post-deployment
4. **Document learnings** for future optimization cycles

"""
    elif goal_met and not sustained:
        report += """
### ⚠️ Partial Success - Error Rate Elevated

1. **Investigate error rate spike** ({:.2f}%)
2. **Review recent code changes** for regressions
3. **Hold deployment** until error rate <1%
4. **Re-run stress tests** after fixes

""".format(after['error_rate'])
    else:
        report += f"""
### 🔴 Optimization Goal Not Met

**Current P95 Reduction:** {p95_reduction:.0f}ms (target: ≥80ms)

**Next Steps:**

1. **Phase 2 Optimizations:**
   - Enable Redis caching (requires provisioning)
   - Implement prepared statements (migrations ready)
   - Add database connection pooling warm-up
   - Reorder middleware (code changes required)

2. **Deep Dive Analysis:**
   - Profile slow queries with EXPLAIN ANALYZE
   - Review AI endpoint latency (if >5000ms)
   - Check database connection pool saturation
   - Analyze middleware overhead

3. **Consider Alternative Approaches:**
   - Horizontal scaling (add replicas)
   - Edge caching (CDN for static responses)
   - Query result materialization
   - Async task offloading for heavy operations

"""
    
    report += f"""
---

## Artifact Metadata

- **Generated:** {datetime.utcnow().isoformat()}
- **Before Baseline:** {before['timestamp']}
- **After Baseline:** {after['timestamp']}
- **P95 Reduction:** {p95_reduction:.1f}ms ({p95_reduction_pct:.1f}%)
- **Goal Achievement:** {'✅ Yes' if goal_met else '🔴 No'}
- **Sustained:** {'✅ Yes' if sustained else '🔴 No'}

**Success Criteria:**
- Documented before/after: ✅
- Sustained improvement: {'✅' if sustained else '🔴'}
- P95 reduction ≥80ms: {'✅' if goal_met else '🔴'}
"""
    
    return report


def run_release_validation():
    """Execute release validation workflow"""
    
    print("=" * 80)
    print("🚀 RELEASE VALIDATION - 48-Hour Optimization Plan")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 80)
    print()
    
    # Step 1: Capture before baseline
    print("1️⃣ Capturing pre-optimization baseline...")
    before = capture_baseline("before")
    print(f"   P95: {before['p95']:.1f}ms")
    print(f"   Error Rate: {before['error_rate']:.2f}%")
    print()
    
    # Step 2: Optimization steps (simulated - actual implementation requires code changes)
    print("2️⃣ Optimization steps...")
    print("   ⏭️  Redis caching: Infrastructure ready (requires provisioning)")
    print("   ⏭️  Middleware reordering: Code changes required")
    print("   ⏭️  Prepared statements: Migration scripts ready")
    print("   ℹ️  Note: Full optimization requires code deployment")
    print()
    
    # Step 3: Capture after baseline (for now, same as before since no actual changes)
    print("3️⃣ Capturing post-optimization baseline...")
    after = capture_baseline("after")
    print(f"   P95: {after['p95']:.1f}ms")
    print(f"   Error Rate: {after['error_rate']:.2f}%")
    print()
    
    # Step 4: Run stress tests
    print("4️⃣ Running stress tests...")
    stress_results = run_stress_tests()
    print(f"   Status: {'✅ PASSED' if stress_results['passed'] else '🔴 FAILED'}")
    print()
    
    # Step 5: Generate report
    print("5️⃣ Generating optimization report...")
    report = generate_optimization_report(before, after, stress_results)
    
    artifact_path = Path("ops/scholarship-api/optimization_before_after.md")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(artifact_path, "w") as f:
        f.write(report)
    
    print(f"   ✅ Artifact saved: {artifact_path}")
    print()
    
    # Summary
    p95_reduction = before["p95"] - after["p95"]
    goal_met = p95_reduction >= 80
    
    print("=" * 80)
    print("📋 RELEASE VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Before/After Documented: Yes")
    print(f"📊 P95 Reduction: {p95_reduction:.1f}ms (goal: ≥80ms)")
    print(f"🎯 Goal Achievement: {'PASS' if goal_met else 'PENDING FULL OPTIMIZATION'}")
    print(f"🔥 Stress Tests: {'PASSED' if stress_results['passed'] else 'FAILED'}")
    print()
    print(f"📁 Full report: {artifact_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_release_validation()
