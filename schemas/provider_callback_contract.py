"""
Provider Onboarding Callback Contract Schema
Shared schema between provider_register and scholarship_api

CEO Directive: Gate B - Define clear integration contract
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class OnboardingStepMetadata(BaseModel):
    """Metadata for onboarding step completion"""
    
    source: str = Field(..., description="Source system (e.g., 'provider_register')")
    environment: str = Field(..., description="Environment (e.g., 'production', 'test')")
    integration_test: bool = Field(default=False, description="Whether this is an integration test")
    additional_data: dict[str, Any] = Field(default_factory=dict, description="Additional context data")


class OnboardingStepData(BaseModel):
    """
    Onboarding step completion data
    
    This is the payload sent from provider_register to scholarship_api
    when an onboarding step is completed
    """
    
    completed_at: str = Field(
        ...,
        description="ISO8601 timestamp when step was completed"
    )
    completed_by: str = Field(
        ...,
        description="Identifier of user/system that completed the step"
    )
    verification_status: Optional[str] = Field(
        None,
        description="Verification status (e.g., 'verified', 'pending', 'failed')"
    )
    metadata: Optional[OnboardingStepMetadata] = Field(
        None,
        description="Additional metadata about the completion"
    )
    
    @validator("completed_at")
    def validate_iso8601(cls, v):
        """Validate ISO8601 timestamp format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO8601 timestamp: {v}")


class OnboardingCallbackPayload(BaseModel):
    """
    Complete callback payload for provider onboarding step completion
    
    Spec Version: v1.0
    Contract Owner: scholarship_api
    Consumers: provider_register
    
    Example:
    ```json
    {
        "step_data": {
            "completed_at": "2025-11-13T18:00:00Z",
            "completed_by": "provider_register_system",
            "verification_status": "verified",
            "metadata": {
                "source": "provider_register",
                "environment": "production",
                "integration_test": false
            }
        }
    }
    ```
    """
    
    step_data: OnboardingStepData = Field(
        ...,
        description="Step completion data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_data": {
                    "completed_at": "2025-11-13T18:00:00Z",
                    "completed_by": "provider_register_system",
                    "verification_status": "verified",
                    "metadata": {
                        "source": "provider_register",
                        "environment": "production",
                        "integration_test": False,
                        "additional_data": {
                            "user_agent": "provider_register/1.0.0",
                            "client_version": "1.2.3"
                        }
                    }
                }
            }
        }


class OnboardingCallbackResponse(BaseModel):
    """
    Response from scholarship_api after processing callback
    
    Spec Version: v1.0
    """
    
    success: bool = Field(..., description="Whether callback was processed successfully")
    step_id: str = Field(..., description="ID of the completed step")
    partner_id: str = Field(..., description="ID of the partner")
    completed: bool = Field(..., description="Whether step is now marked as completed")
    completed_at: Optional[str] = Field(None, description="ISO8601 timestamp of completion")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    message: Optional[str] = Field(None, description="Human-readable message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "step_id": "step_profile_setup",
                "partner_id": "partner_123abc",
                "completed": True,
                "completed_at": "2025-11-13T18:00:00Z",
                "request_id": "req_xyz789",
                "message": "Onboarding step completed successfully"
            }
        }


class OnboardingCallbackErrorResponse(BaseModel):
    """Error response for callback failures"""
    
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    reason: str = Field(..., description="Human-readable error reason")
    step_id: Optional[str] = Field(None, description="Step ID if available")
    partner_id: Optional[str] = Field(None, description="Partner ID if available")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    hint: Optional[str] = Field(None, description="Hint for resolving the error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "InvalidStepError",
                "reason": "Step 'step_xyz' not found for partner 'partner_123'",
                "step_id": "step_xyz",
                "partner_id": "partner_123",
                "request_id": "req_abc456",
                "hint": "Verify step_id is valid and matches an onboarding step for this partner"
            }
        }


class IdempotencyRecord(BaseModel):
    """
    Idempotency record for callback tracking
    
    Prevents duplicate processing of the same callback
    """
    
    idempotency_key: str = Field(
        ...,
        description="Unique key: hash(partner_id + step_id + completed_at)"
    )
    partner_id: str = Field(..., description="Partner ID")
    step_id: str = Field(..., description="Step ID")
    completed_at: str = Field(..., description="Completion timestamp")
    request_id: str = Field(..., description="Original request ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    response: dict[str, Any] = Field(..., description="Cached response for idempotent replays")
    
    @staticmethod
    def generate_key(partner_id: str, step_id: str, completed_at: str) -> str:
        """Generate idempotency key"""
        import hashlib
        
        payload = f"{partner_id}:{step_id}:{completed_at}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
