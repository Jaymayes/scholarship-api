# Predictive Matching API Router
# "Likelihood to win" scoring and intelligent ranking

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from middleware.auth import User, require_auth
from middleware.rate_limiting import search_rate_limit as rate_limit
from models.predictive_matching import (
    PredictiveMatchingResponse,
    PredictiveMatchResult,
    RankedScholarshipRecommendation,
)
from models.scholarship import Scholarship
from models.user import UserProfile
from services.eligibility_service import EligibilityService
from services.openai_service import OpenAIService
from services.predictive_matching_service import PredictiveMatchingService
from services.scholarship_service import scholarship_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/matching", tags=["Predictive Matching"])

# Initialize services
openai_service = OpenAIService()
eligibility_service = EligibilityService()
predictive_service = PredictiveMatchingService(openai_service, eligibility_service)


class PredictiveMatchRequest(BaseModel):
    """Request for predictive matching"""
    user_profile: UserProfile
    scholarship_ids: List[str] | None = None
    analysis_depth: str = "standard"  # "quick", "standard", "deep"
    max_results: int = 20


@router.post("/predict", response_model=PredictiveMatchingResponse)
@rate_limit()
async def predict_scholarship_matches(
    request: Request,
    match_request: PredictiveMatchRequest,
    current_user: User = Depends(require_auth())
) -> PredictiveMatchingResponse:
    """
    Generate predictive scholarship matches with "likelihood to win" scoring
    
    **Key Features:**
    - **Likelihood to Win**: 0-100% probability score based on profile strength
    - **Quick Wins**: Scholarships with high win probability and low effort
    - **Stretch Opportunities**: Competitive but worth applying
    - **Safety Options**: High probability fallbacks
    
    **Analysis Depth:**
    - `quick`: Basic scoring (fastest, ~2s)
    - `standard`: Full analysis with AI insights (recommended, ~5s) 
    - `deep`: Comprehensive with historical data (~10s)
    
    **Returns:**
    - High priority matches (75%+ likelihood)
    - Medium priority matches (50-75% likelihood)
    - Stretch opportunities (competitive)
    - Overall competitiveness score
    - Profile improvement recommendations
    - Estimated application time per scholarship
    
    **Usage:** Helps students focus on scholarships they're most likely to win
    **Credit Cost:** 3.0 credits per matching request
    """
    try:
        # Get scholarships
        if match_request.scholarship_ids:
            scholarships = []
            for s_id in match_request.scholarship_ids:
                scholarship = scholarship_service.get_scholarship_by_id(s_id)
                if scholarship:
                    scholarships.append(scholarship)
        else:
            # Use all active scholarships
            all_scholarships = scholarship_service.get_all_scholarships()
            scholarships = all_scholarships[:100]  # Limit to prevent timeouts
        
        if not scholarships:
            raise HTTPException(status_code=404, detail="No scholarships found")
        
        # Run predictive matching
        result = await predictive_service.predict_scholarship_matches(
            user_profile=match_request.user_profile,
            scholarships=scholarships,
            analysis_depth=match_request.analysis_depth
        )
        
        # Limit results
        result.high_priority_matches = result.high_priority_matches[:match_request.max_results]
        result.medium_priority_matches = result.medium_priority_matches[:match_request.max_results]
        
        logger.info(
            f"Predictive matching for user {current_user.user_id}: "
            f"{len(result.high_priority_matches)} high priority, "
            f"{len(result.medium_priority_matches)} medium priority"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Predictive matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Predictive matching failed: {str(e)}")


class QuickWinsRequest(BaseModel):
    """Request for quick win scholarships"""
    user_profile: UserProfile
    limit: int = 5


@router.post("/quick-wins", response_model=List[RankedScholarshipRecommendation])
@rate_limit()
async def get_quick_wins(
    request: Request,
    quick_wins_request: QuickWinsRequest,
    current_user: User = Depends(require_auth())
) -> List[RankedScholarshipRecommendation]:
    """
    Get "quick win" scholarships - high likelihood, low effort
    
    **Quick Win Criteria:**
    - Likelihood to win ≥ 70%
    - Estimated application time ≤ 2 hours
    - Deadline > 2 weeks away
    
    **Perfect for:** Students who want fast ROI on applications
    **Credit Cost:** 2.0 credits
    """
    try:
        # Get all scholarships
        all_scholarships = scholarship_service.get_all_scholarships()
        
        # Run quick analysis
        result = await predictive_service.predict_scholarship_matches(
            user_profile=quick_wins_request.user_profile,
            scholarships=all_scholarships[:50],
            analysis_depth="quick"
        )
        
        # Filter for quick wins
        quick_wins = [
            rec for rec in result.high_priority_matches + result.medium_priority_matches
            if rec.quick_win_indicator
        ]
        
        return quick_wins[:quick_wins_request.limit]
        
    except Exception as e:
        logger.error(f"Quick wins failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Quick wins analysis failed")


class StretchOpportunitiesRequest(BaseModel):
    """Request for stretch opportunity scholarships"""
    user_profile: UserProfile
    limit: int = 5


@router.post("/stretch-opportunities", response_model=List[RankedScholarshipRecommendation])
@rate_limit()
async def get_stretch_opportunities(
    request: Request,
    stretch_request: StretchOpportunitiesRequest,
    current_user: User = Depends(require_auth())
) -> List[RankedScholarshipRecommendation]:
    """
    Get "stretch opportunity" scholarships - competitive but worth trying
    
    **Stretch Criteria:**
    - Likelihood to win 30-60%
    - High award amount (>$5,000)
    - Profile shows some competitive elements
    
    **Perfect for:** Ambitious students willing to invest time in competitive apps
    **Credit Cost:** 2.0 credits
    """
    try:
        # Get all scholarships
        all_scholarships = scholarship_service.get_all_scholarships()
        
        # Run standard analysis
        result = await predictive_service.predict_scholarship_matches(
            user_profile=stretch_request.user_profile,
            scholarships=all_scholarships[:50],
            analysis_depth="standard"
        )
        
        # Return stretch opportunities
        return result.stretch_opportunities[:stretch_request.limit]
        
    except Exception as e:
        logger.error(f"Stretch opportunities failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Stretch opportunities analysis failed")


@router.post("/profile-strength", response_model=dict)
@rate_limit()
async def analyze_profile_strength(
    request: Request,
    user_profile: UserProfile,
    current_user: User = Depends(require_auth())
) -> dict:
    """
    Analyze overall profile competitiveness
    
    **Returns:**
    - Competitiveness score (0-100)
    - Strength summary
    - Top improvement recommendations
    - Comparison to successful applicants
    
    **Usage:** Understand profile strengths/weaknesses before applying
    **Credit Cost:** 2.5 credits
    """
    try:
        # Run quick analysis to get profile insights
        all_scholarships = scholarship_service.get_all_scholarships()
        
        result = await predictive_service.predict_scholarship_matches(
            user_profile=user_profile,
            scholarships=all_scholarships[:30],
            analysis_depth="standard"
        )
        
        return {
            "competitiveness_score": result.overall_competitiveness_score,
            "profile_strength_summary": result.profile_strength_summary,
            "top_improvements": result.top_improvement_recommendations,
            "expected_win_rate": f"{result.success_probability_range[0]}-{result.success_probability_range[1]}%",
            "recommended_application_count": result.recommended_application_count
        }
        
    except Exception as e:
        logger.error(f"Profile strength analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile strength analysis failed")
