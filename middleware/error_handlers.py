"""
Standardized error handlers for the Scholarship API
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Union, Dict, Any
import traceback
from utils.logger import get_logger

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized error format"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    error_response = {
        "trace_id": trace_id,
        "code": f"HTTP_{exc.status_code}",
        "message": exc.detail,
        "status": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add details for specific error types
    if hasattr(exc, "headers") and exc.headers:
        error_response["details"] = {"headers": exc.headers}
    
    # Log error for debugging
    logger.error(
        f"HTTP {exc.status_code} error on {request.method} {request.url.path}",
        extra={"trace_id": trace_id, "status_code": exc.status_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with detailed field information"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    validation_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_details.append({
            "field": field_path,
            "message": error["msg"],
            "value": error.get("input", None)
        })
    
    error_response = {
        "trace_id": trace_id,
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": validation_details,
        "status": 422,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={"trace_id": trace_id, "validation_errors": validation_details}
    )
    
    return JSONResponse(status_code=422, content=error_response)


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