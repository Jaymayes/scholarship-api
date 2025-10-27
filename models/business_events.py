"""
Business Events Models
Pydantic models for event emission and validation
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class BusinessEvent(BaseModel):
    """Base model for all business events"""
    
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique request identifier")
    app: str = Field(default="scholarship_api", description="Source application name")
    env: str = Field(default="production", description="Environment (production, staging, development)")
    event_name: str = Field(..., description="Snake_case event name")
    ts: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp (UTC)")
    
    actor_type: Literal["student", "provider", "system", "admin"] = Field(..., description="Who triggered the event")
    actor_id: Optional[str] = Field(None, description="User/provider ID if authenticated")
    session_id: Optional[str] = Field(None, description="Session identifier for journey tracking")
    org_id: Optional[str] = Field(None, description="Organization ID for B2B events")
    
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event-specific metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "app": "scholarship_api",
                "env": "production",
                "event_name": "scholarship_viewed",
                "ts": "2025-10-27T14:30:00Z",
                "actor_type": "student",
                "actor_id": "user_123",
                "session_id": "session_456",
                "properties": {
                    "scholarship_id": "sch_789",
                    "source": "search",
                    "match_score": 0.85
                }
            }
        }


# Helper functions to create typed events
def create_scholarship_viewed_event(
    scholarship_id: str,
    source: str,
    match_score: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create scholarship_viewed event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="scholarship_viewed",
        actor_type="student",
        actor_id=actor_id,
        session_id=session_id,
        properties={
            "scholarship_id": scholarship_id,
            "source": source,
            "match_score": match_score
        }
    )


def create_scholarship_saved_event(
    scholarship_id: str,
    match_score: Optional[float] = None,
    eligibility_score: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create scholarship_saved event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="scholarship_saved",
        actor_type="student",
        actor_id=actor_id,
        session_id=session_id,
        properties={
            "scholarship_id": scholarship_id,
            "match_score": match_score,
            "eligibility_score": eligibility_score
        }
    )


def create_match_generated_event(
    student_id: str,
    num_matches: int,
    match_quality_avg: float,
    processing_time_ms: float,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create match_generated event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="match_generated",
        actor_type="system",
        properties={
            "student_id": student_id,
            "num_matches": num_matches,
            "match_quality_avg": match_quality_avg,
            "processing_time_ms": processing_time_ms
        }
    )


def create_application_started_event(
    scholarship_id: str,
    time_since_save_hours: Optional[float] = None,
    credit_cost: Optional[int] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create application_started event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="application_started",
        actor_type="student",
        actor_id=actor_id,
        session_id=session_id,
        properties={
            "scholarship_id": scholarship_id,
            "time_since_save_hours": time_since_save_hours,
            "credit_cost": credit_cost
        }
    )


def create_application_submitted_event(
    scholarship_id: str,
    application_time_minutes: float,
    credit_spent: Optional[int] = None,
    revenue_usd: Optional[float] = None,
    actor_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create application_submitted event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="application_submitted",
        actor_type="student",
        actor_id=actor_id,
        session_id=session_id,
        properties={
            "scholarship_id": scholarship_id,
            "application_time_minutes": application_time_minutes,
            "credit_spent": credit_spent,
            "revenue_usd": revenue_usd
        }
    )


def create_kpi_missing_data_event(
    metric_name: str,
    reason: str,
    time_window_hours: int = 24,
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create kpi_missing_data event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="kpi_missing_data",
        actor_type="system",
        properties={
            "metric_name": metric_name,
            "reason": reason,
            "time_window_hours": time_window_hours
        }
    )


def create_kpi_slo_breach_event(
    slo_type: str,
    endpoint: str,
    target_ms: float,
    actual_ms: float,
    breach_severity: str = "medium",
    request_id: Optional[uuid.UUID] = None
) -> BusinessEvent:
    """Create kpi_slo_breach event"""
    return BusinessEvent(
        request_id=request_id or uuid.uuid4(),
        event_name="kpi_slo_breach",
        actor_type="system",
        properties={
            "slo_type": slo_type,
            "endpoint": endpoint,
            "target_ms": target_ms,
            "actual_ms": actual_ms,
            "breach_severity": breach_severity
        }
    )
