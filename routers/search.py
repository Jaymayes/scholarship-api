from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
from datetime import datetime
import time

from models.scholarship import SearchFilters, SearchResponse, FieldOfStudy, ScholarshipType
from models.user import UserProfile
from services.scholarship_service import scholarship_service
from services.analytics_service import analytics_service
from middleware.auth import get_current_user
from config.settings import settings
from middleware.simple_rate_limiter import search_rate_limit
# from routers.interaction_wrapper import log_interaction  # Will implement if needed
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models for search requests
from pydantic import BaseModel

class SearchRequest(BaseModel):
    """Search request payload for POST endpoint"""
    query: Optional[str] = None
    fields_of_study: List[FieldOfStudy] = []
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    scholarship_types: List[ScholarshipType] = []
    states: List[str] = []
    min_gpa: Optional[float] = None
    citizenship: Optional[str] = None
    deadline_after: Optional[datetime] = None
    deadline_before: Optional[datetime] = None
    limit: int = 20
    offset: int = 0

async def execute_search(
    keyword: Optional[str] = None,
    fields_of_study: List[FieldOfStudy] = [],
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    scholarship_types: List[ScholarshipType] = [],
    states: List[str] = [],
    min_gpa: Optional[float] = None,
    citizenship: Optional[str] = None,
    deadline_after: Optional[datetime] = None,
    deadline_before: Optional[datetime] = None,
    limit: int = 20,
    offset: int = 0,
    user_id: Optional[str] = None
) -> dict:
    """Execute search logic shared between GET and POST endpoints"""
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
            filters=filters.dict()
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
            "filters": filters.dict(),
            "took_ms": took_ms,
            "has_next": result.has_next,
            "has_previous": result.has_previous
        }
        
    except Exception as e:
        logger.error(f"Search execution failed: {str(e)}")
        raise

# QA-005 fix: Add authentication requirement to search endpoints
async def get_auth_user_for_search() -> Optional[dict]:
    """Get authenticated user for search endpoints with feature flag support"""
    if settings.public_read_endpoints:
        # In development or when explicitly enabled, allow unauthenticated access
        return None
    # In production, require authentication
    return Depends(get_current_user)

@router.post("/search")
async def search_scholarships_post(
    request: Request,
    request_data: SearchRequest,
    current_user: Optional[dict] = Depends(get_current_user) if not settings.public_read_endpoints else None,
    _rate_limit: bool = Depends(search_rate_limit)
):
    """
    Search scholarships using POST with request body - QA-005 fix: Authentication enforced
    Requires authentication unless PUBLIC_READ_ENDPOINTS feature flag is enabled.
    
    Returns metadata-rich response with items, total, pagination info, and timing.
    """
    # QA-005 fix: Enforce authentication in production
    if not settings.public_read_endpoints and not current_user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail={
                "trace_id": getattr(request.state, 'trace_id', None),
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication required for search endpoints",
                "status": 401,
                "timestamp": int(time.time())
            }
        )
    user_id = current_user.get("user_id") if current_user else None
    
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
    q: Optional[str] = Query(None, description="Search query"),
    _rate_limit: bool = Depends(search_rate_limit),
    fields_of_study: List[FieldOfStudy] = Query(default=[], description="Filter by fields of study"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum scholarship amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum scholarship amount"),
    scholarship_types: List[ScholarshipType] = Query(default=[], description="Filter by scholarship types"),
    states: List[str] = Query(default=[], description="Filter by US states"),
    min_gpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Minimum GPA filter"),
    citizenship: Optional[str] = Query(None, description="Citizenship requirement"),
    deadline_after: Optional[datetime] = Query(None, description="Deadlines after this date"),
    deadline_before: Optional[datetime] = Query(None, description="Deadlines before this date"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Optional[dict] = Depends(get_current_user) if not settings.public_read_endpoints else None
):
    """
    Search scholarships using GET with query parameters - QA-005 fix: Authentication enforced
    Requires authentication unless PUBLIC_READ_ENDPOINTS feature flag is enabled.
    
    Returns the same metadata-rich response format as POST endpoint.
    """
    # QA-005 fix: Enforce authentication in production
    if not settings.public_read_endpoints and not current_user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail={
                "trace_id": getattr(request.state, 'trace_id', None),
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication required for search endpoints",
                "status": 401,
                "timestamp": int(time.time())
            }
        )
    
    user_id = current_user.get("user_id") if current_user else None
    
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