"""
Security Headers Middleware
Implements HSTS and other security headers based on environment
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers including environment-aware HSTS
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # CEO v2.4 Section 1.3: 6/6 exact security headers
        # API/headless profile - strict CSP
        # GATE 0 EXCEPTION: Relax CSP for /docs, /redoc, and monitoring dashboard
        if request.url.path in ["/docs", "/redoc"] or request.url.path.startswith("/api/v1/monitoring/"):
            # Allow CDN resources for API documentation and monitoring dashboards
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self'"
            )
        else:
            # Strict CSP for all other endpoints
            response.headers["Content-Security-Policy"] = "default-src 'none'; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'"
        
        response.headers["Strict-Transport-Security"] = "max-age=15552000; includeSubDomains"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response
