"""
Identity Headers Middleware - Agent3 Global Compliance

Adds X-System-Identity and X-App-Base-URL headers to all responses
per Agent3 unified execution prompt requirements.
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class IdentityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects identity headers into all HTTP responses.
    
    Required by Agent3 unified execution prompt for cross-app integration
    and preventing identity bleed across the 8-app ScholarshipAI ecosystem.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.app_id = os.getenv("APP_NAME", "scholarship_api")
        self.base_url = os.getenv("APP_BASE_URL", "https://scholarship-api-jamarrlmayes.replit.app")
    
    async def dispatch(self, request: Request, call_next):
        """Add identity headers to all responses"""
        response = await call_next(request)
        
        # Add required identity headers per Agent3 spec
        response.headers["X-System-Identity"] = self.app_id
        response.headers["X-App-Base-URL"] = self.base_url
        
        return response
