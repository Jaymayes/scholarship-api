"""
Observability Dashboards - Live monitoring data endpoints
"""

import json
import psutil
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter
from prometheus_client import REGISTRY
from utils.logger import get_logger

# Import metrics module at module level to ensure counters are registered
from observability import metrics as _metrics_module  # noqa

logger = get_logger("dashboards")

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


def get_metric_value(metric_name: str, labels: dict = None):
    """Extract current value from Prometheus metrics"""
    try:
        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    if labels:
                        sample_labels = dict(zip(sample.labels.keys(), sample.labels.values())) if hasattr(sample, 'labels') else {}
                        if all(sample_labels.get(k) == v for k, v in labels.items()):
                            return sample.value
                    else:
                        return sample.value
        return 0
    except Exception as e:
        logger.error(f"Failed to get metric {metric_name}: {str(e)}")
        return 0


def collect_metrics_by_labels(metric_name: str, label_name: str):
    """Collect all metric values grouped by a specific label"""
    result = defaultdict(float)
    try:
        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    # Skip _created timestamp samples
                    if not sample.name.endswith('_created'):
                        # sample.labels is already a dict
                        key = sample.labels.get(label_name, 'unknown')
                        result[key] += sample.value
    except Exception as e:
        logger.error(f"Failed to collect {metric_name} by {label_name}: {str(e)}")
    return dict(result)


@router.get("/dashboards/auth")
async def auth_dashboard():
    """Authentication Dashboard - Real-time auth metrics"""
    
    try:
        # Import metrics to ensure they're registered
        from observability import metrics as _  # noqa
        
        # Collect all possible label combinations from recent samples
        # This is necessary because get_sample_value requires exact label match
        endpoints_statuses = set()
        for metric_family in REGISTRY.collect():
            if metric_family.name == "auth_requests_total":
                for sample in metric_family.samples:
                    if not sample.name.endswith('_created'):
                        endpoint = sample.labels.get('endpoint')
                        status = sample.labels.get('status')
                        result = sample.labels.get('result')
                        if endpoint and status and result:
                            endpoints_statuses.add((endpoint, status, result))
        
        # Now aggregate using get_sample_value for multiprocess safety
        total_2xx = 0
        total_4xx = 0
        total_5xx = 0
        requests_by_endpoint = {}
        
        for endpoint, status, result in endpoints_statuses:
            val = REGISTRY.get_sample_value('auth_requests_total', {
                'endpoint': endpoint,
                'result': result,
                'status': status
            }) or 0
            
            if status.startswith('2'):
                total_2xx += val
            elif status.startswith('4'):
                total_4xx += val
            elif status.startswith('5'):
                total_5xx += val
            
            requests_by_endpoint[endpoint] = requests_by_endpoint.get(endpoint, 0) + val
        
        # Collect token operations
        token_creates = 0
        token_failures = 0
        ops_statuses = set()
        
        for metric_family in REGISTRY.collect():
            if metric_family.name == "auth_token_operations_total":
                for sample in metric_family.samples:
                    if not sample.name.endswith('_created'):
                        op = sample.labels.get('operation')
                        st = sample.labels.get('status')
                        if op and st:
                            ops_statuses.add((op, st))
        
        for op, st in ops_statuses:
            val = REGISTRY.get_sample_value('auth_token_operations_total', {
                'operation': op,
                'status': st
            }) or 0
            
            if op == 'create' and st == 'success':
                token_creates += val
            if op == 'validate' and st == 'failure':
                token_failures += val
        
        total_requests = total_2xx + total_4xx + total_5xx
        success_rate = (total_2xx / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "dashboard": "authentication",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_requests": total_requests,
                "success_rate_pct": round(success_rate, 2),
                "2xx_count": total_2xx,
                "4xx_count": total_4xx,
                "5xx_count": total_5xx
            },
            "tokens": {
                "issued": token_creates,
                "validation_failures": token_failures,
                "error_rate_pct": round((token_failures / token_creates * 100) if token_creates > 0 else 0, 2)
            },
            "endpoints": requests_by_endpoint,
            "slo_status": {
                "success_rate": "PASS" if success_rate >= 99.0 else "FAIL",
                "error_rate": "PASS" if (total_5xx / total_requests * 100 if total_requests > 0 else 0) < 1.0 else "FAIL"
            }
        }
    except Exception as e:
        logger.error(f"Auth dashboard error: {str(e)}")
        return {"error": str(e)}


