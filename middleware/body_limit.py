"""
Request body size limit middleware
Protects against large payloads that could cause memory exhaustion or DoS attacks
"""

import logging
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request body size limits"""

    def __init__(self, app, max_size: int | None = None):
        super().__init__(app)
        self.max_size = max_size if max_size is not None else settings.max_request_size_bytes

    async def dispatch(self, request: Request, call_next: Callable):
        # Check content-length header first (most efficient)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request body size exceeded: {content_length} > {self.max_size} for {request.method} {request.url.path}"
            )

            # Return unified error response format
            from utils.error_utils import build_error_response

            error_data = build_error_response(
                trace_id=getattr(request.state, "trace_id", "unknown"),
                code="PAYLOAD_TOO_LARGE",
                message=f"Request body size ({content_length}) exceeds maximum allowed size ({self.max_size} bytes)",
                status=413
            )

            return JSONResponse(
                status_code=413,
                content=error_data,
                headers={"Content-Type": "application/json"}
            )

        return await call_next(request)
