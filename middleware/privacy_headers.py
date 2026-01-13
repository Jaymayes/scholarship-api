"""
CEO v2.6 Privacy Headers - HITL-CEO-20260113-CUTOVER-V2
Propagate X-Privacy-Context; never log PII; minors => DoNotSell=true.
"""
import os
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class PrivacyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to handle privacy context headers and minor protection."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        privacy_context = request.headers.get("X-Privacy-Context", "")
        
        is_minor = "minor=true" in privacy_context.lower()
        do_not_sell = "donotsell=true" in privacy_context.lower() or is_minor
        
        request.state.privacy_context = privacy_context
        request.state.is_minor = is_minor
        request.state.do_not_sell = do_not_sell
        
        response = await call_next(request)
        
        if privacy_context:
            response.headers["X-Privacy-Context"] = privacy_context
        
        if do_not_sell:
            response.headers["X-Do-Not-Sell"] = "true"
        
        if is_minor:
            response.headers["X-Minor-Protected"] = "true"
            existing_csp = response.headers.get("Content-Security-Policy", "")
            if "connect-src" not in existing_csp:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "connect-src 'self'; "
                    "img-src 'self' data:; "
                    "style-src 'self' 'unsafe-inline'"
                )
        
        return response
