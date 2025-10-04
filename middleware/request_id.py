"""
Request ID Middleware for Request Tracing
CEO Soft Launch Directive: Structured JSON logging with required fields
"""

import json
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import get_logger

logger = get_logger("request_id_middleware")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate request IDs for tracing"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access by other components
        request.state.trace_id = request_id

        # Track request timing
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # CEO SOFT LAUNCH: Structured JSON logging with required fields
            # Extract auth and WAF results from request state (set by other middleware)
            auth_result = getattr(request.state, "auth_result", "no_auth_required")
            waf_rule = getattr(request.state, "waf_rule", None)
            
            # Build structured log entry
            log_entry = {
                "ts": time.time(),
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "auth_result": auth_result,
                "waf_rule": waf_rule,
                "request_id": request_id,
                "user_agent": request.headers.get("user-agent", "unknown")[:100]
            }
            
            # Log as JSON string for structured parsing
            logger.info(f"REQUEST_LOG: {json.dumps(log_entry)}")

            return response

        except Exception as e:
            # Calculate latency even for errors
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Log error
            logger.error(
                f"{request.method} {request.url.path} - ERROR",
                extra={
                    "trace_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "latency_ms": latency_ms
                }
            )

            # Re-raise the exception
            raise
