"""
A8 Banner Auto-Clear Implementation
File: services/incident_reconciler.py

Implements TTL-based auto-clearing of incident banners after sustained recovery.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.orm import Session

# Feature flags
BANNER_AUTO_CLEAR_ENABLED = os.getenv("BANNER_AUTO_CLEAR_ENABLED", "false").lower() == "true"
BANNER_TTL_MINUTES = int(os.getenv("BANNER_TTL_MINUTES", "15"))

class IncidentBanner:
    """Extended incident model with TTL support"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True)
    app_id = Column(String, nullable=False)
    severity = Column(String, default="warning")  # warning, critical
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_unhealthy_at = Column(DateTime, default=datetime.utcnow)
    last_healthy_at = Column(DateTime, nullable=True)
    current_status = Column(String, default="red")  # red, yellow, green, cleared
    auto_cleared = Column(Boolean, default=False)
    cleared_at = Column(DateTime, nullable=True)
    cleared_by = Column(String, nullable=True)  # "auto" or admin user

async def update_service_status(db: Session, app_id: str, is_healthy: bool):
    """
    Update service status and manage banner TTL.
    Call this from health check aggregation.
    """
    incident = db.query(IncidentBanner).filter(
        IncidentBanner.app_id == app_id,
        IncidentBanner.current_status.in_(["red", "yellow", "green"])
    ).first()
    
    if not incident:
        if not is_healthy:
            # Create new incident
            incident = IncidentBanner(
                app_id=app_id,
                severity="warning",
                message=f"Service {app_id} is unhealthy",
                current_status="red"
            )
            db.add(incident)
        return
    
    if is_healthy:
        # Service recovered
        incident.current_status = "green"
        incident.last_healthy_at = datetime.utcnow()
    else:
        # Service unhealthy
        incident.current_status = "red"
        incident.last_unhealthy_at = datetime.utcnow()
        incident.last_healthy_at = None  # Reset recovery timer
    
    db.commit()

async def reconcile_banners(db: Session) -> List[str]:
    """
    Auto-clear banners that have been green for TTL period.
    Run this as a scheduled task every minute.
    
    Returns list of cleared incident IDs.
    """
    if not BANNER_AUTO_CLEAR_ENABLED:
        return []
    
    cutoff = datetime.utcnow() - timedelta(minutes=BANNER_TTL_MINUTES)
    cleared = []
    
    # Find incidents that have been green past TTL
    stale_incidents = db.query(IncidentBanner).filter(
        IncidentBanner.current_status == "green",
        IncidentBanner.last_healthy_at < cutoff,
        IncidentBanner.auto_cleared == False
    ).all()
    
    for incident in stale_incidents:
        incident.current_status = "cleared"
        incident.auto_cleared = True
        incident.cleared_at = datetime.utcnow()
        incident.cleared_by = "auto"
        cleared.append(str(incident.id))
    
    if cleared:
        db.commit()
    
    return cleared

# Admin endpoint for manual clearing
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def verify_admin_token(x_admin_token: str = Header(...)):
    """Verify admin authentication"""
    expected = os.getenv("ADMIN_CLEAR_TOKEN")
    if not expected or x_admin_token != expected:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True

@router.post("/clear-stale-incidents")
async def admin_clear_incidents(
    app_id: Optional[str] = None,
    admin: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to manually clear stale incidents.
    
    Args:
        app_id: Optional - clear only incidents for this app
    """
    query = db.query(IncidentBanner).filter(
        IncidentBanner.current_status.in_(["green", "yellow"])
    )
    
    if app_id:
        query = query.filter(IncidentBanner.app_id == app_id)
    
    incidents = query.all()
    cleared = []
    
    for incident in incidents:
        incident.current_status = "cleared"
        incident.cleared_at = datetime.utcnow()
        incident.cleared_by = "admin"
        cleared.append(incident.id)
    
    db.commit()
    
    return {
        "cleared_count": len(cleared),
        "cleared_ids": cleared
    }

@router.get("/incidents")
async def list_active_incidents(
    admin: bool = Depends(verify_admin_token),
    db: Session = Depends(get_db)
):
    """List all active (non-cleared) incidents"""
    incidents = db.query(IncidentBanner).filter(
        IncidentBanner.current_status != "cleared"
    ).all()
    
    return [
        {
            "id": i.id,
            "app_id": i.app_id,
            "status": i.current_status,
            "created_at": i.created_at.isoformat(),
            "last_healthy_at": i.last_healthy_at.isoformat() if i.last_healthy_at else None
        }
        for i in incidents
    ]
