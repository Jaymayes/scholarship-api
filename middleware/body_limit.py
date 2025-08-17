"""
Request body size limit middleware
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
from config.settings import get_settings

settings = get_settings()


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request body size limits"""
    
    def __init__(self, app, max_size: Optional[int] = None):
        super().__init__(app)
        self.max_size = max_size if max_size is not None else getattr(settings, 'MAX_REQUEST_BODY_BYTES', 1024 * 1024)  # 1MB default
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check content-length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            raise HTTPException(
                status_code=413,
                detail={
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                    "code": "REQUEST_TOO_LARGE",
                    "message": f"Request body too large. Maximum size is {self.max_size} bytes",
                    "status": 413
                }
            )
        
        response = await call_next(request)
        return response