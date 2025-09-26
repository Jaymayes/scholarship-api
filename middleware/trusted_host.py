"""
Trusted Host Middleware for production security
Validates Host header against whitelist to prevent Host Header attacks
"""

import fnmatch
import time

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.settings import settings


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Host header against trusted hosts list
    Critical security control for production deployments
    """

    def __init__(self, app, allowed_hosts: list[str] = None):
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

        # Check against allowed hosts (supporting wildcards)
        if self.allowed_hosts and not self._is_host_allowed(host):
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

    def _is_host_allowed(self, host: str) -> bool:
        """Check if host matches any allowed pattern (supports wildcards)"""
        host_lower = host.lower()

        for allowed_host in self.allowed_hosts:
            allowed_lower = allowed_host.lower()

            # Exact match
            if host_lower == allowed_lower:
                return True

            # Wildcard pattern match using fnmatch
            if "*" in allowed_lower and fnmatch.fnmatch(host_lower, allowed_lower):
                return True

        return False
