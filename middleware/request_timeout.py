"""
Request Timeout Middleware - CEO Directive (Gate 0 Requirement)

Prevents queue buildup and resource exhaustion by enforcing maximum
request processing time.

Timeout: 5 seconds (configurable)
Response: 504 Gateway Timeout on timeout
"""

import asyncio
import time
import logging
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status

logger = logging.getLogger(__name__)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce maximum request processing time
    
    Args:
        timeout: Maximum seconds allowed per request (default: 5.0)
        exclude_paths: List of paths to exclude from timeout (e.g., long-running uploads)
    """
    
    def __init__(self, app, timeout: float = 5.0, exclude_paths: List[str] | None = None):
        super().__init__(app)
        self.timeout = timeout
        self.exclude_paths = exclude_paths or [
            "/metrics",  # Prometheus scraping may be slow
            "/health",   # Health checks should not timeout
            "/readyz"    # Readiness checks should not timeout
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with timeout enforcement
        
        Returns:
            Response from app or 504 timeout response
        """
        path = request.url.path
        
        # Skip timeout for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
            
            # Log slow requests (>80% of timeout)
            duration = time.time() - start_time
            if duration > (self.timeout * 0.8):
                logger.warning(
                    f"Slow request: {request.method} {path} "
                    f"took {duration:.2f}s (timeout: {self.timeout}s)"
                )
            
            return response
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            
            logger.error(
                f"Request timeout: {request.method} {path} "
                f"exceeded {self.timeout}s limit (actual: {duration:.2f}s)"
            )
            
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request timeout",
                    "message": f"Request exceeded maximum processing time of {self.timeout}s",
                    "path": path,
                    "method": request.method,
                    "timeout_seconds": self.timeout
                }
            )
        
        except Exception as e:
            # Log unexpected errors but let them propagate
            # (they will be caught by error handling middleware)
            logger.error(
                f"Error in request timeout middleware: {type(e).__name__}: {str(e)}"
            )
            raise
