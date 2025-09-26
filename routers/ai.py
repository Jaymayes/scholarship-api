"""
AI-powered endpoints for the Scholarship API
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.analytics_service import analytics_service
from services.openai_service import openai_service
from services.scholarship_service import scholarship_service

# Rate limiting will be handled at the application level
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ai", tags=["AI-Powered Features"])

class SearchEnhancementRequest(BaseModel):
    """Request to enhance a search query using AI"""
    query: str = Field(..., description="Original search query")
    user_context: dict[str, Any] | None = Field(None, description="User context for better enhancement")

class SearchEnhancementResponse(BaseModel):
    """Enhanced search query response"""
    original_query: str
    enhanced_query: str
    suggested_filters: dict[str, Any]
    search_intent: str
    confidence: float

class EligibilityAnalysisRequest(BaseModel):
    """Request for AI eligibility analysis"""
    scholarship_id: str = Field(..., description="Scholarship ID to analyze")
    user_profile: dict[str, Any] = Field(..., description="User profile for analysis")

class EligibilityAnalysisResponse(BaseModel):
    """AI eligibility analysis response"""
    scholarship_name: str
    match_score: float
    analysis: str
    recommendations: list[str]
    missing_requirements: list[str] | None = None
    strengths: list[str] | None = None

@router.post("/enhance-search", response_model=SearchEnhancementResponse)
async def enhance_search_query(request: SearchEnhancementRequest):
    """
    Enhance a search query using AI to improve search results.

    This endpoint uses AI to:
    - Improve search terms for better matching
    - Suggest relevant filters
    - Identify search intent
    - Provide confidence score
    """
    if not openai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please check OpenAI API configuration."
        )

    try:
        # Log analytics
        analytics_service.log_search(
            user_id=None,
            query=request.query,
            result_count=0,
            filters={"ai_enhanced": True}
        )

        result = openai_service.enhance_search_query(
            query=request.query,
            user_context=request.user_context
        )

        return SearchEnhancementResponse(
            original_query=request.query,
            enhanced_query=result.get("enhanced_query", request.query),
            suggested_filters=result.get("suggested_filters", {}),
            search_intent=result.get("search_intent", "Unknown"),
            confidence=result.get("confidence", 0.5)
        )

    except Exception as e:
        logger.error(f"Error enhancing search query: {e}")
        raise HTTPException(status_code=500, detail="Failed to enhance search query")

@router.get("/search-suggestions")
async def get_search_suggestions(
    partial_query: str = Query(..., description="Partial search query"),
    limit: int = Query(5, ge=1, le=10, description="Number of suggestions to return")
):
    """
    Get AI-powered search suggestions based on partial query.

    Returns intelligent suggestions to help users find relevant scholarships.
    """
    if not openai_service.is_available():
        # Fallback suggestions without AI
        fallback_suggestions = [
            f"{partial_query} scholarship",
            f"{partial_query} grant",
            f"{partial_query} funding",
            f"{partial_query} award",
            f"{partial_query} education"
        ]
        return {"suggestions": fallback_suggestions[:limit]}

    try:
        suggestions = openai_service.generate_search_suggestions(
            partial_query=partial_query
        )

        return {"suggestions": suggestions[:limit]}

    except Exception as e:
        logger.error(f"Error generating search suggestions: {e}")
        # Return basic fallback
        return {"suggestions": [f"{partial_query} scholarship"]}

@router.post("/analyze-eligibility", response_model=EligibilityAnalysisResponse)
async def analyze_eligibility_match(request: EligibilityAnalysisRequest):
    """
    Analyze how well a user profile matches scholarship eligibility using AI.

    Provides detailed analysis and recommendations for scholarship applications.
    """
    if not openai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please check OpenAI API configuration."
        )

    try:
        # Get scholarship data
        scholarship = scholarship_service.get_scholarship_by_id(request.scholarship_id)
        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")

        # Convert scholarship to dict for AI analysis
        scholarship_dict = scholarship.model_dump() if hasattr(scholarship, 'model_dump') else scholarship.__dict__

        # Perform AI analysis
        analysis = openai_service.analyze_eligibility_match(
            user_profile=request.user_profile,
            scholarship=scholarship_dict
        )

        return EligibilityAnalysisResponse(
            scholarship_name=scholarship_dict.get("name", "Unknown"),
            match_score=analysis.get("match_score", 0.5),
            analysis=analysis.get("analysis", "Analysis unavailable"),
            recommendations=analysis.get("recommendations", []),
            missing_requirements=analysis.get("missing_requirements"),
            strengths=analysis.get("strengths")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing eligibility match: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze eligibility match")

@router.get("/scholarship-summary/{scholarship_id}")
async def get_ai_scholarship_summary(scholarship_id: str):
    """
    Generate an AI-powered summary of a scholarship.

    Creates a concise, student-friendly summary highlighting key information.
    """
    try:
        # Get scholarship data
        scholarship = scholarship_service.get_scholarship_by_id(scholarship_id)
        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")

        # Convert to dict for AI processing
        scholarship_dict = scholarship.model_dump() if hasattr(scholarship, 'model_dump') else scholarship.__dict__

        if openai_service.is_available():
            summary = openai_service.generate_scholarship_summary(scholarship_dict)
        else:
            # Fallback to truncated description
            summary = scholarship_dict.get("description", "No description available")[:200] + "..."

        return {
            "scholarship_id": scholarship_id,
            "name": scholarship_dict.get("name"),
            "ai_summary": summary,
            "ai_generated": openai_service.is_available()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating scholarship summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

@router.get("/trends-analysis")
async def get_scholarship_trends():
    """
    Get AI-powered analysis of scholarship trends and insights.

    Analyzes current scholarship offerings to identify patterns and provide insights.
    """
    if not openai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please check OpenAI API configuration."
        )

    try:
        # Get current scholarships for analysis
        from models.scholarship import SearchFilters
        filters = SearchFilters(limit=50, offset=0)
        search_result = scholarship_service.search_scholarships(filters)

        scholarships = search_result.scholarships if hasattr(search_result, 'scholarships') else []

        # Convert to dicts for AI analysis
        scholarship_dicts = []
        for scholarship in scholarships:
            if hasattr(scholarship, 'model_dump'):
                scholarship_dicts.append(scholarship.model_dump())
            else:
                scholarship_dicts.append(scholarship.__dict__)

        # Perform AI analysis
        trends = openai_service.analyze_scholarship_trends(scholarship_dicts)

        return {
            "analysis_date": "2025-08-17",
            "scholarships_analyzed": len(scholarship_dicts),
            "trends": trends,
            "ai_generated": True
        }

    except Exception as e:
        logger.error(f"Error analyzing scholarship trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze scholarship trends")

@router.get("/status")
async def get_ai_service_status():
    """
    Check the status of AI-powered features.

    Returns information about AI service availability and capabilities.
    """
    return {
        "ai_service_available": openai_service.is_available(),
        "features": {
            "search_enhancement": openai_service.is_available(),
            "eligibility_analysis": openai_service.is_available(),
            "scholarship_summaries": openai_service.is_available(),
            "search_suggestions": openai_service.is_available(),
            "trends_analysis": openai_service.is_available()
        },
        "model": "gpt-4o" if openai_service.is_available() else None,
        "rate_limits": {
            "search_enhancement": "20/minute",
            "search_suggestions": "30/minute",
            "eligibility_analysis": "10/minute",
            "scholarship_summary": "15/minute",
            "trends_analysis": "5/minute"
        }
    }