@router.get("/dashboards/waf")
async def waf_dashboard():
    """WAF Dashboard - Real-time WAF blocks and allowlist metrics"""
    
    try:
        # Access WAF metrics directly from Counter objects
        from observability.metrics import waf_blocks_total, waf_allowlist_bypasses_total
        
        blocks_by_rule = {}
        blocks_by_endpoint = {}
        allowlist_bypasses = {}
        
        # Get WAF blocks from Counter
        for sample in waf_blocks_total.collect()[0].samples:
            if sample.name.endswith('_created'):
                continue
            rule = sample.labels.get('rule_id', 'unknown')
            endpoint = sample.labels.get('endpoint', 'unknown')
            blocks_by_rule[rule] = blocks_by_rule.get(rule, 0) + sample.value
            blocks_by_endpoint[endpoint] = blocks_by_endpoint.get(endpoint, 0) + sample.value
        
        # Get allowlist bypasses from Counter
        for sample in waf_allowlist_bypasses_total.collect()[0].samples:
            if sample.name.endswith('_created'):
                continue
            endpoint = sample.labels.get('endpoint', 'unknown')
            allowlist_bypasses[endpoint] = allowlist_bypasses.get(endpoint, 0) + sample.value
        
        total_blocks = sum(blocks_by_rule.values())
        total_bypasses = sum(allowlist_bypasses.values())
        
        top_rules = sorted(blocks_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
        top_endpoints = sorted(blocks_by_endpoint.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "dashboard": "waf",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_blocks": total_blocks,
                "total_allowlist_bypasses": total_bypasses,
                "unique_rules_triggered": len(blocks_by_rule),
                "unique_endpoints_blocked": len(blocks_by_endpoint)
            },
            "top_blocking_rules": [{"rule": rule, "count": count} for rule, count in top_rules],
            "top_blocked_endpoints": [{"endpoint": ep, "count": count} for ep, count in top_endpoints],
            "allowlist_bypasses_by_endpoint": allowlist_bypasses,
            "false_positive_candidates": [
                {"endpoint": ep, "blocks": count, "reason": "High block rate on auth endpoint"}
                for ep, count in blocks_by_endpoint.items()
                if "/auth/" in ep and count > 10
            ]
        }
    except Exception as e:
        logger.error(f"WAF dashboard error: {str(e)}")
        return {"error": str(e)}


@router.get("/dashboards/infrastructure")
async def infrastructure_dashboard():
    """Infrastructure Dashboard - System health and performance metrics"""
    
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Access HTTP metrics directly from Counter
        from observability.metrics import http_requests_total
        
        total_requests = 0
        total_5xx = 0
        total_4xx = 0
        
        for sample in http_requests_total.collect()[0].samples:
            if sample.name.endswith('_created'):
                continue
            total_requests += sample.value
            status = str(sample.labels.get('status', ''))
            if status.startswith('5'):
                total_5xx += sample.value
            elif status.startswith('4'):
                total_4xx += sample.value
        
        latency_p95 = 0
        latency_p50 = 0
        try:
            for metric in REGISTRY.collect():
                if metric.name == "http_request_duration_seconds":
                    for sample in metric.samples:
                        if sample.name.endswith("_sum"):
                            continue
                        if "quantile" in getattr(sample, 'labels', {}):
                            q = float(sample.labels.get('quantile', 0))
                            if abs(q - 0.95) < 0.01:
                                latency_p95 = sample.value * 1000
                            if abs(q - 0.50) < 0.01:
                                latency_p50 = sample.value * 1000
        except:
            pass
        
        error_rate_5xx = (total_5xx / total_requests * 100) if total_requests > 0 else 0
        error_rate_4xx = (total_4xx / total_requests * 100) if total_requests > 0 else 0
        
        uptime_slo = 99.9
        current_uptime = 100.0 - error_rate_5xx if error_rate_5xx < 1.0 else 99.0
        
        return {
            "dashboard": "infrastructure",
            "timestamp": datetime.utcnow().isoformat(),
            "system_resources": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "cpu_alert": "HIGH" if cpu_percent > 70 else "OK",
                "memory_alert": "LOW" if memory.percent > 70 else "OK"
            },
            "performance": {
                "total_requests": total_requests,
                "p50_latency_ms": round(latency_p50, 2),
                "p95_latency_ms": round(latency_p95, 2),
                "latency_slo_300ms": "PASS" if latency_p95 < 300 else "FAIL"
            },
            "error_rates": {
                "4xx_rate_pct": round(error_rate_4xx, 2),
                "5xx_rate_pct": round(error_rate_5xx, 2),
                "total_4xx": total_4xx,
                "total_5xx": total_5xx,
                "error_slo_1pct": "PASS" if error_rate_5xx < 1.0 else "FAIL"
            },
            "availability": {
                "current_uptime_pct": round(current_uptime, 3),
                "slo_target_pct": uptime_slo,
                "slo_status": "PASS" if current_uptime >= uptime_slo else "FAIL"
            },
            "slo_summary": {
                "latency_p95_under_300ms": latency_p95 < 300,
                "error_rate_under_1pct": error_rate_5xx < 1.0,
                "uptime_above_99_9pct": current_uptime >= 99.9,
                "overall_status": "PASS" if (latency_p95 < 300 and error_rate_5xx < 1.0 and current_uptime >= 99.9) else "FAIL"
            }
        }
    except Exception as e:
        logger.error(f"Infrastructure dashboard error: {str(e)}")
        return {"error": str(e)}


@router.get("/dashboards/overview")
async def overview_dashboard():
    """Overview Dashboard - Combined view of all metrics"""
    
    auth_data = await auth_dashboard()
    waf_data = await waf_dashboard()
    infra_data = await infrastructure_dashboard()
    
    return {
        "dashboard": "overview",
        "timestamp": datetime.utcnow().isoformat(),
        "auth": auth_data,
        "waf": waf_data,
        "infrastructure": infra_data,
        "overall_health": {
            "auth_healthy": auth_data.get("slo_status", {}).get("success_rate") == "PASS",
            "infra_healthy": infra_data.get("slo_summary", {}).get("overall_status") == "PASS",
            "waf_active": waf_data.get("summary", {}).get("total_blocks", 0) > 0,
            "status": "OPERATIONAL" if all([
                auth_data.get("slo_status", {}).get("success_rate") == "PASS",
                infra_data.get("slo_summary", {}).get("overall_status") == "PASS"
            ]) else "DEGRADED"
        }
    }
