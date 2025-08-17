"""
Interaction Logging Wrapper Functions
"""

from typing import Optional
from fastapi import Request, Response
from sqlalchemy.orm import Session
from services.interaction_service import InteractionService
from models.database import get_db
from utils.logger import get_logger

logger = get_logger("interaction_wrapper")

async def log_scholarship_interaction(
    request: Request,
    response: Response, 
    event_type: str,
    scholarship_id: Optional[str] = None,
    user_id: Optional[str] = None
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

def with_interaction_logging(event_type: str, scholarship_id_param: Optional[str] = None):
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