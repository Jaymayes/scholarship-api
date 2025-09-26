"""
HTTP Request Metrics Middleware
Tracks all HTTP requests for Prometheus metrics
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import get_logger

logger = get_logger(__name__)

class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP requests for Prometheus metrics"""

    def __init__(self, app, enable_metrics: bool = True):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        if self.enable_metrics:
            # Import metrics service here to avoid circular imports
            from observability.metrics import metrics_service
            self.metrics_service = metrics_service
        else:
            self.metrics_service = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics"""

        # Skip metrics tracking if disabled
        if not self.enable_metrics or not self.metrics_service:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Handle exceptions and track as 500 errors
            logger.error(f"Request failed with exception: {str(e)}")
            status_code = 500
            response = JSONResponse(
                content={"error": "Internal server error"},
                status_code=500
            )

        # Calculate duration
        duration = time.time() - start_time

        # Extract endpoint path (normalize to avoid high cardinality)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method

        # Record metrics
        try:
            self.metrics_service.record_http_request(
                method=method,
                endpoint=endpoint,
                status=status_code,
                duration=duration
            )
        except Exception as e:
            # Don't fail the request if metrics recording fails
            logger.warning(f"Failed to record HTTP metrics: {str(e)}")

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path to avoid high cardinality metrics"""

        # Handle common dynamic paths
        if path.startswith("/api/v1/scholarships/"):
            # Replace scholarship IDs with placeholder
            parts = path.split("/")
            if len(parts) >= 5 and parts[4].isdigit():
                return "/api/v1/scholarships/{id}"

        # Handle user/auth paths
        if path.startswith("/users/") and len(path.split("/")) >= 3:
            parts = path.split("/")
            if parts[2].isdigit() or len(parts[2]) > 10:  # Likely user ID or token
                return "/users/{id}"

        # Handle other common patterns
        if path.startswith("/auth/") and "token" in path:
            return "/auth/token"

        # Handle static file requests
        if path.startswith("/static/"):
            return "/static/*"

        # Handle metrics endpoints
        if path in ["/metrics", "/metrics-test"]:
            return path

        # Handle health endpoints
        if path in ["/health", "/healthz", "/readiness", "/readyz"]:
            return path

        # For API endpoints, keep the first few path segments
        if path.startswith("/api/"):
            parts = path.split("/")
            if len(parts) >= 4:
                return "/".join(parts[:4])  # /api/v1/resource

        # Return original path for simple endpoints
        return path
