#!/usr/bin/env python3
"""
KPI/Reporting Script
Report quick-wins and stretch-opportunities usage, conversion to applications,
credit spend, and MRR estimates
Success: Tie feature usage to revenue impact
Artifact: ops/scholarship-api/kpi_24h.txt
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.kpi_reporting import get_kpi_report


def generate_kpi_report_text(period_hours: int = 24):
    """Generate formatted KPI report text"""
    
    report_data = get_kpi_report(period_hours)
    
    # Extract key metrics
    quick_wins = report_data["new_endpoints"]["quick_wins"]
    stretch = report_data["new_endpoints"]["stretch_opportunities"]
    predict = report_data["new_endpoints"]["predictive_matching"]
    bulk_analyze = report_data["new_endpoints"]["document_bulk_analyze"]
    
    applications = report_data["conversions"]["application_starts"]
    credits = report_data["monetization"]["credit_consumption"]["total_credits_consumed"]
    revenue = report_data["monetization"]["revenue_impact_usd"]
    mrr = report_data["business_impact"]["revenue_metrics"]["estimated_monthly_recurring_revenue"]
    active_users = report_data["business_impact"]["user_engagement"]["estimated_active_users"]
    
    # Calculate conversion rates
    total_predictive_calls = quick_wins["total_calls"] + stretch["total_calls"]
    conversion_rate = (applications / total_predictive_calls * 100) if total_predictive_calls > 0 else 0
    
    # Calculate revenue per user
    revenue_per_user = revenue / active_users if active_users > 0 else 0
    
    report = f"""
{'='*80}
KPI REPORT - Scholarship API
Period: Last {period_hours} hours
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
{'='*80}

FEATURE USAGE - NEW ENDPOINTS
{'='*80}

Quick Wins Endpoint
  Total Calls:        {quick_wins['total_calls']:>10}
  Successful:         {quick_wins['successful_calls']:>10} ({quick_wins['successful_calls']/max(1, quick_wins['total_calls'])*100:.1f}%)
  Error Rate:         {quick_wins['error_rate']:>10.2f}%
  Avg Latency (P95):  {quick_wins['p95_latency_ms']:>10.1f}ms
  
Stretch Opportunities Endpoint
  Total Calls:        {stretch['total_calls']:>10}
  Successful:         {stretch['successful_calls']:>10} ({stretch['successful_calls']/max(1, stretch['total_calls'])*100:.1f}%)
  Error Rate:         {stretch['error_rate']:>10.2f}%
  Avg Latency (P95):  {stretch['p95_latency_ms']:>10.1f}ms

Predictive Matching (General)
  Total Calls:        {predict['total_calls']:>10}
  Successful:         {predict['successful_calls']:>10}
  Error Rate:         {predict['error_rate']:>10.2f}%
  Avg Latency (P95):  {predict['p95_latency_ms']:>10.1f}ms

Document Bulk Analyze
  Total Calls:        {bulk_analyze['total_calls']:>10}
  Successful:         {bulk_analyze['successful_calls']:>10}
  Error Rate:         {bulk_analyze['error_rate']:>10.2f}%
  Avg Latency (P95):  {bulk_analyze['p95_latency_ms']:>10.1f}ms


CONVERSION FUNNEL
{'='*80}

Total Predictive Endpoint Usage:  {total_predictive_calls:>10}
  ├─ Quick Wins:                  {quick_wins['total_calls']:>10} ({quick_wins['total_calls']/max(1, total_predictive_calls)*100:.1f}%)
  └─ Stretch Opportunities:       {stretch['total_calls']:>10} ({stretch['total_calls']/max(1, total_predictive_calls)*100:.1f}%)

Estimated Application Starts:     {applications:>10}
  ├─ From Quick Wins (~30%):      {int(quick_wins['successful_calls'] * 0.30):>10}
  └─ From Stretch (~15%):         {int(stretch['successful_calls'] * 0.15):>10}

Overall Conversion Rate:          {conversion_rate:>10.1f}%


CREDIT ECONOMY
{'='*80}

Total Credits Consumed:           {credits:>10.0f}

