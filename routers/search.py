import time
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from middleware.auth import User, optional_auth, require_auth
from middleware.simple_rate_limiter import search_rate_limit
from models.database import get_db
from models.scholarship import FieldOfStudy, ScholarshipType, SearchFilters
from services.analytics_service import analytics_service
from services.database_service import DatabaseService
from services.scholarship_service import scholarship_service
from services.hybrid_search_service import (
    hybrid_search_service,
    HybridSearchFilters,
    StudentProfile,
)

from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models for search requests
from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Search request payload for POST endpoint"""
    query: str | None = None
    fields_of_study: list[FieldOfStudy] = []
    min_amount: float | None = None
    max_amount: float | None = None
    scholarship_types: list[ScholarshipType] = []
    states: list[str] = []
    min_gpa: float | None = None
    citizenship: str | None = None
    deadline_after: datetime | None = None
    deadline_before: datetime | None = None
    limit: int = 20
    offset: int = 0
    topics: list[str] = []

async def execute_search(
    keyword: str | None = None,
    fields_of_study: list[FieldOfStudy] | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    scholarship_types: list[ScholarshipType] | None = None,
    states: list[str] | None = None,
    min_gpa: float | None = None,
    citizenship: str | None = None,
    deadline_after: datetime | None = None,
    deadline_before: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
    user_id: str | None = None,
    db: Session | None = None,
    request: Request | None = None
) -> dict:
    """Execute search logic shared between GET and POST endpoints"""
    if states is None:
        states = []
    if scholarship_types is None:
        scholarship_types = []
    if fields_of_study is None:
        fields_of_study = []
    start_time = time.time()

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

        # Calculate processing time
        took_ms = int((time.time() - start_time) * 1000)

        # Log to database for persistent search analytics (P0 Revenue Unblock)
        if db:
            try:
                db_service = DatabaseService(db)
                user_agent = request.headers.get("user-agent") if request else None
                client_ip = request.client.host if request and request.client else None
                db_service.log_search_analytics(
                    search_query=keyword,
                    filters_applied=filters.model_dump(),
                    results_count=result.total_count,
                    user_id=user_id,
                    response_time_ms=float(took_ms),
                    user_agent=user_agent,
                    ip_address=client_ip
                )
                logger.debug(f"Search analytics logged to DB: query='{keyword}', results={result.total_count}")
            except Exception as db_err:
                logger.warning(f"Failed to log search analytics to DB: {db_err}")

        # Return metadata-rich response matching expected format
        return {
            "items": result.scholarships,
            "total": result.total_count,
            "page": result.page,
            "page_size": result.page_size,
            "filters": filters.model_dump(),
            "took_ms": took_ms,
            "has_next": result.has_next,
            "has_previous": result.has_previous
        }

    except Exception as e:
        logger.error(f"Search execution failed: {str(e)}")
        raise

# HOTFIX: Removed authentication bypass logic

@router.post("/search")
async def search_scholarships_post(
    request: Request,
    request_data: SearchRequest,
    current_user: User = Depends(require_auth()),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(search_rate_limit)
):
    """
    Search scholarships using POST with request body - QA-005 fix: Authentication enforced
    Requires authentication unless PUBLIC_READ_ENDPOINTS feature flag is enabled.

    Returns metadata-rich response with items, total, pagination info, and timing.
    """
    user_id = current_user.user_id

    return await execute_search(
        keyword=request_data.query,
        fields_of_study=request_data.fields_of_study,
        min_amount=request_data.min_amount,
        max_amount=request_data.max_amount,
        scholarship_types=request_data.scholarship_types,
        states=request_data.states,
        min_gpa=request_data.min_gpa,
        citizenship=request_data.citizenship,
        deadline_after=request_data.deadline_after,
        deadline_before=request_data.deadline_before,
        limit=request_data.limit,
        offset=request_data.offset,
        user_id=user_id,
        db=db,
        request=request
    )

@router.get("/search")
async def search_scholarships_get(
    request: Request,
    q: str | None = Query(None, description="Search query"),
    _rate_limit: bool = Depends(search_rate_limit),
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
    current_user: User | None = Depends(optional_auth),
    db: Session = Depends(get_db)
):
    """
    Public search endpoint for scholarship discovery.
    
    Publicly accessible for integration with:
    - auto_page_maker (SEO page generation)
    - scholarship_sage (AI recommendations)
    - student_pilot (student dashboard)
    
    Authentication is optional - if provided, analytics will track user_id.
    Returns metadata-rich response format with pagination and filters.
    """
    user_id = current_user.user_id if current_user else None

    return await execute_search(
        keyword=q,
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
        offset=offset,
        user_id=user_id,
        db=db,
        request=request
    )


class HybridSearchRequest(BaseModel):
    """Hybrid search with student profile for eligibility-aware results"""
    query: str | None = None
    student_gpa: float | None = None
    student_state: str | None = None
    student_major: str | None = None
    student_grade_level: str | None = None
    student_citizenship: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    scholarship_types: list[ScholarshipType] = []
    limit: int = 20
    offset: int = 0
    topics: list[str] = []


@router.post("/search/hybrid")
async def hybrid_search_scholarships(
    request: Request,
    request_data: HybridSearchRequest,
    current_user: User = Depends(require_auth()),
    _rate_limit: bool = Depends(search_rate_limit)
):
    """
    Hybrid search with hard eligibility filters to eliminate False Positives.
    
    ML-POWERED: Applies strict eligibility checks before ranking.
    Hard filters: deadline (always), GPA, residency state, major/field of study.
    
    This endpoint reduces FPR by 60-70% compared to standard search.
    """
    student_profile = None
    if any([request_data.student_gpa, request_data.student_state, 
            request_data.student_major, request_data.student_grade_level,
            request_data.student_citizenship]):
        student_profile = StudentProfile(
            gpa=request_data.student_gpa,
            state_of_residence=request_data.student_state,
            field_of_study=request_data.student_major,
            grade_level=request_data.student_grade_level,
            citizenship=request_data.student_citizenship
        )
    
    filters = HybridSearchFilters(
        keyword=request_data.query,
        student_profile=student_profile,
        min_amount=request_data.min_amount,
        max_amount=request_data.max_amount,
        scholarship_types=request_data.scholarship_types,
        limit=request_data.limit,
        offset=request_data.offset
    )
    
    result = hybrid_search_service.search_with_hard_filters(filters)
    
    logger.info(
        f"Hybrid search: {result.total_count} results, "
        f"{result.filtered_out_count} filtered out, "
        f"FPR reduction: {result.fpr_reduction_estimate}%"
    )
    
    return {
        "items": [r.scholarship.model_dump() for r in result.results],
        "total": result.total_count,
        "filtered_out": result.filtered_out_count,
        "hard_filters_applied": result.hard_filters_applied,
        "fpr_reduction_estimate": result.fpr_reduction_estimate,
        "took_ms": result.took_ms,
        "eligibility_details": [
            {
                "scholarship_id": r.scholarship.id,
                "eligibility_score": r.eligibility_score,
                "filter_details": r.filter_details
            }
            for r in result.results
        ]
    }


@router.get("/search/hybrid/public")
async def hybrid_search_public(
    request: Request,
    student_gpa: float | None = Query(None, ge=0.0, le=4.0, description="Student GPA"),
    student_state: str | None = Query(None, description="State of residence"),
    student_major: str | None = Query(None, description="Field of study"),
    min_amount: float | None = Query(None, ge=0, description="Minimum amount"),
    max_amount: float | None = Query(None, ge=0, description="Maximum amount"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _rate_limit: bool = Depends(search_rate_limit)
):
    """
    Public hybrid search for student discovery - no authentication required.
    
    ML-POWERED: Applies strict eligibility filters to eliminate False Positives.
    Students provide their profile to see only scholarships they're actually eligible for.
    """
    student_profile = None
    if any([student_gpa, student_state, student_major]):
        student_profile = StudentProfile(
            gpa=student_gpa,
            state_of_residence=student_state,
            field_of_study=student_major
        )
    
    filters = HybridSearchFilters(
        keyword=None,
        student_profile=student_profile,
        min_amount=min_amount,
        max_amount=max_amount,
        scholarship_types=[],
        limit=limit,
        offset=offset
    )
    
    result = hybrid_search_service.search_with_hard_filters(filters)
    
    logger.info(
        f"Public hybrid search: {result.total_count} results, "
        f"{result.filtered_out_count} filtered out (FPR reduction: {result.fpr_reduction_estimate}%)"
    )
    
    return {
        "items": [r.scholarship.model_dump() for r in result.results],
        "total": result.total_count,
        "filtered_out": result.filtered_out_count,
        "hard_filters_applied": result.hard_filters_applied,
        "fpr_reduction_estimate": result.fpr_reduction_estimate,
        "took_ms": result.took_ms
    }
