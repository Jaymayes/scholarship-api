"""
Applications router for scholarship application tracking and revenue capture
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from middleware.auth import User, require_auth
from middleware.simple_rate_limiter import general_rate_limit
from models.business_events import (
    create_application_started_event,
    create_application_submitted_event
)
from services.event_emission import event_emitter
from utils.logger import get_logger
from utils.session import extract_session_id, extract_actor_id

logger = get_logger(__name__)
router = APIRouter()


class ApplicationStartRequest(BaseModel):
    """Request to start a scholarship application"""
    scholarship_id: str = Field(..., description="ID of the scholarship to apply for")
    time_since_save_hours: Optional[float] = Field(None, description="Hours since saving this scholarship")
    credit_cost: Optional[int] = Field(None, description="Credit cost to start application")


class ApplicationStartResponse(BaseModel):
    """Response after starting an application"""
    application_id: str
    scholarship_id: str
    started_at: datetime
    message: str = "Application started successfully"


class ApplicationSubmitRequest(BaseModel):
    """Request to submit a scholarship application"""
    scholarship_id: str = Field(..., description="ID of the scholarship being applied for")
    application_time_minutes: float = Field(..., description="Time spent on application in minutes")
    credit_spent: Optional[int] = Field(None, description="Credits spent on this application")
    revenue_usd: Optional[float] = Field(None, description="Revenue from this submission in USD")


class ApplicationSubmitResponse(BaseModel):
    """Response after submitting an application"""
    application_id: str
    scholarship_id: str
    submitted_at: datetime
    credit_spent: Optional[int]
    revenue_usd: Optional[float]
    message: str = "Application submitted successfully"


@router.post("/applications/start", response_model=ApplicationStartResponse)
@general_rate_limit()
async def start_application(
    request: Request,
    data: ApplicationStartRequest,
    current_user: User = Depends(require_auth())
):
    """
    Start a scholarship application.
    
    Emits application_started business event for conversion tracking.
    Required for save_to_apply KPI calculation.
    """
    try:
        session_id = extract_session_id(request)
        actor_id = extract_actor_id(request) or str(current_user.id) if current_user else None
        
        application_id = f"app_{data.scholarship_id}_{int(datetime.utcnow().timestamp())}"
        
        event = create_application_started_event(
            scholarship_id=data.scholarship_id,
            time_since_save_hours=data.time_since_save_hours,
            credit_cost=data.credit_cost,
            actor_id=actor_id,
            session_id=session_id
        )
        
        await event_emitter.emit(event)
        
        logger.info(f"Application started: {application_id} for scholarship {data.scholarship_id}")
        
        return ApplicationStartResponse(
            application_id=application_id,
            scholarship_id=data.scholarship_id,
            started_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start application")


@router.post("/applications/submit", response_model=ApplicationSubmitResponse)
@general_rate_limit()
async def submit_application(
    request: Request,
    data: ApplicationSubmitRequest,
    current_user: User = Depends(require_auth())
):
    """
    Submit a scholarship application.
    
    CRITICAL: Emits application_submitted business event with revenue_usd for B2C revenue tracking.
    This is the primary event for Executive Command Center revenue reporting.
    """
    try:
        session_id = extract_session_id(request)
        actor_id = extract_actor_id(request) or str(current_user.id) if current_user else None
        
        application_id = f"app_{data.scholarship_id}_{int(datetime.utcnow().timestamp())}"
        
        event = create_application_submitted_event(
            scholarship_id=data.scholarship_id,
            application_time_minutes=data.application_time_minutes,
            credit_spent=data.credit_spent,
            revenue_usd=data.revenue_usd,
            actor_id=actor_id,
            session_id=session_id
        )
        
        await event_emitter.emit(event)
        
        logger.info(
            f"Application submitted: {application_id} for scholarship {data.scholarship_id}, "
            f"revenue_usd={data.revenue_usd}, credits={data.credit_spent}"
        )
        
        return ApplicationSubmitResponse(
            application_id=application_id,
            scholarship_id=data.scholarship_id,
            submitted_at=datetime.utcnow(),
            credit_spent=data.credit_spent,
            revenue_usd=data.revenue_usd
        )
        
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit application")
