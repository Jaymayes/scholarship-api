"""
Central error building utilities for unified error responses
Eliminates double-encoding by providing single source of truth for error format
"""

import time
import uuid
from typing import Any

from fastapi import Request


def get_trace_id(request: Request | None = None) -> str:
    """
    Get or generate trace ID for request tracking
    """
    if request and hasattr(request.state, 'trace_id'):
        return request.state.trace_id
    return str(uuid.uuid4())


def build_error(
    code: str,
    message: str,
    status: int,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None
) -> dict[str, Any]:
    """
    Build standardized error response dict

    CEO v2.5 U4 Final: Simplified error format
    Schema: { "error": { "code": "...", "message": "...", "request_id": "..." } }
    
    NO top-level request_id; NO details field per U4 spec.
    Returns plain dict - never JSON string to prevent double encoding
    All error handlers must use this and pass result directly to JSONResponse
    """
    request_id = trace_id or str(uuid.uuid4())

    # CEO v2.5 U4: Error nested under "error" key
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id
        }
    }


def build_rate_limit_error(
    trace_id: str | None = None,
    retry_after_seconds: int = 60
) -> dict[str, Any]:
    """Build rate limit specific error with retry information"""
    return build_error(
        code="RATE_LIMITED",
        message=f"Rate limit exceeded. Retry after {retry_after_seconds} seconds.",
        status=429,
        trace_id=trace_id
    )


def build_auth_error(
    message: str = "Authentication required",
    trace_id: str | None = None
) -> dict[str, Any]:
    """Build authentication error response"""
    return build_error(
        code="UNAUTHORIZED",
        message=message,
        status=401,
        trace_id=trace_id
    )


def build_validation_error(
    message: str = "Invalid input data",
    details: dict[str, Any] | None = None,
    trace_id: str | None = None
) -> dict[str, Any]:
    """Build validation error response"""
    return build_error(
        code="VALIDATION_ERROR",
        message=message,
        status=422,
        details=details,
        trace_id=trace_id
    )


def build_error_response(
    trace_id: str,
    code: str,
    message: str,
    status: int,
    details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Build error response - alias for build_error with specific parameter order
    Used by middleware for consistent error format
    """
    return build_error(
        code=code,
        message=message,
        status=status,
        details=details,
        trace_id=trace_id
    )
