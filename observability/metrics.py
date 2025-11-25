"""
Prometheus Metrics for Observability
"""


import prometheus_client
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from prometheus_client.core import GaugeMetricFamily

from observability.alerts import setup_alerting
from observability.domain_metrics import domain_metrics_service, setup_domain_metrics
from utils.logger import get_logger

logger = get_logger("metrics")

# Metrics definitions
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.12, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')]
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['query_type', 'status']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

interactions_logged_total = Counter(
    'interactions_logged_total',
    'Total interactions logged',
    ['event_type', 'status']
)

# Rate limiting metrics
rate_limit_rejected_total = Counter(
    'rate_limit_rejected_total',
    'Total rate-limited requests rejected',
    ['endpoint', 'method', 'limit_type']
)

# Auth metrics for dashboard
auth_requests_total = Counter(
    'auth_requests_total',
    'Total authentication requests',
    ['endpoint', 'result', 'status']
)

auth_token_operations_total = Counter(
    'auth_token_operations_total',
    'Total token operations (create, validate, refresh)',
    ['operation', 'status']
)

# WAF metrics for dashboard
waf_blocks_total = Counter(
    'waf_blocks_total',
    'Total WAF blocks',
    ['rule_id', 'endpoint', 'method']
)

waf_allowlist_bypasses_total = Counter(
    'waf_allowlist_bypasses_total',
    'Total requests bypassing WAF via allowlist',
    ['endpoint']
)

# Agent3 Required Observability Counters
credits_debit_total = Counter(
    'credits_debit_total',
    'Total credit debit operations',
    ['status']
)

fee_reports_total = Counter(
    'fee_reports_total',
    'Total fee report operations',
    ['status']
)

applications_total = Counter(
    'applications_total',
    'Total application submissions',
    ['status']
)

providers_total = Counter(
    'providers_total',
    'Total provider registrations',
    ['status']
)

# Active scholarships gauge for real-time tracking
# METRICS DUPLICATION FIX: Removed Gauge - using only CustomCollector approach

# CUSTOM COLLECTOR: Computes value at scrape time to eliminate registry drift
class ActiveScholarshipsCollector:
    """Custom collector that computes active scholarships at scrape time"""

    def collect(self):
        """Compute active scholarships count at Prometheus scrape time"""
        try:
            from services.scholarship_service import scholarship_service
            count = len(scholarship_service.scholarships)
            logger.info(f"🔄 SCRAPE-TIME COLLECTION: active_scholarships_total = {count}")

            yield GaugeMetricFamily(
                'active_scholarships_total',
                'Total number of active scholarships',
                value=count
            )
        except Exception as e:
            logger.error(f"❌ SCRAPE-TIME COLLECTION FAILED: {str(e)}")
            # Return 0 if service unavailable
            yield GaugeMetricFamily(
                'active_scholarships_total',
                'Total number of active scholarships',
                value=0
            )


class AppInfoCollector:
    """Agent3 compliance: app_info metric with identity labels"""
    
    def collect(self):
        """Generate app_info metric per Agent3 unified execution prompt"""
        import os
        from prometheus_client.core import InfoMetricFamily
        
        app_id = os.getenv("APP_NAME", "scholarship_api")
        base_url = os.getenv("APP_BASE_URL", "https://scholarship-api-jamarrlmayes.replit.app")
        version = os.getenv("APP_VERSION", "1.0.0")
        
        # Create info metric with labels
        info = InfoMetricFamily(
            'app',
            'Application information',
            value={
                'app_id': app_id,
                'base_url': base_url,
                'version': version
            }
        )
        
        yield info

# Note: active_scholarships value set directly in /metrics endpoint to avoid circular imports

