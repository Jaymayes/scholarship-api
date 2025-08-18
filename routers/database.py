"""
Database Operations Router
Phase 2: Database Integration endpoints for testing and verification
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from models.database import get_db
from services.database_service import DatabaseService
from middleware.auth import require_auth, require_scopes, User
from middleware.rate_limiting import limiter
from utils.logger import get_logger

logger = get_logger("database_router")
router = APIRouter(prefix="/api/v1/database", tags=["Database Operations"])

@router.get("/scholarships")
@limiter.limit("300/minute")
async def get_scholarships_from_db(
    request: Request,
    keyword: Optional[str] = Query(None, description="Search keyword"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(["scholarships:read"]))
):
    """Get scholarships directly from PostgreSQL database"""
    try:
        db_service = DatabaseService(db)
        result = db_service.get_scholarships(
            keyword=keyword,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Retrieved {len(result['scholarships'])} scholarships from database for user {current_user.user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving scholarships from database: {str(e)}")
        raise HTTPException(status_code=500, detail="Database query failed")

@router.get("/scholarships/{scholarship_id}")
@limiter.limit("300/minute")
async def get_scholarship_from_db(
    request: Request,
    scholarship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(["scholarships:read"]))
):
    """Get specific scholarship directly from PostgreSQL database"""
    try:
        db_service = DatabaseService(db)
        scholarship = db_service.get_scholarship_by_id(scholarship_id)
        
        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")
        
        logger.info(f"Retrieved scholarship {scholarship_id} from database for user {current_user.user_id}")
        return scholarship
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scholarship {scholarship_id} from database: {str(e)}")
        raise HTTPException(status_code=500, detail="Database query failed")

@router.post("/interactions")
@limiter.limit("100/minute")
async def log_interaction_to_db(
    request: Request,
    interaction_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(["scholarships:read"]))
):
    """Log user interaction directly to PostgreSQL database"""
    try:
        db_service = DatabaseService(db)
        
        interaction_id = db_service.log_user_interaction(
            user_id=current_user.user_id,
            scholarship_id=interaction_data.get("scholarship_id"),
            interaction_type=interaction_data.get("interaction_type", "viewed"),
            search_query=interaction_data.get("search_query"),
            filters_applied=interaction_data.get("filters_applied"),
            match_score=interaction_data.get("match_score"),
            position_in_results=interaction_data.get("position_in_results"),
            session_id=interaction_data.get("session_id"),
            source=interaction_data.get("source", "direct")
        )
        
        logger.info(f"Logged interaction {interaction_id} to database for user {current_user.user_id}")
        return {"interaction_id": interaction_id, "status": "logged"}
        
    except Exception as e:
        logger.error(f"Error logging interaction to database: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log interaction")

@router.get("/analytics/summary")
@limiter.limit("60/minute")
async def get_analytics_from_db(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(["analytics:read"]))
):
    """Get analytics summary directly from PostgreSQL database"""
    try:
        db_service = DatabaseService(db)
        summary = db_service.get_analytics_summary()
        
        logger.info(f"Retrieved analytics summary from database for user {current_user.user_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Error retrieving analytics from database: {str(e)}")
        raise HTTPException(status_code=500, detail="Analytics query failed")

@router.get("/analytics/popular")
@limiter.limit("60/minute")
async def get_popular_scholarships_from_db(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of popular scholarships"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(["analytics:read"]))
):
    """Get popular scholarships directly from PostgreSQL database"""
    try:
        db_service = DatabaseService(db)
        popular = db_service.get_popular_scholarships(limit=limit)
        
        logger.info(f"Retrieved {len(popular)} popular scholarships from database for user {current_user.user_id}")
        return {"popular_scholarships": popular}
        
    except Exception as e:
        logger.error(f"Error retrieving popular scholarships from database: {str(e)}")
        raise HTTPException(status_code=500, detail="Popular scholarships query failed")

@router.get("/status")
async def database_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """Check database connection and basic statistics (no authentication required for health check)"""
    try:
        # Simple database connectivity test using minimal query
        from sqlalchemy import text
        
        # Test basic connectivity with a simple query
        result = db.execute(text("SELECT 1")).scalar()
        if result != 1:
            raise RuntimeError("Database connectivity test failed")
        
        # Get basic statistics without relying on user context
        from models.database import ScholarshipDB, UserInteractionDB
        
        try:
            scholarship_count = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True).count()
        except Exception:
            scholarship_count = "unknown"
            
        try:
            interaction_count = db.query(UserInteractionDB).count()
        except Exception:
            interaction_count = "unknown"
        
        status = {
            "database_status": "connected",
            "total_scholarships": scholarship_count,
            "total_interactions": interaction_count,
            "database_type": "PostgreSQL",
            "connection_test": "passed"
        }
        
        logger.info("Database status check completed successfully")
        return status
        
    except Exception as e:
        logger.error(f"Database status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")