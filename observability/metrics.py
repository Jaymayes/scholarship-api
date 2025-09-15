"""
Prometheus Metrics for Observability
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
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

# Active scholarships gauge for single-process metrics
active_scholarships = Gauge(
    'active_scholarships_total',
    'Total number of active scholarships'
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
        """Update active scholarship count"""
        if not self.enabled:
            return
            
        try:
            active_scholarships.set(count)
        except Exception as e:
            logger.warning(f"Failed to update scholarship count: {str(e)}")

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
    """Setup metrics endpoint"""
    # Real async handlers for proper FastAPI route registration
    async def _metrics():
        return await get_metrics()
    
    async def _routes():
        return await debug_routes(app)
    
    # TEMP DEBUG: Add scholarship count endpoint to verify service
    async def _debug_scholarships():
        """Debug endpoint to verify scholarship service status"""
        from services.scholarship_service import scholarship_service
        return {
            "service_type": str(type(scholarship_service)),
            "scholarship_count": len(scholarship_service.scholarships),
            "scholarships_sample": scholarship_service.scholarships[:3] if scholarship_service.scholarships else []
        }
    
    # GUARANTEED ENDPOINT: /internal/metrics bypasses auto-instrumentation
    app.add_api_route("/internal/metrics", _metrics, methods=["GET"], include_in_schema=False, name="internal_metrics_guaranteed")
    
    # Original endpoint (may be intercepted by auto-instrumentation)
    app.add_api_route("/metrics", _metrics, methods=["GET"], include_in_schema=False, name="metrics_primary")
    
    # Debug endpoints  
    app.add_api_route("/_debug/routes", _routes, methods=["GET"], include_in_schema=False, name="debug_routes")
    app.add_api_route("/_debug/scholarships", _debug_scholarships, methods=["GET"], include_in_schema=False, name="debug_scholarships")
    
    # Add startup diagnostics - log route table
    async def _debug_startup():
        """Startup diagnostic to verify route registration"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        logger.info(f"🔍 Startup route table: {sorted(routes)}")
        return {"registered_routes": sorted(routes)}
    
    app.add_api_route("/_debug/startup", _debug_startup, methods=["GET"], include_in_schema=False, name="debug_startup")
    
    logger.info("✅ Metrics endpoints registered - /internal/metrics (guaranteed), /metrics (may be intercepted)")
    logger.info("🔍 Use /internal/metrics for guaranteed custom handler execution")