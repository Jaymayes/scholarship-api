"""
Central error building utilities for unified error responses
Eliminates double-encoding by providing single source of truth for error format
"""

import time
import uuid
from typing import Optional, Dict, Any
from fastapi import Request


def get_trace_id(request: Optional[Request] = None) -> str:
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
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build standardized error response dict
    
    Returns plain dict - never JSON string to prevent double encoding
    All error handlers must use this and pass result directly to JSONResponse
    """
    error_dict = {
        "trace_id": trace_id or str(uuid.uuid4()),
        "code": code,
        "message": message,
        "status": status,
        "timestamp": int(time.time())
    }
    
    if details:
        error_dict["details"] = details
        
    return error_dict


def build_rate_limit_error(
    trace_id: Optional[str] = None,
    retry_after_seconds: int = 60
) -> Dict[str, Any]:
    """Build rate limit specific error with retry information"""
    return build_error(
        code="RATE_LIMITED",
        message="Rate limit exceeded: 5 requests per minute",
        status=429,
        details={"retry_after_seconds": retry_after_seconds},
        trace_id=trace_id
    )


def build_auth_error(
    message: str = "Authentication required",
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """Build authentication error response"""
    return build_error(
        code="UNAUTHORIZED",
        message=message,
        status=401,
        trace_id=trace_id
    )


def build_validation_error(
    message: str = "Invalid input data",
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
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
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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