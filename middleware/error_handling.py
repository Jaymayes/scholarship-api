"""
Unified Error Handling Middleware
Standardized error responses and logging across the API
"""

import traceback
import uuid
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
import time

from utils.logger import get_logger

logger = get_logger("error_handler")

class APIError(Exception):
    """Base API error class"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationAPIError(APIError):
    """Validation error"""
    def __init__(self, message: str, field_errors: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors} if field_errors else {}
        )

class NotFoundAPIError(APIError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )

class AuthenticationAPIError(APIError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_REQUIRED"
        )

class AuthorizationAPIError(APIError):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="INSUFFICIENT_PERMISSIONS"
        )

class RateLimitAPIError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: int):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )

def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking"""
    return str(uuid.uuid4())

def create_error_response(
    trace_id: str,
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "trace_id": trace_id,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        },
        "status": status_code
    }

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    trace_id = getattr(request.state, "trace_id", generate_trace_id())
    
    logger.error(
        f"API Error - {exc.error_code}: {exc.message}",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        trace_id=trace_id,
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    trace_id = getattr(request.state, "trace_id", generate_trace_id())
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "INSUFFICIENT_PERMISSIONS",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    logger.warning(
        f"HTTP Exception - {error_code}: {exc.detail}",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        trace_id=trace_id,
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    trace_id = getattr(request.state, "trace_id", generate_trace_id())
    
    # Extract field-specific errors
    field_errors = {}
    for error in exc.errors():
        field_path = ".".join(str(x) for x in error["loc"])
        field_errors[field_path] = {
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        }
    
    logger.warning(
        f"Validation Error: {len(field_errors)} field errors",
        extra={
            "trace_id": trace_id,
            "field_errors": field_errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        trace_id=trace_id,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details={"field_errors": field_errors}
    )
    
    return JSONResponse(
        status_code=422,
        content=response_data
    )

async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors"""
    trace_id = getattr(request.state, "trace_id", generate_trace_id())
    
    # Get retry_after safely, with fallback
    retry_after = getattr(exc, 'retry_after', 60)  # Default to 60 seconds
    
    logger.warning(
        f"Rate Limit Exceeded: {exc.detail}",
        extra={
            "trace_id": trace_id,
            "limit": exc.detail,
            "retry_after": retry_after,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        trace_id=trace_id,
        error_code="RATE_LIMIT_EXCEEDED",
        message=f"Rate limit exceeded: {exc.detail}",
        status_code=429,
        details={"retry_after": retry_after}
    )
    
    response = JSONResponse(
        status_code=429,
        content=response_data
    )
    
    # Add rate limiting headers
    response.headers["Retry-After"] = str(retry_after)
    try:
        response.headers["X-RateLimit-Limit"] = str(exc.detail.split("/")[0])
    except (AttributeError, IndexError):
        response.headers["X-RateLimit-Limit"] = "30"
    response.headers["X-RateLimit-Reset"] = str(retry_after)
    
    return response

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    trace_id = getattr(request.state, "trace_id", generate_trace_id())
    
    logger.error(
        f"Unexpected Error: {str(exc)}",
        extra={
            "trace_id": trace_id,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal error details in production
    message = "An internal error occurred"
    details = {"type": type(exc).__name__}
    
    response_data = create_error_response(
        trace_id=trace_id,
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        details=details
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data
    )

# Middleware to add trace IDs to requests
async def trace_id_middleware(request: Request, call_next):
    """Add trace ID to request state for error tracking"""
    trace_id = request.headers.get("X-Trace-ID", generate_trace_id())
    request.state.trace_id = trace_id
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    
    return response