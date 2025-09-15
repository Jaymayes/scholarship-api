"""
Prometheus Metrics for Observability
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from prometheus_client.core import GaugeMetricFamily
import prometheus_client
from fastapi import FastAPI, Response
from typing import Optional
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
    ['method', 'endpoint']
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
        duration: Optional[float] = None
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
        duration: Optional[float] = None
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
    
    def update_scholarship_count(self, count: int):
        """Update active scholarship count on unified registry"""
        if not self.enabled:
            return
            
        try:
            active_scholarships.set(count)
            logger.info(f"📊 UNIFIED METRICS: Updated active_scholarships_total to {count} on default registry")
        except Exception as e:
            logger.warning(f"Failed to update scholarship count: {str(e)}")
    
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
        # Force detailed logging to verify handler execution
        logger.error("🚨 CUSTOM METRICS HANDLER EXECUTING - This proves it's not intercepted!")
        
        # Set active scholarships count at scrape-time to ensure accuracy
        from services.scholarship_service import scholarship_service
        scholarship_count = len(scholarship_service.scholarships)
        active_scholarships.set(scholarship_count)
        logger.error(f"🎯 CRITICAL: Updated active_scholarships_total to {scholarship_count}")
        logger.error(f"🔍 SCHOLARSHIP SERVICE STATUS: {type(scholarship_service)}, count={scholarship_count}")
        
        # Use default single-process registry
        content = generate_latest()
        logger.error("✅ CUSTOM HANDLER: Generated metrics using default registry")
        
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
    
    # LIFECYCLE RECONCILIATION: Ensure scholarship count is correct on startup
    def reconcile_metrics_on_startup():
        """Reconcile metrics with actual data on startup"""
        try:
            count = metrics_service.reconcile_scholarship_count_from_service()
            logger.info(f"🚀 STARTUP RECONCILIATION: active_scholarships_total = {count}")
        except Exception as e:
            logger.error(f"Failed startup metrics reconciliation: {str(e)}")
    
    # Register CustomCollector AFTER instrumentation to ensure correct registry
    try:
        # Unregister any existing gauge to prevent name collision
        prometheus_client.REGISTRY.unregister(active_scholarships)
        logger.info("🗑️ CLEANUP: Unregistered existing active_scholarships gauge")
    except Exception as e:
        logger.info(f"ℹ️ No existing gauge to unregister: {str(e)}")
    
    # Register CustomCollector for scrape-time computation
    collector = ActiveScholarshipsCollector()
    prometheus_client.REGISTRY.register(collector)
    logger.info("✅ CUSTOM COLLECTOR: Registered ActiveScholarshipsCollector for scrape-time computation")
    
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