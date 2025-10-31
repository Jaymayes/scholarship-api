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
        response.headers["Strict-Transport-Security"] = "max-age=15552000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'none'; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'"
        response.headers["Permissions-Policy"] = "camera=(); microphone=(); geolocation=(); payment=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response
