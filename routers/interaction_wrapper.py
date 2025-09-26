"""
Interaction Logging Wrapper Functions with Input Validation - QA-003 fix
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from config.settings import settings
from middleware.auth import get_current_user
from models.database import get_db
from schemas.interaction import (
    BulkInteractionRequest,
    InteractionRequest,
    InteractionResponse,
)
from services.interaction_service import InteractionService
from utils.logger import get_logger

logger = get_logger("interaction_wrapper")
router = APIRouter(prefix="/interactions", tags=["interactions"])
security = HTTPBearer(auto_error=False)

async def log_scholarship_interaction(
    request: Request,
    response: Response,
    event_type: str,
    scholarship_id: str | None = None,
    user_id: str | None = None
):
    """Wrapper to log interactions without breaking the main request flow"""
    try:
        # Get database session
        db = next(get_db())

        try:
            # Create interaction service
            interaction_service = InteractionService(db)

            # Extract user ID from request if not provided
            if not user_id and hasattr(request.state, 'user'):
                user_id = getattr(request.state.user, 'user_id', None)

            # Log the interaction
            await interaction_service.log_interaction(
                event_type=event_type,
                request=request,
                response=response,
                user_id=user_id,
                scholarship_id=scholarship_id,
                trace_id=getattr(request.state, 'trace_id', None)
            )

        finally:
            db.close()

    except Exception as e:
        # Never let interaction logging break the main request
        logger.warning(f"Failed to log interaction {event_type}: {str(e)}")

def with_interaction_logging(event_type: str, scholarship_id_param: str | None = None):
    """Decorator to add interaction logging to endpoint functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Execute the original function
            response = await func(*args, **kwargs)

            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                # Extract scholarship_id if specified
                scholarship_id = None
                if scholarship_id_param and scholarship_id_param in kwargs:
                    scholarship_id = kwargs[scholarship_id_param]

                # Create mock response object for logging
                mock_response = type('MockResponse', (), {'status_code': 200})()

                # Log the interaction
                await log_scholarship_interaction(
                    request=request,
                    response=mock_response,
                    event_type=event_type,
                    scholarship_id=scholarship_id
                )

            return response

        return wrapper
    return decorator

# QA-003 fix: Add properly validated endpoints with authentication
@router.post("/log", response_model=InteractionResponse)
async def log_interaction_endpoint(
    interaction: InteractionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) if not settings.public_read_endpoints else None
):
    """
    Log a single interaction event with strict input validation
    Requires authentication unless PUBLIC_READ_ENDPOINTS is enabled
    """
    try:
        interaction_service = InteractionService(db)

        # Create mock response for logging
        mock_response = type('MockResponse', (), {'status_code': 200})()

        # Log the interaction with validated data
        await interaction_service.log_interaction(
            event_type=interaction.event_type.value,
            request=request,
            response=mock_response,
            user_id=interaction.user_id or (current_user.get("user_id") if current_user else None),
            scholarship_id=interaction.scholarship_id,
            trace_id=getattr(request.state, 'trace_id', None),
            metadata={
                "search_query": interaction.search_query,
                "filters": interaction.filters,
                "custom_metadata": interaction.metadata
            }
        )

        return InteractionResponse(
            success=True,
            interaction_id=getattr(request.state, 'trace_id', None),
            message="Interaction logged successfully"
        )

    except Exception as e:
        logger.error(f"Failed to log interaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log interaction"  # Use simple string to avoid double encoding
        )

@router.post("/bulk-log", response_model=dict)
async def bulk_log_interactions_endpoint(
    bulk_request: BulkInteractionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) if not settings.public_read_endpoints else None
):
    """
    Log multiple interaction events with strict input validation
    Requires authentication unless PUBLIC_READ_ENDPOINTS is enabled
    """
    try:
        interaction_service = InteractionService(db)
        logged_count = 0
        errors = []

        for interaction in bulk_request.interactions:
            try:
                # Create mock response for logging
                mock_response = type('MockResponse', (), {'status_code': 200})()

                # Log each interaction with validated data
                await interaction_service.log_interaction(
                    event_type=interaction.event_type.value,
                    request=request,
                    response=mock_response,
                    user_id=interaction.user_id or (current_user.get("user_id") if current_user else None),
                    scholarship_id=interaction.scholarship_id,
                    trace_id=getattr(request.state, 'trace_id', None),
                    metadata={
                        "search_query": interaction.search_query,
                        "filters": interaction.filters,
                        "custom_metadata": interaction.metadata
                    }
                )
                logged_count += 1

            except Exception as e:
                errors.append(f"Failed to log interaction {logged_count + 1}: {str(e)}")
                logger.warning(f"Failed to log bulk interaction: {str(e)}")

        return {
            "success": logged_count > 0,
            "logged_count": logged_count,
            "total_requested": len(bulk_request.interactions),
            "errors": errors[:10],  # Limit error reporting
            "message": f"Successfully logged {logged_count}/{len(bulk_request.interactions)} interactions"
        }

    except Exception as e:
        logger.error(f"Failed to process bulk interaction logging: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trace_id": getattr(request.state, 'trace_id', None),
                "code": "BULK_INTERACTION_LOG_FAILED",
                "message": "Failed to process bulk interaction logging",
                "status": 500,
                "timestamp": int(time.time())
            }
        )
