"""
URL length validation middleware
Protects against overly long URLs that could cause buffer overflow or DoS attacks
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable
from config.settings import get_settings
import logging
import time

logger = logging.getLogger(__name__)
settings = get_settings()


class URLLengthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce URL length limits"""
    
    def __init__(self, app, max_length: int | None = None):
        super().__init__(app)
        self.max_length = max_length if max_length is not None else settings.max_url_length
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Calculate full URL length (path + query string)
        full_url = str(request.url)
        url_length = len(full_url)
        
        if url_length > self.max_length:
            logger.warning(
                f"URL length exceeded: {url_length} > {self.max_length} for {request.method} {request.url.path}"
            )
            
            # Return unified error response format
            from utils.error_utils import build_error_response
            
            error_data = build_error_response(
                trace_id=getattr(request.state, "trace_id", "unknown"),
                code="URI_TOO_LONG",
                message=f"URL length ({url_length}) exceeds maximum allowed length ({self.max_length})",
                status=414
            )
            
            return JSONResponse(
                status_code=414,
                content=error_data,
                headers={"Content-Type": "application/json"}
            )
        
        response = await call_next(request)
        return response