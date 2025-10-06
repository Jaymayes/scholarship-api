"""
Recommendations router - minimal implementation for production readiness
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from config.settings import settings
from middleware.auth import get_current_user
from middleware.rate_limiting import limiter

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

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

    # Return feature-disabled response with proper structure
    return RecommendationResponse(
        recommendations=[],
        feature_status="disabled",
        message="Recommendations feature is currently under development",
        total_count=0
    )
