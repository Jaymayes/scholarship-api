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

        # Always add basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'; frame-ancestors 'self'"

        # Add HSTS header only in production with HTTPS
        if self.settings.should_enable_hsts:
            hsts_value = f"max-age={self.settings.hsts_max_age}"
            if self.settings.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.settings.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        return response
