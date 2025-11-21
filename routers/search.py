import time
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request

from middleware.auth import User, optional_auth, require_auth
from middleware.simple_rate_limiter import search_rate_limit
from models.scholarship import FieldOfStudy, ScholarshipType, SearchFilters
from services.analytics_service import analytics_service
from services.scholarship_service import scholarship_service

# from routers.interaction_wrapper import log_interaction  # Will implement if needed
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
    user_id: str | None = None
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
    current_user: User = Depends(require_auth()),  # HOTFIX: Always require authentication
    _rate_limit: bool = Depends(search_rate_limit)
):
    """
    Search scholarships using POST with request body - QA-005 fix: Authentication enforced
    Requires authentication unless PUBLIC_READ_ENDPOINTS feature flag is enabled.

    Returns metadata-rich response with items, total, pagination info, and timing.
    """
    # Authentication enforced by dependency injection - no additional check needed
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
        user_id=user_id
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
    current_user: User | None = Depends(optional_auth)  # PUBLIC ACCESS for auto_page_maker, scholarship_sage, student_pilot
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
        user_id=user_id
    )
