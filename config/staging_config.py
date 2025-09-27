"""
Staging Environment Configuration
Enterprise-grade staging deployment with 48-72 hour soak validation
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings, Field

class StagingValidationConfig(BaseSettings):
    """Staging validation configuration with executive-mandated gates"""
    
    # Traffic Management
    traffic_shadow_percentage: int = Field(15, ge=10, le=20)  # 10-20% production mirror
    synthetic_traffic_enabled: bool = Field(True)
    
    # Security Gates (Must-Pass)
    host_validation_success_rate: float = Field(99.0, ge=99.0)  # ≥99% unknown hosts rejected
    unexpected_2xx_tolerance: int = Field(0)  # 0 unexpected 2xx on unknown hosts
    ssl_handshake_failure_rate: float = Field(0.1, le=0.1)  # ≤0.1% SSL failures
    cert_expiry_alert_days: int = Field(30)  # Alert when cert expires ≤30 days
    
    # Reliability/SLO Gates
    availability_target: float = Field(99.9, ge=99.9)  # ≥99.9% availability
    error_budget_burn_limit: float = Field(5.0, le=5.0)  # ≤5% monthly budget
    p95_latency_target_ms: int = Field(120, le=120)  # P95 ≤120ms read endpoints
    p99_latency_target_ms: int = Field(300, le=300)  # P99 ≤300ms
    error_schema_compliance: float = Field(99.5, ge=99.5)  # ≥99.5% standardized errors
    
    # Performance Baseline Tolerance
    latency_delta_tolerance: float = Field(5.0, le=5.0)  # Within 5% of baseline
    
    # Production Rollout Thresholds
    canary_p95_latency_threshold: float = Field(15.0)  # +15% vs baseline triggers pause
    canary_5xx_rate_threshold: float = Field(0.5)  # >0.5% triggers pause
    canary_tls_failure_threshold: float = Field(0.2)  # >0.2% triggers pause
    
    # Monitoring Windows
    soak_duration_hours: int = Field(48, ge=48, le=72)  # 48-72 hour soak
    consecutive_pass_hours: int = Field(48)  # 48 consecutive hours for Go/No-Go
    
    # Observability Requirements
    log_retention_days: int = Field(30)
    structured_logging_enabled: bool = Field(True)
    privacy_filters_enabled: bool = Field(True)
    
    class Config:
        env_prefix = "STAGING_"
        case_sensitive = False

# Global staging config
staging_config = StagingValidationConfig()

# Alert Thresholds for Dashboards
ALERT_THRESHOLDS = {
    "security": {
        "unknown_host_rejections_per_hour": 100,  # Spike detection
        "ssl_handshake_failures_per_minute": 5,
        "cert_expiry_warning_days": 30,
        "verify_full_compliance_percentage": 99.0
    },
    "reliability": {
        "availability_percentage": 99.9,
        "p95_latency_ms": 120,
        "p99_latency_ms": 300,
        "error_rate_percentage": 0.5,
        "db_retry_success_rate": 95.0
    },
    "performance": {
        "response_time_spike_threshold": 1.15,  # 15% increase
        "connection_pool_saturation": 80.0,
        "memory_usage_percentage": 85.0,
        "cpu_usage_percentage": 80.0
    },
    "business": {
        "seo_crawl_success_rate": 98.0,
        "provider_api_success_rate": 99.0,
        "page_load_p95_delta": 10.0  # 10% increase threshold
    }
}

# Staging Environment Allowlist (SEO + Health Checks)
STAGING_HOST_ALLOWLIST = [
    # Core hosts
    "localhost",
    "127.0.0.1",
    "testserver",
    
    # Replit staging domains
    "*.replit.app",
    "*.replit.dev", 
    "*.repl.co",
    "*.picard.replit.dev",
    "*.kirk.replit.dev",
    "*.spock.replit.dev",
    
    # SEO Auto Page Maker domains (CRITICAL for CAC protection)
    "seo-staging.scholarship-api.com",
    "auto-pages-staging.scholarship-api.com",
    "scholarships-preview.education",
    "staging-scholarships.education",
    "*.scholarship-api.com",
    
    # Health check and monitoring
    "healthcheck.internal",
    "monitoring.internal",
    "uptime.staging",
    
    # CDN and edge hosts
    "*.cloudflare.com",
    "*.fastly.com",
    "cdn.staging.scholarship-api.com",
    
    # Search engine crawlers (CRITICAL for SEO)
    "crawler.google.com",
    "crawler.bing.com", 
    "crawler.duckduckgo.com",
    "bot.crawler",
    "googlebot",
    "bingbot",
    
    # Load balancer health checks
    "lb-health.staging",
    "elb-healthcheck",
    "health.aws",
    
    # Provider testing endpoints
    "provider-test.staging",
    "api-test.partners"
]

def get_staging_dashboard_config() -> Dict[str, Any]:
    """Get staging dashboard configuration for monitoring"""
    return {
        "dashboards": [
            {
                "name": "Security Validation",
                "panels": [
                    "host_validation_rejections",
                    "ssl_handshake_status", 
                    "cert_expiry_alerts",
                    "verify_full_compliance"
                ],
                "alerts": ALERT_THRESHOLDS["security"]
            },
            {
                "name": "Reliability SLOs", 
                "panels": [
                    "availability_percentage",
                    "latency_percentiles",
                    "error_rates",
                    "db_retry_success"
                ],
                "alerts": ALERT_THRESHOLDS["reliability"]
            },
            {
                "name": "Performance Baseline",
                "panels": [
                    "response_time_trends",
                    "connection_pool_health",
                    "resource_utilization",
                    "baseline_comparison"
                ],
                "alerts": ALERT_THRESHOLDS["performance"]
            },
            {
                "name": "Business Impact",
                "panels": [
                    "seo_crawler_success",
                    "provider_api_health",
                    "conversion_metrics",
                    "page_load_performance"
                ],
                "alerts": ALERT_THRESHOLDS["business"]
            }
        ],
        "alert_channels": [
            "staging-alerts-slack",
            "executive-staging-email",
            "sre-pager-duty"
        ],
        "retention_policy": "30_days",
        "export_format": "prometheus"
    }

def validate_host_allowlist_coverage() -> Dict[str, bool]:
    """Validate critical hosts are covered in allowlist"""
    critical_checks = {
        "seo_domains_covered": any("seo" in host or "auto-pages" in host for host in STAGING_HOST_ALLOWLIST),
        "health_checks_covered": any("health" in host for host in STAGING_HOST_ALLOWLIST),
        "crawler_bots_covered": any("bot" in host or "crawler" in host for host in STAGING_HOST_ALLOWLIST),
        "replit_domains_covered": any("replit" in host for host in STAGING_HOST_ALLOWLIST),
        "cdn_coverage": any("cdn" in host or "cloudflare" in host or "fastly" in host for host in STAGING_HOST_ALLOWLIST)
    }
    return critical_checks