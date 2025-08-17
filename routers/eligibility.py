from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
import time

from models.user import UserProfile, EligibilityCheck, EligibilityResult
from models.scholarship import FieldOfStudy
from services.eligibility_service import eligibility_service
from services.scholarship_service import scholarship_service
from middleware.auth import get_current_user
from middleware.rate_limiting import limiter
# from routers.interaction_wrapper import log_interaction  # Will implement if needed
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models for eligibility requests
from pydantic import BaseModel

class EligibilityCheckRequest(BaseModel):
    """Eligibility check request payload for POST endpoint"""
    gpa: Optional[float] = None
    grade_level: Optional[str] = None
    field_of_study: Optional[str] = None
    citizenship: Optional[str] = None
    state_of_residence: Optional[str] = None
    age: Optional[int] = None
    financial_need: Optional[bool] = None
    scholarship_ids: Optional[List[str]] = None

async def execute_eligibility_check(
    gpa: Optional[float] = None,
    grade_level: Optional[str] = None,
    field_of_study: Optional[str] = None,
    citizenship: Optional[str] = None,
    state_of_residence: Optional[str] = None,
    age: Optional[int] = None,
    financial_need: Optional[bool] = None,
    scholarship_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None
) -> dict:
    """Execute eligibility check logic shared between GET and POST endpoints"""
    start_time = time.time()
    
    try:
        # Create user profile from provided data
        user_profile = UserProfile(
            gpa=gpa,
            grade_level=grade_level or "undergraduate",
            field_of_study=field_of_study or "other",
            citizenship=citizenship or "US",
            state_of_residence=state_of_residence,
            age=age or 20,
            financial_need=financial_need or False
        )
        
        # If no specific scholarship IDs provided, check against all scholarships
        if not scholarship_ids:
            all_scholarships = scholarship_service.get_all_scholarships()
            scholarship_ids = [s.id for s in all_scholarships]
        
        # Perform eligibility check for each scholarship
        results = eligibility_service.check_multiple_eligibilities(user_profile, scholarship_ids)
        
        # Count eligible scholarships
        eligible_count = sum(1 for result in results if result.eligible)
        
        # Calculate processing time
        took_ms = int((time.time() - start_time) * 1000)
        
        # Return metadata-rich response matching expected format
        return {
            "eligible_count": eligible_count,
            "results": [
                {
                    "scholarship_id": result.scholarship_id,
                    "eligible": result.eligible,
                    "score": result.match_score,
                    "reasons": result.reasons
                }
                for result in results
            ],
            "took_ms": took_ms,
            "user_profile": user_profile.dict(),
            "checked_scholarships": len(scholarship_ids)
        }
        
    except Exception as e:
        logger.error(f"Eligibility check failed: {str(e)}")
        raise

@router.post("/eligibility/check")
@limiter.limit("30/minute")
async def check_eligibility_post(
    request_data: EligibilityCheckRequest,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Check scholarship eligibility using POST with request body
    
    Returns detailed eligibility results with scoring and reasons.
    """
    user_id = current_user.get("user_id") if current_user else None
    
    return await execute_eligibility_check(
        gpa=request_data.gpa,
        grade_level=request_data.grade_level,
        field_of_study=request_data.field_of_study,
        citizenship=request_data.citizenship,
        state_of_residence=request_data.state_of_residence,
        age=request_data.age,
        financial_need=request_data.financial_need,
        scholarship_ids=request_data.scholarship_ids,
        user_id=user_id
    )

@router.get("/eligibility/check")
@limiter.limit("30/minute")
async def check_eligibility_get(
    request: Request,
    gpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Student GPA"),
    grade_level: Optional[str] = Query("undergraduate", description="Grade level (undergraduate, graduate, etc.)"),
    field_of_study: Optional[str] = Query("other", description="Field of study"),
    citizenship: Optional[str] = Query("US", description="Citizenship status"),
    state_of_residence: Optional[str] = Query(None, description="State of residence"),
    age: Optional[int] = Query(20, ge=16, le=100, description="Student age"),
    financial_need: Optional[bool] = Query(False, description="Has financial need"),
    scholarship_ids: Optional[List[str]] = Query(default=None, description="Specific scholarship IDs to check"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Check scholarship eligibility using GET with query parameters
    
    Returns the same detailed eligibility results as POST endpoint.
    """
    user_id = current_user.get("user_id") if current_user else None
    
    return await execute_eligibility_check(
        gpa=gpa,
        grade_level=grade_level,
        field_of_study=field_of_study,
        citizenship=citizenship,
        state_of_residence=state_of_residence,
        age=age,
        financial_need=financial_need,
        scholarship_ids=scholarship_ids,
        user_id=user_id
    )