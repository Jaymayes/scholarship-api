"""
API Documentation Protection Middleware
Conditionally blocks access to docs in production environments
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config.settings import settings


class DocsProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect API documentation endpoints in production
    Returns 404 for docs endpoints when disabled for security
    """

    def __init__(self, app):
        super().__init__(app)
        self.docs_enabled = settings.should_enable_docs
        self.protected_paths = {
            "/docs",
            "/redoc",
            "/openapi.json"
        }

    async def dispatch(self, request: Request, call_next):
        """Block docs endpoints when disabled"""

        # Check if request is for protected documentation
        if request.url.path in self.protected_paths and not self.docs_enabled:
            # Return 404 instead of 403 to avoid information disclosure
            error_detail = {
                "trace_id": getattr(request.state, 'trace_id', 'docs_protection'),
                "code": "NOT_FOUND",
                "message": "The requested resource was not found",
                "status": 404,
                "timestamp": int(time.time())
            }

            return JSONResponse(
                status_code=404,
                content=error_detail
            )

        return await call_next(request)
