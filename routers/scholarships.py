from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from middleware.auth import User, require_auth
from middleware.enhanced_rate_limiting import general_rate_limit, search_rate_limit
from models.scholarship import (
    FieldOfStudy,
    Scholarship,
    ScholarshipSummary,
    ScholarshipType,
    SearchFilters,
    SearchResponse,
)
from models.user import (
    EligibilityCheck,
    EligibilityResult,
    RecommendationRequest,
    UserProfile,
)
from services.analytics_service import analytics_service
from services.eligibility_service import eligibility_service
from services.scholarship_service import scholarship_service
from services.search_service import search_service
from utils.logger import get_logger
from utils.session import extract_session_id, extract_actor_id
from models.business_events import create_scholarship_saved_event
from services.event_emission import EventEmissionService

logger = get_logger(__name__)
router = APIRouter()

event_emitter = EventEmissionService()

@router.get("/scholarships", response_model=SearchResponse)
@search_rate_limit()  # QA FIX: Apply rate limiting to scholarships endpoint
async def search_scholarships(
    request: Request,  # QA FIX: Add request parameter for rate limiting
    keyword: str | None = Query(None, description="Search keyword"),
    fields_of_study: list[FieldOfStudy] = Query(default=[], description="Filter by fields of study"),
    min_amount: float | None = Query(None, ge=0, description="Minimum scholarship amount"),
    max_amount: float | None = Query(None, ge=0, description="Maximum scholarship amount"),
    scholarship_types: list[ScholarshipType] = Query(default=[], description="Filter by scholarship types"),
    states: list[str] = Query(default=[], description="Filter by US states"),
    min_gpa: float | None = Query(None, ge=0.0, le=4.0, description="Minimum GPA filter"),
    citizenship: str | None = Query(None, description="Citizenship requirement"),
    deadline_after: datetime | None = Query(None, description="Deadlines after this date"),
    deadline_before: datetime | None = Query(None, description="Deadlines before this date"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    user_id: str | None = Query(None, description="User ID for analytics"),
    # CEO WAR ROOM FIX: Optional authentication for public scholarship browsing
    current_user: User | None = None
):
    """
    Search scholarships with various filters and pagination support - QA-004 fix: Authentication enforced.
    Requires authentication unless PUBLIC_READ_ENDPOINTS feature flag is enabled.

    This endpoint allows users to search through available scholarships using
    multiple criteria including keywords, fields of study, amount ranges, and more.
    """
    # Authentication enforced by dependency injection - no additional check needed
    try:
        filters = SearchFilters(
            keyword=keyword,
            fields_of_study=fields_of_study,
            min_amount=min_amount,
            max_amount=max_amount,
            scholarship_types=scholarship_types,
            states=states,
            min_gpa=min_gpa,
            citizenship=citizenship,
            deadline_after=deadline_after,
            deadline_before=deadline_before,
            limit=limit,
            offset=offset
        )

        # Log search interaction
        analytics_service.log_search(
            user_id=user_id,
            query=keyword or "",
            result_count=0,  # Will be updated after search
            filters=filters.model_dump()
        )

        result = scholarship_service.search_scholarships(filters)

        # Update analytics with actual result count
        if analytics_service.interactions:
            analytics_service.interactions[-1].metadata["result_count"] = result.total_count

        return result

    except Exception as e:
        logger.error(f"Error searching scholarships: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during search")

@router.get("/scholarships/smart-search")
@search_rate_limit()  # QA FIX: Apply rate limiting to smart search endpoint
async def smart_search_scholarships(
    request: Request,  # QA FIX: Add request parameter for rate limiting
    keyword: str | None = Query(None, description="Search keyword"),
    fields_of_study: list[FieldOfStudy] = Query(default=[], description="Filter by fields of study"),
    min_amount: float | None = Query(None, ge=0, description="Minimum scholarship amount"),
    max_amount: float | None = Query(None, ge=0, description="Maximum scholarship amount"),
    scholarship_types: list[ScholarshipType] = Query(default=[], description="Filter by scholarship types"),
    states: list[str] = Query(default=[], description="Filter by US states"),
    min_gpa: float | None = Query(None, ge=0.0, le=4.0, description="Minimum GPA filter"),
    citizenship: str | None = Query(None, description="Citizenship requirement"),
    deadline_after: datetime | None = Query(None, description="Deadlines after this date"),
    deadline_before: datetime | None = Query(None, description="Deadlines before this date"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    user_id: str | None = Query(None, description="User ID for analytics")
):
    """
    Enhanced search with smart suggestions and search quality assessment.

    This endpoint provides the same search functionality as the basic search
    but includes additional features like search suggestions and metadata.
    """
    try:
        filters = SearchFilters(
            keyword=keyword,
            fields_of_study=fields_of_study,
            min_amount=min_amount,
            max_amount=max_amount,
            scholarship_types=scholarship_types,
            states=states,
            min_gpa=min_gpa,
            citizenship=citizenship,
            deadline_after=deadline_after,
            deadline_before=deadline_before,
            limit=limit,
            offset=offset
        )

        # Log search interaction
        analytics_service.log_search(
            user_id=user_id,
            query=keyword or "",
            result_count=0,
            filters=filters.model_dump()
        )

        result = search_service.search_with_smart_suggestions(filters)

        # Update analytics
        if analytics_service.interactions:
            analytics_service.interactions[-1].metadata["result_count"] = result["results"].total_count

        return result

    except Exception as e:
        logger.error(f"Error in smart search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during smart search")

@router.get("/scholarships/{scholarship_id}", response_model=Scholarship)
@general_rate_limit()  # QA FIX: Apply rate limiting to scholarship detail endpoint
async def get_scholarship(
    request: Request,  # QA FIX: Add request parameter for rate limiting
    scholarship_id: str,
    user_id: str | None = Query(None, description="User ID for analytics")
):
    """
    Get detailed information about a specific scholarship.

    Returns comprehensive scholarship details including eligibility criteria,
    application requirements, and deadlines.
    """
    try:
        scholarship = scholarship_service.get_scholarship_by_id(scholarship_id)

        if not scholarship:
            raise HTTPException(
                status_code=404,
                detail=f"Scholarship with ID {scholarship_id} not found"
            )

        # Log scholarship view (existing analytics)
        analytics_service.log_scholarship_view(user_id, scholarship_id)
        
        # Emit business event for KPI tracking (NEW: CEO directive)
        session_id = extract_session_id(request)
        actor_id = extract_actor_id(request) or user_id
        
        from models.business_events import create_scholarship_viewed_event
        event = create_scholarship_viewed_event(
            scholarship_id=scholarship_id,
            source="detail",
            match_score=None,
            actor_id=actor_id,
            session_id=session_id
        )
        await event_emitter.emit(event)

        return scholarship

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scholarship {scholarship_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


from pydantic import BaseModel, Field
from typing import Optional as OptionalType


class SaveScholarshipRequest(BaseModel):
    """Request to save a scholarship for later"""
    match_score: OptionalType[float] = Field(None, description="Match quality score (0-1)")
    eligibility_score: OptionalType[float] = Field(None, description="Eligibility score (0-1)")


class SaveScholarshipResponse(BaseModel):
    """Response after saving a scholarship"""
    scholarship_id: str
    saved: bool = True
    message: str = "Scholarship saved successfully"


@router.post("/scholarships/{scholarship_id}/save", response_model=SaveScholarshipResponse)
@general_rate_limit()
async def save_scholarship(
    request: Request,
    scholarship_id: str,
    data: SaveScholarshipRequest,
    current_user: User = Depends(require_auth())
):
    """
    Save a scholarship to user's saved list.
    
    Emits scholarship_saved business event for scholarship_view_to_save KPI tracking.
    Required for view→save→apply conversion funnel.
    """
    try:
        session_id = extract_session_id(request)
        actor_id = extract_actor_id(request) or current_user.user_id if current_user else None
        
        scholarship = scholarship_service.get_scholarship_by_id(scholarship_id)
        if not scholarship:
            raise HTTPException(
                status_code=404,
                detail=f"Scholarship with ID {scholarship_id} not found"
            )
        
        event = create_scholarship_saved_event(
            scholarship_id=scholarship_id,
            match_score=data.match_score,
            eligibility_score=data.eligibility_score,
            actor_id=actor_id,
            session_id=session_id
        )
        
        await event_emitter.emit(event)
        
        logger.info(f"Scholarship saved: {scholarship_id} by user {actor_id}")
        
        return SaveScholarshipResponse(
            scholarship_id=scholarship_id,
            saved=True,
            message=f"Saved {scholarship.name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving scholarship {scholarship_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save scholarship")


@router.post("/scholarships/eligibility-check", response_model=EligibilityResult)
async def check_eligibility(eligibility_request: EligibilityCheck):
    """
    Check if a user profile meets the eligibility criteria for a specific scholarship.

    This endpoint evaluates user information against scholarship requirements
    and provides detailed feedback on eligibility status.
    """
    try:
        result = eligibility_service.check_eligibility(
            eligibility_request.user_profile,
            eligibility_request.scholarship_id
        )

        # Log eligibility check
        analytics_service.log_eligibility_check(
            user_id=eligibility_request.user_profile.id,
            scholarship_id=eligibility_request.scholarship_id,
            eligible=result.eligible,
            match_score=result.match_score
        )

        return result

    except Exception as e:
        logger.error(f"Error checking eligibility: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing eligibility check")

@router.post("/scholarships/bulk-eligibility-check", response_model=list[EligibilityResult])
async def bulk_eligibility_check(
    user_profile: UserProfile,
    scholarship_ids: list[str]
):
    """
    Check eligibility for multiple scholarships at once.

    This endpoint allows users to check their eligibility for multiple
    scholarships in a single request, improving efficiency.
    """
    try:
        if len(scholarship_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum of 50 scholarships can be checked at once"
            )

        results = eligibility_service.check_multiple_eligibilities(
            user_profile, scholarship_ids
        )

        # Log bulk eligibility check
        for result in results:
            analytics_service.log_eligibility_check(
                user_id=user_profile.id,
                scholarship_id=result.scholarship_id,
                eligible=result.eligible,
                match_score=result.match_score
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk eligibility check: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing bulk eligibility check")

@router.post("/scholarships/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Get personalized scholarship recommendations based on user profile.

    This endpoint uses the user's profile information to generate
    tailored scholarship recommendations with eligibility scoring.
    """
    try:
        recommendations = search_service.get_recommendations(request)

        # Log recommendation request
        analytics_service.log_recommendation_request(
            user_id=request.user_profile.id,
            recommendation_count=len(recommendations)
        )

        return {
            "user_profile_summary": {
                "field_of_study": request.user_profile.field_of_study,
                "gpa": request.user_profile.gpa,
                "grade_level": request.user_profile.grade_level,
                "citizenship": request.user_profile.citizenship,
                "state_of_residence": request.user_profile.state_of_residence
            },
            "recommendations": recommendations,
            "recommendation_metadata": {
                "total_recommendations": len(recommendations),
                "request_limit": request.limit,
                "include_ineligible": request.include_ineligible
            }
        }

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating recommendations")

@router.get("/scholarships/organization/{organization}")
async def get_scholarships_by_organization(
    organization: str,
    user_id: str | None = Query(None, description="User ID for analytics")
):
    """
    Get all scholarships offered by a specific organization.

    This endpoint returns scholarships filtered by the sponsoring organization.
    """
    try:
        scholarships = scholarship_service.get_scholarships_by_organization(organization)

        if not scholarships:
            raise HTTPException(
                status_code=404,
                detail=f"No scholarships found for organization: {organization}"
            )

        # Convert to summary format
        scholarship_summaries = [
            ScholarshipSummary(
                id=sch.id,
                name=sch.name,
                organization=sch.organization,
                amount=sch.amount,
                application_deadline=sch.application_deadline,
                scholarship_type=sch.scholarship_type,
                description=sch.description[:197] + "..." if len(sch.description) > 200 else sch.description,
                eligibility_criteria=sch.eligibility_criteria
            )
            for sch in scholarships
        ]

        return {
            "organization": organization,
            "scholarship_count": len(scholarship_summaries),
            "scholarships": scholarship_summaries
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scholarships for organization {organization}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scholarships/fields/{field_of_study}")
async def get_scholarships_by_field(
    field_of_study: FieldOfStudy,
    limit: int = Query(20, ge=1, le=100),
    user_id: str | None = Query(None, description="User ID for analytics")
):
    """
    Get scholarships available for a specific field of study.
    """
    try:
        filters = SearchFilters(
            keyword=None,
            fields_of_study=[field_of_study],
            min_amount=None,
            max_amount=None,
            scholarship_types=[],
            states=[],
            min_gpa=None,
            citizenship=None,
            deadline_after=None,
            deadline_before=None,
            limit=limit,
            offset=0
        )

        result = scholarship_service.search_scholarships(filters)

        return {
            "field_of_study": field_of_study,
            "results": result
        }

    except Exception as e:
        logger.error(f"Error retrieving scholarships for field {field_of_study}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
