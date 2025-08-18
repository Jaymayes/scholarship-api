"""
Trusted Host Middleware for production security
Validates Host header against whitelist to prevent Host Header attacks
"""

from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from config.settings import settings
import time


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Host header against trusted hosts list
    Critical security control for production deployments
    """

    def __init__(self, app, allowed_hosts: List[str] = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or settings.allowed_hosts
        self.enforce = settings.environment.value == "production"

    async def dispatch(self, request: Request, call_next):
        """Validate host header before processing request"""
        
        # Skip enforcement in development unless explicitly configured
        if not self.enforce and not self.allowed_hosts:
            return await call_next(request)

        host = request.headers.get("host", "").lower()
        
        # Remove port from host if present
        if ":" in host:
            host = host.split(":")[0]

        # Check against allowed hosts
        if self.allowed_hosts and host not in [h.lower() for h in self.allowed_hosts]:
            # Create error response using unified format
            error_detail = {
                "trace_id": getattr(request.state, 'trace_id', 'host_validation'),
                "code": "INVALID_HOST",
                "message": f"Host '{host}' is not allowed",
                "status": 400,
                "timestamp": int(time.time())
            }
            
            raise HTTPException(status_code=400, detail=error_detail)

        return await call_next(request)