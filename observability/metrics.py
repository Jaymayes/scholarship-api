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

active_scholarships = Gauge(
    'active_scholarships_total',
    'Total number of active scholarships'
)

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

def setup_metrics(app: FastAPI):
    """Setup metrics endpoint"""
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        try:
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"Failed to generate metrics: {str(e)}")
            return Response(
                content="# Failed to generate metrics\n",
                status_code=500,
                media_type=CONTENT_TYPE_LATEST
            )
    
    logger.info("Metrics endpoint configured at /metrics")