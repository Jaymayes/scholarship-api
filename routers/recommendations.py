"""
Recommendations router - minimal implementation for production readiness
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
import time

from config.settings import settings
from middleware.auth import get_current_user
from middleware.rate_limiting import limiter
from models.business_events import create_match_generated_event
from services.event_emission import EventEmissionService
from utils.session import extract_session_id, extract_actor_id

router = APIRouter(prefix="/api/v1", tags=["recommendations"])
event_emitter = EventEmissionService()

# Rate limiting for recommendations endpoint (30 rpm as specified)
def recommendations_rate_limit():
    if limiter is None:
        def no_op_decorator(func):
            return func
        return no_op_decorator
    return limiter.limit("30/minute")

class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: list[dict] = []
    feature_status: str = "disabled"
    message: str = "Recommendations feature is currently disabled"
    total_count: int = 0

@router.get("/recommendations")
@recommendations_rate_limit()
async def get_recommendations(
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_id: str | None = Query(None, description="User ID for personalized recommendations"),
    limit: int | None = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    offset: int | None = Query(0, ge=0, description="Pagination offset")
):
    """
    Get scholarship recommendations for a user.

    Currently returns a feature-disabled response with proper rate limiting.
    This endpoint is rate limited to 30 requests per minute per user/IP.
    """
    # Authentication required in production
    if not settings.public_read_endpoints and not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for recommendations endpoint"
        )
    
    start_time = time.time()
    
    # Emit match_generated event (even for disabled feature, for KPI tracking)
    session_id = extract_session_id(request)
    actor_id = extract_actor_id(request) or (current_user.get("user_id") if current_user else user_id)
    
    processing_time_ms = (time.time() - start_time) * 1000
    
    event = create_match_generated_event(
        student_id=actor_id or "anonymous",
        num_matches=0,
        match_quality_avg=0.0,
        processing_time_ms=processing_time_ms
    )
    await event_emitter.emit(event)

    # Return feature-disabled response with proper structure
    return RecommendationResponse(
        recommendations=[],
        feature_status="disabled",
        message="Recommendations feature is currently under development",
        total_count=0
    )
