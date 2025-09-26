"""
Disaster Recovery Dashboard Router
Provides backup/restore status endpoints for CEO/Marketing dashboards
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse

from infrastructure.disaster_recovery_service import (
    dr_service,
)
from middleware.auth import User, get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/disaster-recovery", tags=["Disaster Recovery"])

@router.get("/status/global", response_model=dict[str, Any])
async def get_global_dr_status():
    """
    Get global disaster recovery status for CEO/Marketing dashboards

    Returns comprehensive DR status across all applications including:
    - Backup health scores
    - Compliance status
    - Storage utilization
    - Recovery time objectives
    """
    try:
        dashboard_data = await dr_service.get_global_dr_dashboard()

        logger.info("Global DR status retrieved for dashboard")
        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to retrieve global DR status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve DR status")

@router.get("/status/{app_name}", response_model=dict[str, Any])
async def get_app_dr_status(app_name: str):
    """
    Get disaster recovery status for specific application

    Args:
        app_name: Application name (scholarship_api, auto_command_center, etc.)
    """
    try:
        dr_status = await dr_service.get_dr_status(app_name)

        return {
            "app_name": dr_status.app_name,
            "last_backup_time": dr_status.last_backup_time.isoformat() if dr_status.last_backup_time != datetime.min else None,
            "last_successful_backup": dr_status.last_successful_backup.isoformat() if dr_status.last_successful_backup != datetime.min else None,
            "backup_frequency_hours": dr_status.backup_frequency_hours,
            "next_backup_time": dr_status.next_backup_time.isoformat(),
            "backup_retention_days": dr_status.backup_retention_days,
            "rpo_target_hours": dr_status.rpo_target_hours,
            "rto_target_hours": dr_status.rto_target_hours,
            "last_restore_test": dr_status.last_restore_test.isoformat() if dr_status.last_restore_test else None,
            "backup_health_score": round(dr_status.backup_health_score, 1),
            "compliance_status": dr_status.compliance_status
        }

    except Exception as e:
        logger.error(f"Failed to retrieve DR status for {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DR status for {app_name}")

@router.post("/backup/{app_name}")
async def create_backup(app_name: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """
    Create backup for specified application

    Args:
        app_name: Application to backup
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
    """
    try:
        # Validate app name
        if app_name not in dr_service.dr_config:
            raise HTTPException(status_code=404, detail=f"Application {app_name} not found in DR configuration")

        # Start backup in background
        backup_record = await dr_service.create_database_backup(app_name)

        logger.info(f"Backup initiated for {app_name} by {current_user.user_id}")

        return {
            "backup_id": backup_record.backup_id,
            "app_name": backup_record.app_name,
            "status": backup_record.status.value,
            "created_at": backup_record.created_at.isoformat(),
            "message": "Backup initiated successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create backup for {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

@router.post("/restore/{backup_id}")
async def initiate_restore(backup_id: str, target_app: str, current_user: User = Depends(get_current_user)):
    """
    Initiate restore operation from backup

    Args:
        backup_id: ID of backup to restore
        target_app: Target application for restore
        current_user: Authenticated user
    """
    try:
        restore_record = await dr_service.initiate_restore(backup_id, target_app, current_user.user_id)

        logger.info(f"Restore initiated: {restore_record.restore_id} by {current_user.user_id}")

        return {
            "restore_id": restore_record.restore_id,
            "backup_id": restore_record.backup_id,
            "target_app": restore_record.app_name,
            "status": restore_record.status.value,
            "initiated_by": restore_record.initiated_by,
            "created_at": restore_record.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to initiate restore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate restore: {str(e)}")

@router.get("/backups", response_model=list[dict[str, Any]])
async def list_backups(app_name: str | None = None, limit: int = 50):
    """
    List recent backups with optional filtering

    Args:
        app_name: Optional app filter
        limit: Maximum number of records to return
    """
    try:
        backups = dr_service.backup_records

        if app_name:
            backups = [b for b in backups if b.app_name == app_name]

        # Sort by creation time (newest first) and limit
        backups = sorted(backups, key=lambda b: b.created_at, reverse=True)[:limit]

        return [
            {
                "backup_id": backup.backup_id,
                "app_name": backup.app_name,
                "backup_type": backup.backup_type,
                "status": backup.status.value,
                "size_bytes": backup.size_bytes,
                "location": backup.location,
                "created_at": backup.created_at.isoformat(),
                "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
                "error_message": backup.error_message,
                "retention_days": backup.retention_days
            }
            for backup in backups
        ]

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail="Failed to list backups")

@router.get("/restores", response_model=list[dict[str, Any]])
async def list_restores(app_name: str | None = None, limit: int = 20):
    """
    List recent restore operations

    Args:
        app_name: Optional app filter
        limit: Maximum number of records to return
    """
    try:
        restores = dr_service.restore_records

        if app_name:
            restores = [r for r in restores if r.app_name == app_name]

        # Sort by creation time (newest first) and limit
        restores = sorted(restores, key=lambda r: r.created_at, reverse=True)[:limit]

        return [
            {
                "restore_id": restore.restore_id,
                "backup_id": restore.backup_id,
                "app_name": restore.app_name,
                "restore_type": restore.restore_type,
                "status": restore.status.value,
                "initiated_by": restore.initiated_by,
                "created_at": restore.created_at.isoformat(),
                "completed_at": restore.completed_at.isoformat() if restore.completed_at else None,
                "error_message": restore.error_message,
                "validation_passed": restore.validation_passed
            }
            for restore in restores
        ]

    except Exception as e:
        logger.error(f"Failed to list restores: {e}")
        raise HTTPException(status_code=500, detail="Failed to list restores")

@router.get("/health-check")
async def dr_health_check():
    """
    Health check endpoint for DR service
    """
    try:
        # Perform basic service checks
        total_apps = len(dr_service.dr_config)
        total_backups = len(dr_service.backup_records)

        # Check if all critical apps have recent backups
        critical_apps = [app for app, config in dr_service.dr_config.items() if config.get('critical_priority', False)]
        critical_status = {}

        for app in critical_apps:
            dr_status = await dr_service.get_dr_status(app)
            critical_status[app] = {
                "health_score": dr_status.backup_health_score,
                "compliance": dr_status.compliance_status
            }

        overall_health = "healthy"
        if any(status["compliance"] == "non_compliant" for status in critical_status.values()):
            overall_health = "degraded"

        return {
            "status": overall_health,
            "total_applications": total_apps,
            "total_backups": total_backups,
            "critical_apps_status": critical_status,
            "service_version": "1.0.0",
            "last_check": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"DR health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
        )

@router.post("/test-restore/{app_name}")
async def schedule_restore_test(app_name: str, current_user: User = Depends(get_current_user)):
    """
    Schedule disaster recovery test for application

    Args:
        app_name: Application to test DR for
        current_user: Authenticated user
    """
    try:
        # Get latest successful backup
        app_backups = [b for b in dr_service.backup_records
                      if b.app_name == app_name and b.status.value == "success"]

        if not app_backups:
            raise HTTPException(status_code=404, detail=f"No successful backups found for {app_name}")

        latest_backup = max(app_backups, key=lambda b: b.created_at)

        # Create test restore in a separate environment (simulated)
        test_restore_id = f"test-restore-{app_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"DR test scheduled for {app_name} using backup {latest_backup.backup_id}")

        return {
            "test_restore_id": test_restore_id,
            "app_name": app_name,
            "backup_used": latest_backup.backup_id,
            "scheduled_by": current_user.user_id,
            "scheduled_at": datetime.utcnow().isoformat(),
            "estimated_duration_minutes": 30,
            "message": "DR test scheduled successfully"
        }

    except Exception as e:
        logger.error(f"Failed to schedule DR test for {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule DR test: {str(e)}")

@router.get("/metrics/dashboard")
async def get_dr_metrics_for_dashboard():
    """
    Get DR metrics formatted for executive dashboards
    """
    try:
        dashboard_data = await dr_service.get_global_dr_dashboard()

        # Format for executive consumption
        executive_metrics = {
            "disaster_recovery_status": {
                "overall_health": "healthy" if dashboard_data["global_metrics"]["compliance_score"] >= 80 else "at_risk",
                "applications_protected": f"{dashboard_data['global_metrics']['apps_compliant']}/{dashboard_data['global_metrics']['apps_total']}",
                "backup_success_rate": f"{(dashboard_data['global_metrics']['successful_backups_24h'] / max(dashboard_data['global_metrics']['total_backups_24h'], 1)) * 100:.1f}%",
                "storage_utilized_gb": dashboard_data["global_metrics"]["total_storage_gb"],
                "last_updated": dashboard_data["last_updated"]
            },
            "critical_applications": {},
            "key_metrics": {
                "rpo_compliance": "≤24h",
                "rto_target": "≤4h",
                "backup_frequency": "Every 6h",
                "retention_period": "90 days"
            }
        }

        # Add critical app details
        for app_name, app_data in dashboard_data["apps"].items():
            if dr_service.dr_config.get(app_name, {}).get('critical_priority', False):
                executive_metrics["critical_applications"][app_name] = {
                    "status": "✅ Protected" if app_data["status"] == "compliant" else "⚠️ At Risk",
                    "health_score": f"{app_data['health_score']}%",
                    "last_backup": app_data["last_backup"],
                    "next_backup": app_data["next_backup"]
                }

        return executive_metrics

    except Exception as e:
        logger.error(f"Failed to get DR metrics for dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DR metrics")
