"""
Standardized error handlers for the Scholarship API
All errors return unified schema: { trace_id, code, message, status, timestamp }
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from datetime import datetime
from typing import Union, Dict, Any
import traceback
import time
from utils.logger import get_logger

logger = get_logger(__name__)


def create_error_response(
    request: Request, 
    status_code: int, 
    error_code: str, 
    message: str,
    details: dict = None
) -> dict:
    """Create standardized error response format"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    error_response = {
        "trace_id": trace_id,
        "code": error_code,
        "message": message,
        "status": status_code,
        "timestamp": int(time.time())
    }
    
    if details:
        error_response["details"] = details
    
    return error_response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized error format"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    
    error_response = create_error_response(
        request, exc.status_code, error_code, str(exc.detail)
    )
    
    # Log appropriate level based on status code
    if exc.status_code >= 500:
        logger.error(
            f"Server error {exc.status_code} on {request.method} {request.url.path}",
            extra={"trace_id": trace_id, "status_code": exc.status_code}
        )
    elif exc.status_code == 404:
        logger.info(
            f"Not found: {request.method} {request.url.path}",
            extra={"trace_id": trace_id}
        )
    else:
        logger.warning(
            f"Client error {exc.status_code} on {request.method} {request.url.path}",
            extra={"trace_id": trace_id, "status_code": exc.status_code}
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with detailed field information"""
    validation_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_details.append({
            "field": field_path,
            "message": error["msg"],
            "value": error.get("input", None)
        })
    
    error_response = create_error_response(
        request, 422, "VALIDATION_ERROR", "Request validation failed", 
        {"fields": validation_details}
    )
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "trace_id": error_response["trace_id"], 
            "validation_errors": validation_details
        }
    )
    
    return JSONResponse(status_code=422, content=error_response)


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded with standard headers"""
    error_response = create_error_response(
        request, 429, "RATE_LIMITED", 
        f"Rate limit exceeded: {exc.detail}"
    )
    
    # Extract rate limit info from exception
    headers = {
        "Retry-After": "60",  # Retry after 1 minute
        "X-RateLimit-Limit": str(getattr(exc, 'limit', 'unknown')),
        "X-RateLimit-Remaining": "0"
    }
    
    logger.warning(
        f"Rate limit exceeded for {request.method} {request.url.path}",
        extra={"trace_id": error_response["trace_id"]}
    )
    
    return JSONResponse(
        status_code=429, 
        content=error_response,
        headers=headers
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected server errors"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        extra={
            "trace_id": trace_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    error_response = create_error_response(
        request, 500, "INTERNAL_ERROR", 
        "An internal server error occurred"
    )
    
    return JSONResponse(status_code=500, content=error_response)


# Specific handlers for common status codes
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 Not Found errors"""
    error_response = create_error_response(
        request, 404, "NOT_FOUND",
        f"The requested resource '{request.url.path}' was not found"
    )
    
    logger.info(
        f"Resource not found: {request.method} {request.url.path}",
        extra={"trace_id": error_response["trace_id"]}
    )
    
    return JSONResponse(status_code=404, content=error_response)


async def method_not_allowed_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 405 Method Not Allowed errors"""
    error_response = create_error_response(
        request, 405, "METHOD_NOT_ALLOWED",
        f"Method {request.method} not allowed for '{request.url.path}'"
    )
    
    logger.warning(
        f"Method not allowed: {request.method} {request.url.path}",
        extra={"trace_id": error_response["trace_id"]}
    )
    
    return JSONResponse(status_code=405, content=error_response)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with appropriate logging"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    error_response = {
        "trace_id": trace_id,
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "status": 500,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Log the full exception for debugging
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}: {str(exc)}",
        extra={
            "trace_id": trace_id,
            "exception": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(status_code=500, content=error_response)


async def not_found_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle 404 errors with standardized format"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    error_response = {
        "trace_id": trace_id,
        "code": "NOT_FOUND",
        "message": "The requested resource was not found",
        "status": 404,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(
        f"404 error on {request.method} {request.url.path}",
        extra={"trace_id": trace_id}
    )
    
    return JSONResponse(status_code=404, content=error_response)


async def method_not_allowed_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle 405 errors with standardized format"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    error_response = {
        "trace_id": trace_id,
        "code": "METHOD_NOT_ALLOWED",
        "message": f"Method {request.method} not allowed for this endpoint",
        "status": 405,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(
        f"405 error: {request.method} not allowed on {request.url.path}",
        extra={"trace_id": trace_id}
    )
    
    return JSONResponse(status_code=405, content=error_response)