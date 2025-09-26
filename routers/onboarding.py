# AI Scholarship Playbook - Magic Onboarding Router
# Conversational AI-powered profile intake endpoints

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from middleware.auth import User, require_auth
from middleware.rate_limiting import search_rate_limit as general_rate_limit
from models.onboarding import (
    OnboardingContinueRequest,
    OnboardingResponse,
    OnboardingStartRequest,
    ProfileCompletionStatus,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from services.magic_onboarding_service import MagicOnboardingService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/onboarding", tags=["Magic Onboarding"])

# Initialize service (will be properly injected in production)
openai_service = OpenAIService()
onboarding_service = MagicOnboardingService(openai_service)

@router.post("/start", response_model=OnboardingResponse)
@general_rate_limit()
async def start_magic_onboarding(
    request: OnboardingStartRequest,
    current_user: User = Depends(require_auth())
):
    """
    Start Magic Onboarding - AI-powered conversational profile intake.

    This endpoint initiates a personalized conversation to help students
    build their scholarship profile through natural conversation rather
    than traditional forms.
    """
    try:
        if not openai_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable. Please try again later."
            )

        response = await onboarding_service.start_onboarding(
            user_id=current_user.user_id,
            request=request
        )

        logger.info(f"Started magic onboarding for user {current_user.user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to start magic onboarding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start onboarding process"
        )

@router.post("/continue", response_model=OnboardingResponse)
@general_rate_limit()
async def continue_magic_onboarding(
    request: OnboardingContinueRequest,
    current_user: User = Depends(require_auth())
):
    """
    Continue Magic Onboarding conversation.

    Processes user responses and continues the AI-guided conversation
    to build a comprehensive scholarship profile.
    """
    try:
        if not openai_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service unavailable. Please try again later."
            )

        response = await onboarding_service.continue_onboarding(request)

        logger.info(f"Continued onboarding session {request.session_id}")
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to continue onboarding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to continue onboarding conversation"
        )

@router.get("/profile/completion", response_model=ProfileCompletionStatus)
@general_rate_limit()
async def get_profile_completion(
    request: Request,
    current_user: User = Depends(require_auth())
):
    """
    Get current profile completion status.

    Returns detailed completion percentages across different profile
    categories and suggestions for improvement.
    """
    try:
        # This would integrate with user profile service
        # For now, return a mock response indicating MVP status
        return ProfileCompletionStatus(
            overall_completion=0.0,
            basic_info_completion=0.0,
            academic_completion=0.0,
            interests_completion=0.0,
            financial_completion=0.0,
            activities_completion=0.0,
            documents_completion=0.0,
            missing_critical_fields=["All fields - complete Magic Onboarding first"],
            suggested_improvements=["Start Magic Onboarding to build your profile"],
            estimated_time_to_complete=15
        )

    except Exception as e:
        logger.error(f"Failed to get profile completion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve profile completion status"
        )

@router.put("/profile/update", response_model=ProfileUpdateResponse)
@general_rate_limit()
async def update_profile_from_onboarding(
    request: Request,
    request_data: ProfileUpdateRequest,
    current_user: User = Depends(require_auth())
):
    """
    Update user profile with data from Magic Onboarding.

    Applies extracted profile data from the onboarding conversation
    to the user's main profile for scholarship matching.
    """
    try:
        # This would integrate with user profile service
        # For MVP, return success response
        return ProfileUpdateResponse(
            updated_fields=list(request_data.field_updates.keys()),
            new_completion_percentage=0.8,
            improved_match_count=25,
            new_recommendations=[
                "Complete your document uploads",
                "Review your scholarship matches",
                "Set up deadline reminders"
            ],
            next_suggested_action="Upload your transcript for better matching"
        )

    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile from onboarding data"
        )

@router.get("/session/{session_id}")
@general_rate_limit()
async def get_onboarding_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(require_auth())
):
    """
    Retrieve details of a specific onboarding session.

    Allows users to review their onboarding conversation history
    and extracted profile data.
    """
    try:
        session = onboarding_service.active_sessions.get(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Onboarding session not found"
            )

        # Verify session belongs to current user
        if session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this onboarding session"
            )

        return {
            "session_id": session.session_id,
            "current_stage": session.current_stage,
            "completion_percentage": session.completion_percentage,
            "is_completed": session.is_completed,
            "started_at": session.started_at,
            "last_activity": session.last_activity,
            "profile_completion_status": session.profile_completion_status,
            "conversation_length": len(session.conversation_context.conversation_history)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve onboarding session"
        )
