"""
Security Headers Middleware
Adds OWASP recommended security headers to all responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Allow iframe embedding in development for web preview
        if settings.environment.value in ["local", "development"]:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'; frame-ancestors 'self'"
        else:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
            
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # X-XSS-Protection (deprecated but kept for legacy compatibility per SEC-1103)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only in production with HTTPS per SEC-1104)
        if settings.should_enable_hsts:
            hsts_value = f"max-age={settings.hsts_max_age}"
            if settings.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if settings.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Override server header
        response.headers["Server"] = "Scholarship API"
        
        return response