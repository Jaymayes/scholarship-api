"""
Standardized error response schemas
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error detail schema"""
    trace_id: str = Field(..., description="Request trace ID for debugging")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    status: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class ValidationErrorDetail(BaseModel):
    """Validation error detail for 422 responses"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any | None = Field(None, description="Invalid value provided")


class ValidationError(BaseModel):
    """Standard validation error response"""
    trace_id: str = Field(..., description="Request trace ID")
    code: str = Field(default="VALIDATION_ERROR", description="Error code")
    message: str = Field(default="Validation failed", description="Error message")
    details: list[ValidationErrorDetail] = Field(..., description="Validation error details")
    status: int = Field(default=422, description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateLimitError(BaseModel):
    """Rate limit error response"""
    trace_id: str = Field(..., description="Request trace ID")
    code: str = Field(default="RATE_LIMIT_EXCEEDED", description="Error code")
    message: str = Field(default="Rate limit exceeded", description="Error message")
    details: dict[str, Any] = Field(default={}, description="Rate limit details")
    status: int = Field(default=429, description="HTTP status code")
    retry_after: int = Field(..., description="Seconds to wait before retrying")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
