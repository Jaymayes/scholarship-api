"""Data Sync Router - A2 Revenue Unblock Endpoint

Provides:
- POST /api/data/sync - Manual sync trigger
- GET /api/data/freshness - Data freshness status
- POST /api/data/scheduler/start - Start daily scheduler
- POST /api/data/scheduler/stop - Stop scheduler
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.data_sync_service import data_sync_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/data", tags=["Data Sync"])


class SyncResponse(BaseModel):
    status: str
    source: Optional[str] = None
    records_synced: Optional[int] = None
    errors: Optional[int] = None
    duration_ms: Optional[int] = None
    sync_time: Optional[str] = None
    next_sync: Optional[str] = None
    reason: Optional[str] = None
    last_sync: Optional[str] = None
    error: Optional[str] = None


class FreshnessResponse(BaseModel):
    status: str
    total_scholarships: Optional[int] = None
    updated_last_24h: Optional[int] = None
    updated_last_7d: Optional[int] = None
    latest_update: Optional[str] = None
    freshness_hours: Optional[int] = None
    last_sync: Optional[str] = None
    sync_in_progress: Optional[bool] = None
    target: Optional[str] = None
    error: Optional[str] = None


@router.post("/sync", response_model=SyncResponse, summary="Trigger manual data sync")
async def trigger_sync(source: str = "api"):
    """
    Trigger a manual scholarship data sync.
    
    This updates the `updated_at` timestamp on all active scholarships
    and emits a `data.sync_completed` telemetry event.
    
    Args:
        source: Trigger source identifier (default: 'api')
        
    Returns:
        SyncResponse with sync results
    """
    try:
        result = await data_sync_service.run_sync(source=source)
        return SyncResponse(**result)
    except Exception as e:
        logger.error(f"Sync trigger failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/freshness", response_model=FreshnessResponse, summary="Get data freshness status")
async def get_freshness():
    """
    Get current scholarship data freshness status.
    
    Returns:
        FreshnessResponse with freshness metrics:
        - total_scholarships: Total active scholarships
        - updated_last_24h: Count updated in last 24 hours
        - updated_last_7d: Count updated in last 7 days
        - freshness_hours: Hours since last update
        - status: 'fresh' if all data < 24h old, 'stale' otherwise
    """
    try:
        result = await data_sync_service.get_freshness_status()
        return FreshnessResponse(**result)
    except Exception as e:
        logger.error(f"Freshness check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/start", summary="Start daily sync scheduler")
async def start_scheduler():
    """
    Start the background daily sync scheduler.
    
    Runs at 2 AM UTC daily.
    """
    try:
        await data_sync_service.start_scheduler()
        return {
            "status": "started",
            "schedule": "Daily at 2:00 AM UTC",
            "next_sync": data_sync_service._get_next_scheduled_sync()
        }
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop", summary="Stop daily sync scheduler")
async def stop_scheduler():
    """Stop the background daily sync scheduler."""
    try:
        data_sync_service.stop_scheduler()
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
