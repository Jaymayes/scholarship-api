#!/usr/bin/env python3
"""
Daily Ops Script
Run observability endpoints: health-summary, latency-dashboard, kpi-report(24h)
Flag any endpoint group with P95 >200ms
Artifact: ops/scholarship-api/daily_ops_snapshot.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.latency_dashboard import get_daily_ops_snapshot
from observability.kpi_reporting import get_kpi_report


def run_daily_ops():
    """Execute daily operations check and generate snapshot"""
    
    print("=" * 80)
    print("📊 DAILY OPS - Scholarship API")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 80)
    print()
    
    # 1. Health Summary
    print("1️⃣ Health Summary Check...")
    from observability.latency_dashboard import dashboard
    snapshot = get_daily_ops_snapshot()
    
    health_status = {
        "status": "healthy" if snapshot["error_rate"] < 1.0 else "degraded",
        "error_rate": snapshot["error_rate"],
        "p95_overall": snapshot["overall"]["p95"],
        "p95_target": 120.0,
        "p95_compliance": snapshot["overall"]["p95"] <= 120.0
    }
    
    print(f"   Status: {health_status['status']}")
    print(f"   Error Rate: {health_status['error_rate']:.2f}%")
    print(f"   P95 Overall: {health_status['p95_overall']:.1f}ms")
    print(f"   P95 Compliance: {'✅' if health_status['p95_compliance'] else '🔴'}")
    print()
    
    # 2. Latency Dashboard
    print("2️⃣ Latency Dashboard...")
    slow_endpoints = []
    
    for group_name, stats in snapshot['endpoint_groups'].items():
        if stats['p95'] > 200 and stats['p95'] > 0:
            slow_endpoints.append({
                "group": group_name,
                "p95_ms": stats['p95'],
                "p99_ms": stats['p99'],
                "status": "warning"
            })
            print(f"   ⚠️  {group_name}: P95={stats['p95']:.1f}ms (>200ms threshold)")
    
    if not slow_endpoints:
        print("   ✅ All endpoint groups within P95 ≤200ms target")
    print()
    
    # 3. KPI Report (24h)
    print("3️⃣ KPI Report (24 hours)...")
    kpi_report = get_kpi_report(period_hours=24)
    
    total_calls = sum(ep["total_calls"] for ep in kpi_report["new_endpoints"].values())
    print(f"   New Endpoint Calls: {total_calls}")
    print(f"   Estimated Applications: {kpi_report['conversions']['application_starts']}")
    print(f"   Credits Consumed: {kpi_report['monetization']['credit_consumption']['total_credits_consumed']:.0f}")
    print(f"   Revenue Impact: ${kpi_report['monetization']['revenue_impact_usd']:.2f}")
    print()
    
    # 4. Generate Artifact
    print("4️⃣ Generating Artifact...")
    
    artifact = {
        "timestamp": datetime.utcnow().isoformat(),
        "health_summary": health_status,
        "latency_snapshot": {
            "overall": snapshot["overall"],
            "endpoint_groups": snapshot["endpoint_groups"],
            "slow_queries": snapshot["slow_queries"]
        },
        "slow_endpoints_flagged": slow_endpoints,
        "kpi_24h": {
            "total_endpoint_calls": total_calls,
            "estimated_applications": kpi_report["conversions"]["application_starts"],
            "credits_consumed": kpi_report["monetization"]["credit_consumption"]["total_credits_consumed"],
            "revenue_impact_usd": kpi_report["monetization"]["revenue_impact_usd"],
            "estimated_mrr": kpi_report["business_impact"]["revenue_metrics"]["estimated_monthly_recurring_revenue"]
        },
        "success_criteria": {
            "baseline_captured": True,
            "slow_endpoints_identified": len(slow_endpoints) > 0,
            "slow_endpoint_count": len(slow_endpoints)
        }
    }
    
    # Save to artifact location
    artifact_path = Path("ops/scholarship-api/daily_ops_snapshot.json")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(artifact_path, "w") as f:
        json.dump(artifact, f, indent=2)
    
    print(f"   ✅ Artifact saved: {artifact_path}")
    print()
    
    # 5. Summary
    print("=" * 80)
    print("📋 DAILY OPS SUMMARY")
    print("=" * 80)
    print(f"✅ Baseline Captured: {artifact['success_criteria']['baseline_captured']}")
    print(f"⚠️  Slow Endpoints Identified: {artifact['success_criteria']['slow_endpoint_count']}")
    print(f"📊 Health Status: {health_status['status'].upper()}")
    print(f"🎯 P95 Compliance: {'PASS' if health_status['p95_compliance'] else 'FAIL'}")
    print(f"💰 Revenue Impact (24h): ${kpi_report['monetization']['revenue_impact_usd']:.2f}")
    print()
    print(f"📁 Full report: {artifact_path}")
    print("=" * 80)
    
    return artifact


if __name__ == "__main__":
    run_daily_ops()
