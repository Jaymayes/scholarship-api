"""
Database Status Router
Provides database connectivity and health information
"""

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings import settings
from models.database import get_db
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Database Status"])

async def get_db_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get database connectivity status and counts"""
    start_time = time.time()

    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        connected = True

        # Get scholarship count
        scholarship_count = 0
        try:
            result = db.execute(text("SELECT COUNT(*) FROM scholarships"))
            scholarship_count = result.scalar() or 0
        except Exception:
            scholarship_count = "N/A"

        # Get interactions count if table exists
        interactions_count = 0
        try:
            result = db.execute(text("SELECT COUNT(*) FROM interactions"))
            interactions_count = result.scalar() or 0
        except Exception:
            interactions_count = "N/A"

        took_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "ok",
            "database": {
                "connected": connected,
                "url": f"postgresql://{settings.database_url.split('@')[1] if '@' in settings.database_url else 'redacted'}",
                "scholarships": scholarship_count,
                "interactions": interactions_count
            },
            "environment": settings.environment,
            "took_ms": took_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        took_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Database status check failed: {str(e)}")

        # Return 503 for database connectivity issues
        raise HTTPException(
            status_code=503,
            detail={
                "status": "down",
                "database": {
                    "connected": False,
                    "error": str(e),
                    "url": "redacted"
                },
                "environment": settings.environment,
                "took_ms": took_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/db/status")
async def get_database_status_root(status_data: dict[str, Any] = Depends(get_db_status)):
    """Get database status - root endpoint"""
    return status_data

@router.get("/api/v1/db/status")
async def get_database_status_api(status_data: dict[str, Any] = Depends(get_db_status)):
    """Get database status - API v1 endpoint"""
    return status_data