class MetricsService:
    """Service for managing Prometheus metrics"""

    def __init__(self):
        self.enabled = True

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float | None = None
    ):
        """Record HTTP request metrics"""
        if not self.enabled:
            return

        try:
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            if duration is not None:
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

        except Exception as e:
            logger.warning(f"Failed to record HTTP metrics: {str(e)}")

    def record_database_query(
        self,
        query_type: str,
        status: str,
        duration: float | None = None
    ):
        """Record database query metrics"""
        if not self.enabled:
            return

        try:
            database_queries_total.labels(
                query_type=query_type,
                status=status
            ).inc()

            if duration is not None:
                database_query_duration_seconds.labels(
                    query_type=query_type
                ).observe(duration)

        except Exception as e:
            logger.warning(f"Failed to record database metrics: {str(e)}")

    def record_interaction(self, event_type: str, status: str):
        """Record interaction logging metrics"""
        if not self.enabled:
            return

        try:
            interactions_logged_total.labels(
                event_type=event_type,
                status=status
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record interaction metrics: {str(e)}")

    def record_auth_request(self, endpoint: str, result: str, status: int):
        """Record authentication request metrics"""
        if not self.enabled:
            return

        try:
            auth_requests_total.labels(
                endpoint=endpoint,
                result=result,
                status=status
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record auth metrics: {str(e)}")

    def record_token_operation(self, operation: str, status: str):
        """Record token operation metrics (create, validate, refresh)"""
        if not self.enabled:
            return

        try:
            auth_token_operations_total.labels(
                operation=operation,
                status=status
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record token operation metrics: {str(e)}")

    def record_waf_block(self, rule_id: str, endpoint: str, method: str):
        """Record WAF block event"""
        if not self.enabled:
            return

        try:
            waf_blocks_total.labels(
                rule_id=rule_id,
                endpoint=endpoint,
                method=method
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record WAF block metrics: {str(e)}")

    def record_waf_allowlist_bypass(self, endpoint: str):
        """Record WAF allowlist bypass event"""
        if not self.enabled:
            return

        try:
            waf_allowlist_bypasses_total.labels(
                endpoint=endpoint
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record WAF bypass metrics: {str(e)}")

    def update_scholarship_count(self, count: int):
        """Update active scholarship count - using CustomCollector only (no duplication)"""
        if not self.enabled:
            return

        # CustomCollector handles this at scrape-time, no need for manual updates
        logger.info(f"📊 CUSTOM COLLECTOR: Scholarship count will be updated at scrape-time ({count} scholarships)")

    def reconcile_scholarship_count_from_service(self):
        """Reconcile scholarship count from service - startup/lifecycle hook"""
        try:
            from services.scholarship_service import scholarship_service
            count = len(scholarship_service.scholarships)
            self.update_scholarship_count(count)
            logger.info(f"🔄 LIFECYCLE RECONCILIATION: Set active_scholarships_total to {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to reconcile scholarship count from service: {str(e)}")
            return 0

# Global metrics service instance
metrics_service = MetricsService()

async def get_metrics():
    """Prometheus metrics endpoint with real-time scholarship count"""
    try:
        # Reduce log volume - use info level for normal operations
        logger.info("📊 CUSTOM METRICS HANDLER: Generating metrics")

        # CustomCollector handles active_scholarships_total at scrape-time (no manual set needed)
        from services.scholarship_service import scholarship_service
        scholarship_count = len(scholarship_service.scholarships)
        logger.info(f"📊 Updated active_scholarships_total to {scholarship_count}")

        # Use default single-process registry
        content = generate_latest()
        logger.info("✅ Generated metrics using default registry")

        return Response(
            content=content,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"❌ CUSTOM HANDLER FAILED: {str(e)}")
        return Response(
            content="# Failed to generate metrics\n",
            status_code=500,
            media_type=CONTENT_TYPE_LATEST
        )

async def debug_routes(app):
    """Debug endpoint to show all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unnamed')
            })
    return {"routes": routes, "total": len(routes)}

def setup_metrics(app: FastAPI):
    """Setup metrics using unified registry approach - work with auto-instrumentation"""

    # Priority 2 Day 2: Initialize domain metrics with strict governance
    try:
        setup_domain_metrics(env='development', service='scholarship_api', version='1.0.0')
        setup_alerting()
        logger.info("🎯 Priority 2 Day 2: Domain metrics and alerting configured")
    except Exception as e:
        logger.error(f"Failed to setup domain metrics: {e}")

    # LIFECYCLE RECONCILIATION: Ensure scholarship count is correct on startup
    def reconcile_metrics_on_startup():
        """Reconcile metrics with actual data on startup - Enhanced with domain metrics"""
        try:
            count = metrics_service.reconcile_scholarship_count_from_service()
            logger.info(f"🚀 STARTUP RECONCILIATION: active_scholarships_total = {count}")

            # Priority 2 Day 2: Record initial scholarship indexing with reconciliation
            domain_metrics_service.record_scholarship_indexed(count, current_active=count)
            logger.info(f"🎯 Domain metrics: Recorded {count} scholarships as indexed, reconciliation gauge set")

        except Exception as e:
            logger.error(f"Failed startup metrics reconciliation: {str(e)}")

    # CRITICAL FIX: Actually call the reconciliation function
    reconcile_metrics_on_startup()

    # Register CustomCollector AFTER instrumentation to ensure correct registry
    try:
        # METRICS DUPLICATION FIX: No gauge to unregister - using only CustomCollector
        logger.info("✅ DUPLICATION FIX: Using only CustomCollector (no Gauge approach)")
    except Exception as e:
        logger.info(f"ℹ️ No existing gauge to unregister: {str(e)}")

    # Register CustomCollector for scrape-time computation
    collector = ActiveScholarshipsCollector()
    prometheus_client.REGISTRY.register(collector)
    logger.info("✅ CUSTOM COLLECTOR: Registered ActiveScholarshipsCollector for scrape-time computation")
    
    # Agent3: Register app_info collector
    app_info_collector = AppInfoCollector()
    prometheus_client.REGISTRY.register(app_info_collector)
    logger.info("✅ AGENT3: Registered AppInfoCollector for identity compliance")

    # Create our own /metrics route using prometheus_client.REGISTRY
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        """Custom metrics endpoint using our registry with CustomCollector"""
        logger.info("📊 CUSTOM METRICS ENDPOINT: Serving from prometheus_client.REGISTRY")
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Test route to verify CustomCollector is working
    @app.get("/metrics-test", include_in_schema=False)
    async def metrics_test_endpoint():
        """Test endpoint to verify CustomCollector"""
        logger.info("🧪 TEST METRICS ENDPOINT: Verifying CustomCollector functionality")
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logger.info("✅ UNIFIED METRICS: Using default registry with auto-instrumentation")
    logger.info("📊 Metrics available at /metrics endpoint (served by CUSTOM ROUTE)")
    logger.info("🔄 Scholarship count will be reconciled on startup and service operations")
