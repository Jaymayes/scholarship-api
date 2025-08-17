"""
Interaction Service for Logging User Behavior and API Analytics
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request, Response
from models.interaction import InteractionDB
from utils.logger import get_logger
import json

logger = get_logger("interaction_service")

class InteractionService:
    """Service for logging user interactions"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def log_interaction(
        self,
        event_type: str,
        request: Request,
        response: Response,
        user_id: Optional[str] = None,
        scholarship_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Log user interaction to database
        
        Args:
            event_type: Type of event (root_view, list_scholarships, view_scholarship, search_scholarships)
            request: FastAPI request object
            response: FastAPI response object
            user_id: User ID if authenticated
            scholarship_id: Scholarship ID for specific scholarship interactions
            metadata: Additional metadata (query params, search filters, etc.)
            trace_id: Request trace ID for correlation
            
        Returns:
            Interaction ID if successful, None if failed
        """
        try:
            # Extract request information
            path = str(request.url.path)
            method = request.method
            status = response.status_code
            
            # Get trace ID from request state if not provided
            if not trace_id and hasattr(request.state, 'trace_id'):
                trace_id = request.state.trace_id
            
            # Sanitize metadata - remove sensitive information
            safe_metadata = self._sanitize_metadata(metadata, request)
            
            # Create interaction record
            interaction = InteractionDB(
                event_type=event_type,
                user_id=user_id,
                scholarship_id=scholarship_id,
                path=path,
                method=method,
                status=status,
                trace_id=trace_id,
                request_metadata=safe_metadata
            )
            
            self.db.add(interaction)
            self.db.commit()
            
            logger.info(
                f"Logged interaction: {event_type}",
                extra={
                    "interaction_id": interaction.id,
                    "event_type": event_type,
                    "user_id": user_id,
                    "scholarship_id": scholarship_id,
                    "path": path,
                    "method": method,
                    "status": status,
                    "trace_id": trace_id
                }
            )
            
            return interaction.id
            
        except Exception as e:
            # Never let interaction logging break the main request
            logger.error(
                f"Failed to log interaction: {str(e)}",
                extra={
                    "event_type": event_type,
                    "path": getattr(request, 'url', {}).get('path', 'unknown'),
                    "method": getattr(request, 'method', 'unknown'),
                    "error": str(e),
                    "trace_id": trace_id
                }
            )
            # Rollback any partial transaction
            try:
                self.db.rollback()
            except:
                pass
            return None
    
    def _sanitize_metadata(
        self, 
        metadata: Optional[Dict[str, Any]], 
        request: Request
    ) -> Optional[Dict[str, Any]]:
        """Sanitize metadata to remove sensitive information"""
        try:
            safe_metadata = {}
            
            # Add provided metadata if safe
            if metadata:
                for key, value in metadata.items():
                    # Skip sensitive keys
                    if key.lower() not in ['password', 'token', 'secret', 'key', 'authorization']:
                        safe_metadata[key] = value
            
            # Add query parameters (sanitized)
            if request.query_params:
                query_params = {}
                for key, value in request.query_params.items():
                    if key.lower() not in ['token', 'password', 'secret', 'key']:
                        query_params[key] = value
                if query_params:
                    safe_metadata['query_params'] = query_params
            
            # Add user agent (truncated)
            user_agent = request.headers.get('user-agent')
            if user_agent:
                safe_metadata['user_agent'] = user_agent[:200]  # Truncate to prevent bloat
            
            return safe_metadata if safe_metadata else None
            
        except Exception as e:
            logger.warning(f"Failed to sanitize metadata: {str(e)}")
            return None
    
    def get_interaction_stats(
        self, 
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get interaction statistics"""
        try:
            from sqlalchemy import func, and_
            from datetime import datetime, timedelta
            
            # Base query
            query = self.db.query(InteractionDB)
            
            # Apply filters
            if event_type:
                query = query.filter(InteractionDB.event_type == event_type)
            
            if user_id:
                query = query.filter(InteractionDB.user_id == user_id)
            
            # Time filter
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(InteractionDB.created_at >= since)
            
            # Get counts
            total_count = query.count()
            
            # Get counts by event type
            event_counts = (
                self.db.query(
                    InteractionDB.event_type,
                    func.count(InteractionDB.id).label('count')
                )
                .filter(InteractionDB.created_at >= since)
                .group_by(InteractionDB.event_type)
                .all()
            )
            
            return {
                "total_interactions": total_count,
                "time_window_hours": hours,
                "event_type_counts": {event: count for event, count in event_counts}
            }
            
        except Exception as e:
            logger.error(f"Failed to get interaction stats: {str(e)}")
            return {"error": str(e)}