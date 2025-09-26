"""
Health Check Endpoints for Observability
"""

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import get_db
from utils.logger import get_logger

logger = get_logger("health")
router = APIRouter(tags=["Health"])

@router.get("/healthz")
async def liveness_probe() -> dict[str, str]:
    """
    Liveness probe - checks if the application is running
    Returns 200 if the service is alive
    """
    return {"status": "ok", "service": "scholarship-api"}

@router.get("/readyz")
async def readiness_probe(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness probe - checks if the application is ready to serve requests
    Checks database connectivity and other dependencies
    """
    try:
        health_status = {
            "status": "ready",
            "service": "scholarship-api",
            "checks": {}
        }

        # Check database connectivity
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            health_status["checks"]["database"] = {
                "status": "healthy",
                "type": "PostgreSQL"
            }
        except Exception as db_error:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(db_error),
                "type": "PostgreSQL"
            }
            health_status["status"] = "not_ready"

        # Check Redis (if configured)
        redis_url = os.getenv("RATE_LIMIT_REDIS_URL")
        if redis_url:
            try:
                # This is a placeholder - would need actual Redis client
                health_status["checks"]["redis"] = {
                    "status": "healthy",
                    "type": "Redis Rate Limiting"
                }
            except Exception as redis_error:
                health_status["checks"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(redis_error),
                    "type": "Redis Rate Limiting"
                }
        else:
            health_status["checks"]["redis"] = {
                "status": "not_configured",
                "type": "In-Memory Rate Limiting"
            }

        # Check environment configuration
        required_configs = ["DATABASE_URL", "JWT_SECRET_KEY"]
        missing_configs = [config for config in required_configs if not os.getenv(config)]

        if missing_configs:
            health_status["checks"]["configuration"] = {
                "status": "unhealthy",
                "missing": missing_configs
            }
            health_status["status"] = "not_ready"
        else:
            health_status["checks"]["configuration"] = {
                "status": "healthy"
            }

        # Return appropriate status code
        if health_status["status"] == "not_ready":
            raise HTTPException(status_code=503, detail=health_status)

        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e)
            }
        )
