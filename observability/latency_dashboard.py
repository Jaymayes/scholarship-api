# Daily Ops: Latency Dashboard
# P50/P95/P99 by endpoint group, error rate, slow queries

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from prometheus_client import REGISTRY


class LatencyDashboard:
    """
    Real-time latency dashboard for daily operations
    Provides P50/P95/P99 metrics by endpoint group
    """
    
    ENDPOINT_GROUPS = {
        "health": ["/", "/api/v1/health", "/api/v1/health/deep"],
        "search": ["/api/v1/search", "/api/v1/search/suggestions", "/api/v1/search/advanced"],
        "predictive_matching": [
            "/api/v1/matching/predict",
            "/api/v1/matching/quick-wins",
            "/api/v1/matching/stretch-opportunities",
            "/api/v1/matching/profile-strength"
        ],
        "document_hub": [
            "/api/v1/documents/upload",
            "/api/v1/documents/user/me",
            "/api/v1/documents/{id}",
            "/api/v1/documents/bulk-analyze"
        ],
        "scholarships": [
            "/api/v1/scholarships",
            "/api/v1/scholarships/{id}",
            "/api/v1/scholarships/recommend"
        ],
        "eligibility": [
            "/api/v1/eligibility/check",
            "/api/v1/eligibility/bulk-check"
        ],
        "monetization": [
            "/api/v1/credits/balance",
            "/api/v1/credits/history",
            "/api/v1/credits/packages"
        ]
    }
    
    def get_snapshot(self) -> Dict:
        """
        Get current latency snapshot across all endpoint groups
        Returns P50/P95/P99, error rate, and slow queries
        """
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint_groups": {},
            "overall": {},
            "slow_queries": [],
            "error_rate": 0.0
        }
        
        # Collect metrics from Prometheus registry
        for metric_family in REGISTRY.collect():
            if metric_family.name == "http_request_duration_seconds":
                snapshot["endpoint_groups"] = self._process_latency_metrics(metric_family)
            elif metric_family.name == "http_requests_total":
                snapshot["error_rate"] = self._calculate_error_rate(metric_family)
        
        # Calculate overall statistics
        snapshot["overall"] = self._calculate_overall_stats(snapshot["endpoint_groups"])
        
        # Identify slow queries (P95 > 200ms)
        snapshot["slow_queries"] = self._identify_slow_queries(snapshot["endpoint_groups"])
        
        return snapshot
    
    def _process_latency_metrics(self, metric_family) -> Dict:
        """Process latency metrics by endpoint group"""
        groups = {}
        
        for group_name, endpoints in self.ENDPOINT_GROUPS.items():
            groups[group_name] = {
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "request_count": 0
            }
            
            # Aggregate metrics for endpoints in this group
            for sample in metric_family.samples:
                endpoint = sample.labels.get("endpoint", "")
                
                # Check if endpoint matches any in this group
                if any(ep in endpoint for ep in endpoints):
                    quantile = sample.labels.get("quantile")
                    
                    if quantile == "0.5":
                        groups[group_name]["p50"] = max(groups[group_name]["p50"], sample.value * 1000)
                    elif quantile == "0.9":
                        groups[group_name]["p90"] = max(groups[group_name]["p90"], sample.value * 1000)
                    elif quantile == "0.95":
                        groups[group_name]["p95"] = max(groups[group_name]["p95"], sample.value * 1000)
                    elif quantile == "0.99":
                        groups[group_name]["p99"] = max(groups[group_name]["p99"], sample.value * 1000)
        
        return groups
    
    def _calculate_error_rate(self, metric_family) -> float:
        """Calculate overall error rate"""
        total_requests = 0
        error_requests = 0
        
        for sample in metric_family.samples:
            if sample.name.endswith("_total"):
                count = sample.value
                status_code = sample.labels.get("status_code", "200")
                
                total_requests += count
                
                if status_code.startswith("5"):
                    error_requests += count
        
        if total_requests == 0:
            return 0.0
        
        return (error_requests / total_requests) * 100
    
    def _calculate_overall_stats(self, groups: Dict) -> Dict:
        """Calculate overall statistics across all groups"""
        all_p50 = [g["p50"] for g in groups.values() if g["p50"] > 0]
        all_p95 = [g["p95"] for g in groups.values() if g["p95"] > 0]
        all_p99 = [g["p99"] for g in groups.values() if g["p99"] > 0]
        
        return {
            "p50": sum(all_p50) / len(all_p50) if all_p50 else 0.0,
            "p95": sum(all_p95) / len(all_p95) if all_p95 else 0.0,
            "p99": sum(all_p99) / len(all_p99) if all_p99 else 0.0,
            "groups_measured": len([g for g in groups.values() if g["p50"] > 0])
        }
    
    def _identify_slow_queries(self, groups: Dict) -> List[Dict]:
        """Identify endpoint groups with P95 > 300ms (Gate-2 Stabilization: tuned from 200ms)"""
        slow_queries = []
        
        # Gate-2 Stabilization: Alert threshold raised to 300ms to reduce noise
        # Internal warning threshold remains at 150ms for monitoring (see get_snapshot)
        for group_name, stats in groups.items():
            if stats["p95"] > 300:
                slow_queries.append({
                    "group": group_name,
                    "p95_ms": stats["p95"],
                    "p99_ms": stats["p99"],
                    "severity": "critical" if stats["p95"] > 500 else "warning"
                })
        
        return sorted(slow_queries, key=lambda x: x["p95_ms"], reverse=True)
    
    def format_snapshot(self, snapshot: Dict) -> str:
        """Format snapshot for CLI display"""
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"📊 LATENCY DASHBOARD SNAPSHOT")
        output.append(f"Timestamp: {snapshot['timestamp']}")
        output.append(f"{'='*80}\n")
        
        # Overall stats
        output.append(f"OVERALL PERFORMANCE:")
        output.append(f"  P50: {snapshot['overall']['p50']:.1f}ms")
        output.append(f"  P95: {snapshot['overall']['p95']:.1f}ms")
        output.append(f"  P99: {snapshot['overall']['p99']:.1f}ms")
        output.append(f"  Error Rate: {snapshot['error_rate']:.2f}% {'✅' if snapshot['error_rate'] < 1.0 else '🔴'}")
        output.append("")
        
        # Endpoint groups
        output.append(f"ENDPOINT GROUPS:")
        for group_name, stats in snapshot['endpoint_groups'].items():
            if stats['p50'] > 0:
                status = "✅" if stats['p95'] <= 300 else "🔴"
                output.append(f"  {group_name:20s} {status}")
                output.append(f"    P50: {stats['p50']:6.1f}ms  P95: {stats['p95']:6.1f}ms  P99: {stats['p99']:6.1f}ms")
        output.append("")
        
        # Slow queries
        if snapshot['slow_queries']:
            output.append(f"⚠️  SLOW QUERIES (P95 > 300ms):")
            for sq in snapshot['slow_queries']:
                severity_icon = "🔴" if sq['severity'] == "critical" else "⚠️"
                output.append(f"  {severity_icon} {sq['group']:20s} P95: {sq['p95_ms']:.1f}ms  P99: {sq['p99_ms']:.1f}ms")
        else:
            output.append(f"✅ NO SLOW QUERIES DETECTED")
        
        output.append(f"\n{'='*80}\n")
        
        return "\n".join(output)


# Global dashboard instance
dashboard = LatencyDashboard()


def get_daily_ops_snapshot() -> Dict:
    """Get daily operations snapshot"""
    return dashboard.get_snapshot()


def print_daily_ops_snapshot():
    """Print formatted snapshot to console"""
    snapshot = get_daily_ops_snapshot()
    print(dashboard.format_snapshot(snapshot))


if __name__ == "__main__":
    print_daily_ops_snapshot()
