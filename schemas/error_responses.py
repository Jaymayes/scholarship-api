"""
OpenAPI error response schemas for consistent documentation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ErrorResponse(BaseModel):
    """Standard error response schema used across all endpoints"""
    trace_id: str = Field(..., description="Unique request identifier for tracing")
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    status: int = Field(..., description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp when error occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "status": 422,
                "timestamp": 1755524925,
                "details": {
                    "fields": [
                        {
                            "field": "email",
                            "message": "field required",
                            "value": None
                        }
                    ]
                }
            }
        }
    }


class ValidationErrorField(BaseModel):
    """Individual field validation error"""
    field: str = Field(..., description="Field path that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(None, description="The invalid value that was provided")


class ValidationErrorResponse(BaseModel):
    """422 Validation error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("VALIDATION_ERROR", description="Error code")
    message: str = Field("Request validation failed", description="Error message")
    status: int = Field(422, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")
    details: Dict[str, List[ValidationErrorField]] = Field(..., description="Validation details")


class UnauthorizedErrorResponse(BaseModel):
    """401 Unauthorized error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("UNAUTHORIZED", description="Error code")
    message: str = Field("Authentication required", description="Error message")
    status: int = Field(401, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "UNAUTHORIZED",
                "message": "Authentication required",
                "status": 401,
                "timestamp": 1755524925
            }
        }
    }


class ForbiddenErrorResponse(BaseModel):
    """403 Forbidden error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("FORBIDDEN", description="Error code")
    message: str = Field("Access denied", description="Error message")
    status: int = Field(403, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")


class NotFoundErrorResponse(BaseModel):
    """404 Not Found error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("NOT_FOUND", description="Error code")
    message: str = Field(..., description="Error message")
    status: int = Field(404, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "NOT_FOUND",
                "message": "The requested resource '/api/v1/nonexistent' was not found",
                "status": 404,
                "timestamp": 1755524925
            }
        }
    }


class PayloadTooLargeErrorResponse(BaseModel):
    """413 Payload Too Large error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("PAYLOAD_TOO_LARGE", description="Error code")
    message: str = Field(..., description="Request body size exceeded limit")
    status: int = Field(413, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "PAYLOAD_TOO_LARGE",
                "message": "Request body size (2000000) exceeds maximum allowed size (1048576 bytes)",
                "status": 413,
                "timestamp": 1755524925
            }
        }
    }


class URITooLongErrorResponse(BaseModel):
    """414 URI Too Long error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("URI_TOO_LONG", description="Error code")
    message: str = Field(..., description="URL length exceeded limit")
    status: int = Field(414, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "URI_TOO_LONG",
                "message": "URL length (3000) exceeds maximum allowed length (2048)",
                "status": 414,
                "timestamp": 1755524925
            }
        }
    }


class RateLimitErrorResponse(BaseModel):
    """429 Rate Limited error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("RATE_LIMITED", description="Error code")
    message: str = Field(..., description="Rate limit exceeded")
    status: int = Field(429, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "RATE_LIMITED",
                "message": "Rate limit exceeded: 100 per 60 seconds",
                "status": 429,
                "timestamp": 1755524925
            }
        }
    }


class InternalErrorResponse(BaseModel):
    """500 Internal Server Error response"""
    trace_id: str = Field(..., description="Unique request identifier")
    code: str = Field("INTERNAL_ERROR", description="Error code")
    message: str = Field("An internal server error occurred", description="Error message")
    status: int = Field(500, description="HTTP status code")
    timestamp: int = Field(..., description="Unix timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "7611df6e-11b5-47b6-9177-cd2cf51e3c27",
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "status": 500,
                "timestamp": 1755524925
            }
        }
    }


# Dictionary mapping status codes to response models for OpenAPI
ERROR_RESPONSES = {
    401: {"model": UnauthorizedErrorResponse, "description": "Authentication required"},
    403: {"model": ForbiddenErrorResponse, "description": "Access denied"},
    404: {"model": NotFoundErrorResponse, "description": "Resource not found"},
    413: {"model": PayloadTooLargeErrorResponse, "description": "Request body too large"},
    414: {"model": URITooLongErrorResponse, "description": "URL too long"},
    422: {"model": ValidationErrorResponse, "description": "Validation error"},
    429: {"model": RateLimitErrorResponse, "description": "Rate limit exceeded"},
    500: {"model": InternalErrorResponse, "description": "Internal server error"}
}