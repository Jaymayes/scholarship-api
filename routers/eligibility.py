import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from config.settings import settings
from middleware.auth import User, require_auth
from middleware.rate_limiting import eligibility_rate_limit
from models.user import UserProfile
from schemas.eligibility import (
    CitizenshipEnum,
    EligibilityCheckRequest,
    FieldOfStudyEnum,
    GradeLevelEnum,
    StateEnum,
)
from services.eligibility_service import eligibility_service
from services.scholarship_service import scholarship_service

# from routers.interaction_wrapper import log_interaction  # Will implement if needed
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def execute_eligibility_check(
    gpa: float | None = None,
    grade_level: str | None = None,
    field_of_study: str | None = None,
    citizenship: str | None = None,
    state_of_residence: str | None = None,
    age: int | None = None,
    financial_need: bool | None = None,
    scholarship_ids: list[str] | None = None,
    user_id: str | None = None,
    require_params: bool = False
) -> dict:
    """Execute eligibility check logic shared between GET and POST endpoints"""
    start_time = time.time()

    try:
        # Validate required parameters if specified
        if require_params:
            if not any([gpa, grade_level, field_of_study, citizenship, age]):
                raise HTTPException(
                    status_code=422,
                    detail="At least one eligibility parameter (gpa, grade_level, field_of_study, citizenship, or age) is required"
                )

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
@eligibility_rate_limit()
async def check_eligibility_post(
    request: Request,
    request_data: EligibilityCheckRequest,
    current_user: User = Depends(require_auth())  # HOTFIX: Always require authentication
):
    """
    Check scholarship eligibility using POST with request body.

    Enhanced validation with strict input constraints.
    Requires authentication in production unless PUBLIC_READ_ENDPOINTS is enabled.
    """
    # Authentication enforced by dependency injection - no additional check needed
    return await execute_eligibility_check(
        gpa=request_data.gpa,
        grade_level=request_data.grade_level if request_data.grade_level else None,
        field_of_study=request_data.field_of_study if request_data.field_of_study else None,
        citizenship=request_data.citizenship if request_data.citizenship else None,
        state_of_residence=request_data.state_of_residence if request_data.state_of_residence else None,
        age=request_data.age,
        financial_need=request_data.financial_need,
        scholarship_ids=request_data.scholarship_ids,
        user_id=None,
        require_params=True
    )

@router.get("/eligibility/check")
@eligibility_rate_limit()
async def check_eligibility_get(
    request: Request,
    current_user: User = Depends(require_auth()),  # HOTFIX: Always require authentication
    gpa: float | None = Query(None, ge=0.0, le=4.0, description="GPA on 4.0 scale"),
    grade_level: GradeLevelEnum | None = Query(None, description="Grade level"),
    field_of_study: FieldOfStudyEnum | None = Query(None, description="Field of study"),
    citizenship: CitizenshipEnum | None = Query(None, description="Citizenship status"),
    state_of_residence: StateEnum | None = Query(None, description="State of residence"),
    age: int | None = Query(None, ge=13, le=120, description="Age"),
    financial_need: bool | None = Query(None, description="Financial need indicator"),
    scholarship_ids: str | None = Query(None, description="Comma-separated scholarship IDs"),
    user_id: str | None = Query(None, description="User ID for analytics")
):
    """
    Check scholarship eligibility using GET with query parameters.

    Enhanced validation requires at least one eligibility parameter.
    Requires authentication in production unless PUBLIC_READ_ENDPOINTS is enabled.
    """
    # QA-005 fix: Enforce authentication in production
    if not settings.public_read_endpoints and not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for eligibility endpoints"
        )
    # Convert string scholarship_ids to list if provided
    scholarship_ids_list = None
    if scholarship_ids:
        scholarship_ids_list = [s.strip() for s in scholarship_ids.split(",") if s.strip()]

    return await execute_eligibility_check(
        gpa=gpa,
        grade_level=grade_level.value if grade_level else None,
        field_of_study=field_of_study.value if field_of_study else None,
        citizenship=citizenship.value if citizenship else None,
        state_of_residence=state_of_residence.value if state_of_residence else None,
        age=age,
        financial_need=financial_need,
        scholarship_ids=scholarship_ids_list,
        user_id=user_id,
        require_params=True
    )
