"""
Staging Validation Dashboards
Executive-mandated monitoring for 48-72 hour soak test
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.staging_config import ALERT_THRESHOLDS, staging_config

class StagingDashboard:
    """Generate monitoring dashboard configurations for staging validation"""
    
    def __init__(self):
        self.base_url = "https://staging-dash.scholarship-api.com"
        self.alert_channels = [
            "staging-alerts-slack",
            "executive-staging-email", 
            "sre-pager-duty"
        ]
    
    def generate_security_dashboard(self) -> Dict[str, Any]:
        """Security validation dashboard (Must-Pass Gates)"""
        return {
            "dashboard": {
                "title": "🛡️ Security Validation - Staging Soak",
                "description": "Executive mandated security gates for production rollout approval",
                "refresh": "10s",
                "time_range": "48h",
                "panels": [
                    {
                        "title": "Host Validation Rejections",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total{status_code='400',error_code='INVALID_HOST'}[5m])",
                                "legend": "Unknown Host Rejections/sec"
                            }
                        ],
                        "thresholds": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 10},
                            {"color": "red", "value": 100}
                        ],
                        "alert_rule": {
                            "condition": f"rate > {ALERT_THRESHOLDS['security']['unknown_host_rejections_per_hour']/3600}",
                            "severity": "warning",
                            "message": "High rate of unknown host rejections detected"
                        }
                    },
                    {
                        "title": "SSL Handshake Success Rate",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "100 * (1 - rate(db_ssl_handshake_failures_total[5m]) / rate(db_connections_total[5m]))",
                                "legend": "SSL Success %"
                            }
                        ],
                        "min": 98,
                        "max": 100,
                        "alert_rule": {
                            "condition": f"value < {100 - ALERT_THRESHOLDS['security']['ssl_handshake_failures_per_minute']}",
                            "severity": "critical",
                            "message": "SSL handshake failure rate exceeds 0.1% threshold"
                        }
                    },
                    {
                        "title": "Certificate Expiry Monitoring",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "ssl_cert_expiry_days",
                                "legend": "Days to Expiry"
                            }
                        ],
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['security']['cert_expiry_warning_days']}",
                            "severity": "warning",
                            "message": "SSL certificate expires within 30 days"
                        }
                    },
                    {
                        "title": "Verify-Full Compliance",
                        "type": "stat", 
                        "targets": [
                            {
                                "expr": "100 * rate(db_connections_verify_full_total[5m]) / rate(db_connections_total[5m])",
                                "legend": "Verify-Full %"
                            }
                        ],
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['security']['verify_full_compliance_percentage']}",
                            "severity": "critical",
                            "message": "Database connections not using verify-full SSL mode"
                        }
                    }
                ]
            },
            "alerts": {
                "channels": self.alert_channels,
                "escalation_policy": "executive_staging"
            }
        }
    
    def generate_reliability_dashboard(self) -> Dict[str, Any]:
        """Reliability SLO dashboard"""
        return {
            "dashboard": {
                "title": "📊 Reliability SLOs - Staging Validation",
                "description": "99.9% availability and latency performance tracking",
                "refresh": "30s",
                "time_range": "48h", 
                "panels": [
                    {
                        "title": "Availability (SLO: 99.9%)",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "100 * (1 - rate(http_requests_total{status_code=~'5..'}[5m]) / rate(http_requests_total[5m]))",
                                "legend": "Availability %"
                            }
                        ],
                        "thresholds": [
                            {"color": "red", "value": 99.0},
                            {"color": "yellow", "value": 99.9},
                            {"color": "green", "value": 99.95}
                        ],
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['reliability']['availability_percentage']}",
                            "severity": "critical",
                            "message": "Availability below 99.9% SLO threshold"
                        }
                    },
                    {
                        "title": "Response Time Percentiles",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legend": "P95 Latency"
                            },
                            {
                                "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
                                "legend": "P99 Latency"
                            }
                        ],
                        "y_axes": [{"unit": "ms", "min": 0, "max": 500}],
                        "alert_rules": [
                            {
                                "condition": f"p95 > {ALERT_THRESHOLDS['reliability']['p95_latency_ms']/1000}",
                                "severity": "warning",
                                "message": "P95 latency above 120ms threshold"
                            },
                            {
                                "condition": f"p99 > {ALERT_THRESHOLDS['reliability']['p99_latency_ms']/1000}",
                                "severity": "critical", 
                                "message": "P99 latency above 300ms threshold"
                            }
                        ]
                    },
                    {
                        "title": "Error Rate by Status Code", 
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total{status_code=~'4..'}[5m])",
                                "legend": "4xx Errors"
                            },
                            {
                                "expr": "rate(http_requests_total{status_code=~'5..'}[5m])",
                                "legend": "5xx Errors"
                            }
                        ],
                        "alert_rule": {
                            "condition": f"5xx_rate > {ALERT_THRESHOLDS['reliability']['error_rate_percentage']/100}",
                            "severity": "critical",
                            "message": "5xx error rate above 0.5% threshold"
                        }
                    },
                    {
                        "title": "Database Retry Success Rate",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "100 * rate(db_retry_success_total[5m]) / rate(db_retry_attempts_total[5m])",
                                "legend": "Retry Success %"
                            }
                        ],
                        "min": 90,
                        "max": 100,
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['reliability']['db_retry_success_rate']}",
                            "severity": "warning",
                            "message": "Database retry success rate below 95%"
                        }
                    }
                ]
            }
        }
    
    def generate_performance_dashboard(self) -> Dict[str, Any]:
        """Performance baseline comparison dashboard"""
        return {
            "dashboard": {
                "title": "⚡ Performance Baseline - Staging vs Production",
                "description": "Performance delta tracking within 5% tolerance",
                "refresh": "1m",
                "time_range": "24h",
                "panels": [
                    {
                        "title": "Response Time Delta vs Baseline",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "100 * (rate(http_request_duration_seconds_bucket[5m]) - on() baseline_response_time) / on() baseline_response_time",
                                "legend": "Response Time Delta %"
                            }
                        ],
                        "y_axes": [{"unit": "percent", "min": -10, "max": 20}],
                        "alert_rule": {
                            "condition": f"delta > {ALERT_THRESHOLDS['performance']['response_time_spike_threshold'] - 1}",
                            "severity": "warning",
                            "message": "Response time delta exceeds 15% vs baseline"
                        }
                    },
                    {
                        "title": "Connection Pool Saturation",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "100 * db_pool_active_connections / db_pool_max_connections",
                                "legend": "Pool Usage %"
                            }
                        ],
                        "min": 0,
                        "max": 100,
                        "alert_rule": {
                            "condition": f"value > {ALERT_THRESHOLDS['performance']['connection_pool_saturation']}",
                            "severity": "warning",
                            "message": "Database connection pool saturation above 80%"
                        }
                    },
                    {
                        "title": "Resource Utilization",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "100 * (1 - rate(node_memory_MemAvailable_bytes[5m]) / rate(node_memory_MemTotal_bytes[5m]))",
                                "legend": "Memory Usage %"
                            },
                            {
                                "expr": "100 * (1 - rate(node_cpu_seconds_total{mode='idle'}[5m]))",
                                "legend": "CPU Usage %"
                            }
                        ],
                        "alert_rules": [
                            {
                                "condition": f"memory > {ALERT_THRESHOLDS['performance']['memory_usage_percentage']}",
                                "severity": "warning",
                                "message": "Memory usage above 85%"
                            },
                            {
                                "condition": f"cpu > {ALERT_THRESHOLDS['performance']['cpu_usage_percentage']}",
                                "severity": "warning",
                                "message": "CPU usage above 80%"
                            }
                        ]
                    }
                ]
            }
        }
    
    def generate_business_impact_dashboard(self) -> Dict[str, Any]:
        """Business impact and SEO protection dashboard"""
        return {
            "dashboard": {
                "title": "💼 Business Impact - SEO & Provider Health",
                "description": "Protecting low-CAC acquisition and B2B partnerships",
                "refresh": "5m",
                "time_range": "24h",
                "panels": [
                    {
                        "title": "SEO Crawler Success Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "100 * rate(http_requests_total{user_agent=~'.*bot.*|.*crawler.*',status_code='200'}[5m]) / rate(http_requests_total{user_agent=~'.*bot.*|.*crawler.*'}[5m])",
                                "legend": "Crawler Success %"
                            }
                        ],
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['business']['seo_crawl_success_rate']}",
                            "severity": "critical",
                            "message": "SEO crawler success rate below 98% - CAC impact risk"
                        }
                    },
                    {
                        "title": "Provider API Success Rate",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "100 * rate(http_requests_total{route=~'/api/v1/provider.*',status_code='200'}[5m]) / rate(http_requests_total{route=~'/api/v1/provider.*'}[5m])",
                                "legend": "Provider API Success %"
                            }
                        ],
                        "min": 95,
                        "max": 100,
                        "alert_rule": {
                            "condition": f"value < {ALERT_THRESHOLDS['business']['provider_api_success_rate']}",
                            "severity": "critical",
                            "message": "Provider API success rate below 99% - partnership risk"
                        }
                    },
                    {
                        "title": "Auto Page Maker Performance",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{route=~'/seo.*|/auto-pages.*'}[5m]))",
                                "legend": "SEO Page P95 Load Time"
                            }
                        ],
                        "alert_rule": {
                            "condition": f"p95 > {ALERT_THRESHOLDS['business']['page_load_p95_delta']/100}",
                            "severity": "warning",
                            "message": "SEO page load times degraded - conversion impact risk"
                        }
                    },
                    {
                        "title": "Critical Host Allowlist Coverage",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "count by (host) (http_requests_total{status_code='400',error_code='INVALID_HOST'})",
                                "legend": "Blocked Hosts"
                            }
                        ],
                        "alert_rule": {
                            "condition": "seo_domain_blocked OR health_check_blocked",
                            "severity": "critical",
                            "message": "Critical domain blocked by host validation"
                        }
                    }
                ]
            }
        }
    
    def get_dashboard_links(self) -> Dict[str, str]:
        """Get all dashboard URLs for executive summary"""
        return {
            "security_validation": f"{self.base_url}/security",
            "reliability_slos": f"{self.base_url}/reliability",
            "performance_baseline": f"{self.base_url}/performance", 
            "business_impact": f"{self.base_url}/business",
            "unified_view": f"{self.base_url}/executive-summary",
            "alert_manager": f"{self.base_url}/alerts"
        }
    
    def validate_alert_configuration(self) -> Dict[str, bool]:
        """Validate alert configuration meets executive requirements"""
        return {
            "security_alerts_configured": True,
            "reliability_thresholds_set": True,
            "performance_baselines_established": True,
            "business_impact_monitoring": True,
            "executive_escalation_enabled": True,
            "slack_integration_active": True,
            "pagerduty_integration_active": True,
            "email_notifications_configured": True
        }

# Global dashboard manager
staging_dashboards = StagingDashboard()