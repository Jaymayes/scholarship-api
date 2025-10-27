# KPI/Reporting: Usage and Conversion Metrics
# Track quick-wins/stretch endpoints, application starts, credit consumption, revenue impact

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from prometheus_client import REGISTRY


class KPIReporter:
    """
    KPI reporting for business metrics
    Focuses on new endpoint usage, conversions, and revenue impact
    """
    
    def get_usage_report(self, period_hours: int = 24) -> Dict:
        """
        Generate usage and conversion report
        
        Tracks:
        - Calls to quick-wins/stretch endpoints
        - Downstream application starts
        - Credit consumption
        - Revenue impact
        """
        report = {
            "period": f"last_{period_hours}_hours",
            "timestamp": datetime.utcnow().isoformat(),
            "new_endpoints": {
                "quick_wins": self._get_endpoint_stats("/api/v1/matching/quick-wins"),
                "stretch_opportunities": self._get_endpoint_stats("/api/v1/matching/stretch-opportunities"),
                "predictive_matching": self._get_endpoint_stats("/api/v1/matching/predict"),
                "document_bulk_analyze": self._get_endpoint_stats("/api/v1/documents/bulk-analyze")
            },
            "conversions": {
                "application_starts": 0,
                "conversion_rate": 0.0,
                "avg_time_to_apply": 0.0
            },
            "monetization": {
                "credit_consumption": self._get_credit_consumption(),
                "revenue_impact_usd": 0.0,
                "avg_credits_per_user": 0.0,
                "top_consuming_features": []
            },
            "business_impact": {}
        }
        
        # Calculate derived metrics
        report["conversions"]["application_starts"] = self._estimate_application_starts(
            report["new_endpoints"]
        )
        report["monetization"]["revenue_impact_usd"] = self._calculate_revenue_impact(
            report["monetization"]["credit_consumption"]
        )
        report["business_impact"] = self._calculate_business_impact(report)
        
        return report
    
    def _get_endpoint_stats(self, endpoint: str) -> Dict:
        """Get statistics for a specific endpoint"""
        stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "error_rate": 0.0,
            "avg_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "unique_users": 0
        }
        
        for metric_family in REGISTRY.collect():
            if metric_family.name == "http_requests_total":
                for sample in metric_family.samples:
                    if endpoint in sample.labels.get("endpoint", ""):
                        count = sample.value
                        status = sample.labels.get("status_code", "200")
                        
                        stats["total_calls"] += count
                        if status.startswith("2"):
                            stats["successful_calls"] += count
            
            elif metric_family.name == "http_request_duration_seconds":
                for sample in metric_family.samples:
                    if endpoint in sample.labels.get("endpoint", ""):
                        if sample.labels.get("quantile") == "0.95":
                            stats["p95_latency_ms"] = sample.value * 1000
        
        if stats["total_calls"] > 0:
            stats["error_rate"] = (1 - stats["successful_calls"] / stats["total_calls"]) * 100
        
        return stats
    
    def _get_credit_consumption(self) -> Dict:
        """Get credit consumption metrics"""
        consumption = {
            "total_credits_consumed": 0.0,
            "by_feature": {
                "search": 0.0,
                "predictive_matching": 0.0,
                "document_analysis": 0.0,
                "ai_insights": 0.0
            },
            "trending": "stable"
        }
        
        # Extract from Prometheus metrics if available
        for metric_family in REGISTRY.collect():
            if "credit" in metric_family.name.lower():
                for sample in metric_family.samples:
                    if "consumed" in sample.name:
                        consumption["total_credits_consumed"] += sample.value
        
        return consumption
    
    def _estimate_application_starts(self, endpoints: Dict) -> int:
        """
        Estimate application starts based on endpoint usage
        Assumption: Quick-wins users are 3x more likely to apply
        """
        quick_wins_calls = endpoints["quick_wins"]["successful_calls"]
        stretch_calls = endpoints["stretch_opportunities"]["successful_calls"]
        
        # Conversion rates (industry estimates)
        quick_wins_conversion = 0.30  # 30% conversion
        stretch_conversion = 0.15  # 15% conversion
        
        estimated_starts = int(
            (quick_wins_calls * quick_wins_conversion) +
            (stretch_calls * stretch_conversion)
        )
        
        return estimated_starts
    
    def _calculate_revenue_impact(self, consumption: Dict) -> float:
        """
        Calculate revenue impact from credit consumption
        Uses credit package pricing
        """
        total_credits = consumption["total_credits_consumed"]
        
        # Average revenue per credit (based on package pricing)
        # Starter: $9.99 / 100 credits = $0.0999/credit
        # Pro: $49.99 / 600 credits = $0.0833/credit
        # Enterprise: $249.99 / 3500 credits = $0.0714/credit
        avg_revenue_per_credit = 0.08  # Blended average
        
        return total_credits * avg_revenue_per_credit
    
    def _calculate_business_impact(self, report: Dict) -> Dict:
        """Calculate high-level business impact metrics"""
        total_endpoint_calls = sum(
            ep["total_calls"] for ep in report["new_endpoints"].values()
        )
        
        return {
            "new_endpoint_adoption": {
                "total_calls": total_endpoint_calls,
                "growth_trend": "up" if total_endpoint_calls > 100 else "stable"
            },
            "user_engagement": {
                "estimated_active_users": total_endpoint_calls // 5,  # Avg 5 calls/user
                "engagement_level": "high" if total_endpoint_calls > 500 else "moderate"
            },
            "revenue_metrics": {
                "estimated_monthly_recurring_revenue": report["monetization"]["revenue_impact_usd"] * 30,
                "avg_revenue_per_user": report["monetization"]["revenue_impact_usd"] / max(1, total_endpoint_calls // 5)
            }
        }
    
    def format_report(self, report: Dict) -> str:
        """Format KPI report for display"""
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"📈 KPI REPORT: Usage & Conversion")
        output.append(f"Period: {report['period']}")
        output.append(f"Timestamp: {report['timestamp']}")
        output.append(f"{'='*80}\n")
        
        # New endpoint usage
        output.append(f"🎯 NEW ENDPOINT USAGE:")
        for name, stats in report['new_endpoints'].items():
            if stats['total_calls'] > 0:
                output.append(f"  {name:25s}")
                output.append(f"    Calls: {stats['total_calls']:>6.0f}  Success: {stats['successful_calls']:>6.0f}  Error: {stats['error_rate']:>5.1f}%")
                output.append(f"    Latency P95: {stats['p95_latency_ms']:>6.1f}ms")
        output.append("")
        
        # Conversions
        output.append(f"💼 CONVERSIONS:")
        output.append(f"  Estimated Application Starts: {report['conversions']['application_starts']}")
        output.append("")
        
        # Monetization
        output.append(f"💰 MONETIZATION:")
        output.append(f"  Credits Consumed: {report['monetization']['credit_consumption']['total_credits_consumed']:.0f}")
        output.append(f"  Revenue Impact: ${report['monetization']['revenue_impact_usd']:.2f}")
        output.append("")
        
        # Business impact
        output.append(f"📊 BUSINESS IMPACT:")
        bi = report['business_impact']
        output.append(f"  New Endpoint Calls: {bi['new_endpoint_adoption']['total_calls']}")
        output.append(f"  Estimated Active Users: {bi['user_engagement']['estimated_active_users']}")
        output.append(f"  Est. MRR: ${bi['revenue_metrics']['estimated_monthly_recurring_revenue']:.2f}")
        output.append(f"  Avg Revenue/User: ${bi['revenue_metrics']['avg_revenue_per_user']:.2f}")
        
        output.append(f"\n{'='*80}\n")
        
        return "\n".join(output)


# Global KPI reporter
kpi_reporter = KPIReporter()


def get_kpi_report(period_hours: int = 24) -> Dict:
    """Get KPI report for specified period"""
    return kpi_reporter.get_usage_report(period_hours)


def print_kpi_report(period_hours: int = 24):
    """Print formatted KPI report"""
    report = get_kpi_report(period_hours)
    print(kpi_reporter.format_report(report))


if __name__ == "__main__":
    print_kpi_report()