Consumption by Feature:
  Search & Discovery:             {report_data['monetization']['credit_consumption']['by_feature']['search']:>10.0f}
  Predictive Matching:            {report_data['monetization']['credit_consumption']['by_feature']['predictive_matching']:>10.0f}
  Document Analysis:              {report_data['monetization']['credit_consumption']['by_feature']['document_analysis']:>10.0f}
  AI Insights:                    {report_data['monetization']['credit_consumption']['by_feature']['ai_insights']:>10.0f}


REVENUE IMPACT
{'='*80}

Revenue Impact ({period_hours}h):         ${revenue:>10.2f}
  ├─ Avg Revenue per Credit:      ${0.08:>10.2f}
  └─ Credits Consumed:            {credits:>10.0f}

Estimated MRR:                    ${mrr:>10.2f}
  (Extrapolated from {period_hours}h period)

Active Users (Estimated):         {active_users:>10}
Revenue per User ({period_hours}h):       ${revenue_per_user:>10.2f}


BUSINESS METRICS SUMMARY
{'='*80}

Key Performance Indicators:
  
  ✅ Feature Adoption:
     - Quick Wins endpoint usage:             {quick_wins['total_calls']} calls
     - Stretch Opportunities usage:           {stretch['total_calls']} calls
     - Total new endpoint volume:             {total_predictive_calls} calls
  
  ✅ User Engagement:
     - Estimated active users:                {active_users}
     - Avg calls per user:                    {total_predictive_calls/max(1, active_users):.1f}
     - Application start rate:                {conversion_rate:.1f}%
  
  ✅ Revenue Generation:
     - Revenue from new features ({period_hours}h):   ${revenue:.2f}
     - Projected MRR:                         ${mrr:.2f}
     - Revenue per active user:               ${revenue_per_user:.2f}
  
  ✅ System Health:
     - Overall error rate:                    {(quick_wins['error_rate'] + stretch['error_rate'])/2:.2f}%
     - Avg P95 latency:                       {(quick_wins['p95_latency_ms'] + stretch['p95_latency_ms'])/2:.1f}ms


SUCCESS CRITERIA
{'='*80}

✅ Feature usage tracked:        Quick-wins ({quick_wins['total_calls']}), Stretch ({stretch['total_calls']})
✅ Conversion measured:          {applications} applications from {total_predictive_calls} predictive calls
✅ Credit spend documented:      {credits:.0f} credits consumed
✅ Revenue impact calculated:    ${revenue:.2f} ({period_hours}h) → ${mrr:.2f} MRR


INSIGHTS & RECOMMENDATIONS
{'='*80}

"""
    
    # Add insights
    if conversion_rate > 20:
        report += f"🎯 Strong Conversion: {conversion_rate:.1f}% conversion rate exceeds industry average\n"
    elif conversion_rate > 10:
        report += f"📊 Moderate Conversion: {conversion_rate:.1f}% conversion rate is acceptable\n"
    else:
        report += f"⚠️  Low Conversion: {conversion_rate:.1f}% conversion needs improvement\n"
    
    if quick_wins['total_calls'] > stretch['total_calls'] * 2:
        report += f"💡 Users prefer Quick Wins (2:1 ratio) - optimize for high-probability matches\n"
    
    if revenue_per_user > 1.0:
        report += f"💰 High Value Users: ${revenue_per_user:.2f}/user indicates strong engagement\n"
    
    if mrr > 5000:
        report += f"🚀 Strong MRR: ${mrr:.2f}/month puts us on track for growth targets\n"
    
    report += f"\n{'='*80}\n"
    
    return report


def run_kpi_reporting(period_hours: int = 24):
    """Execute KPI reporting workflow"""
    
    print("=" * 80)
    print("📈 KPI REPORTING - Scholarship API")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 80)
    print()
    
    print(f"Generating KPI report for last {period_hours} hours...")
    print()
    
    # Generate report text
    report_text = generate_kpi_report_text(period_hours)
    
    # Save to artifact location
    artifact_path = Path("ops/scholarship-api/kpi_24h.txt")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(artifact_path, "w") as f:
        f.write(report_text)
    
    # Print to console
    print(report_text)
    
    print(f"✅ Artifact saved: {artifact_path}")
    print()


if __name__ == "__main__":
    run_kpi_reporting(period_hours=24)
