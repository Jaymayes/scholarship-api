"""
Request body size limit middleware
Protects against large payloads that could cause memory exhaustion or DoS attacks
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Optional
from config.settings import get_settings
import logging
import time

logger = logging.getLogger(__name__)
settings = get_settings()


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request body size limits"""
    
    def __init__(self, app, max_size: Optional[int] = None):
        super().__init__(app)
        self.max_size = max_size if max_size is not None else settings.max_request_size_bytes
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check content-length header first (most efficient)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request body size exceeded: {content_length} > {self.max_size} for {request.method} {request.url.path}"
            )
            
            # Return standardized error response
            error_response = {
                "trace_id": getattr(request.state, "trace_id", "unknown"),
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Request body size ({content_length}) exceeds maximum allowed size ({self.max_size} bytes)",
                "status": 413,
                "timestamp": int(time.time())
            }
            
            return JSONResponse(
                status_code=413,
                content={"detail": error_response}
            )
        
        response = await call_next(request)
        return response