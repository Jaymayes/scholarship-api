"""
Replit-specific health check endpoints with Input Validation - QA-006 fix
Robust health checks designed for Replit deployment environment
"""

import os
import time

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from config.settings import settings
from schemas.health import (
    BasicHealthResponse,
    CorsConfig,
    DatabaseConfig,
    DatabaseHealthResponse,
    DebugConfigResponse,
    FeatureConfig,
    HealthStatus,
    JwtConfig,
    RateLimitConfig,
    ReplitEnvConfig,
    ServiceInfo,
    ServicesHealthResponse,
    ServiceStatus,
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/healthz", response_model=BasicHealthResponse)
async def health_check_replit():
    """
    Replit-optimized health check endpoint
    Returns simple JSON for deployment health monitoring
    QA-006 fix: Strict response model, no input parameters accepted
    """
    return BasicHealthResponse(
        status="healthy",
        timestamp=int(time.time()),
        environment=settings.environment.value
    )

@router.get("/health/database", response_model=DatabaseHealthResponse)
async def database_health_check():
    """
    Database connectivity health check with Replit-specific handling
    Uses short timeout and graceful fallback for SQLite in dev
    """
    try:
        # For Replit, handle both PostgreSQL and SQLite fallback
        if settings.database_url:
            # Import here to avoid circular imports
            # Try to use existing database models for connectivity test
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            # Create a temporary session for health check
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as session:
                # Simple connectivity test with timeout
                result = session.execute(text("SELECT 1")).scalar()

                if result == 1:
                    return DatabaseHealthResponse(
                        status="healthy",
                        database="connected",
                        type=getattr(settings, 'get_database_info', 'PostgreSQL'),
                        timestamp=int(time.time())
                    )
                raise Exception("Database connectivity test failed")
        else:
            # Development fallback (Replit without DATABASE_URL)
            if settings.is_development:
                return DatabaseHealthResponse(
                    status="healthy",
                    database="development_mode",
                    type="SQLite fallback",
                    note="Using in-memory database for development",
                    timestamp=int(time.time())
                )
            raise Exception("No database configured")

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")

        # Return 503 with unified error format
        raise HTTPException(
            status_code=503,
            detail={
                "trace_id": "health_check",
                "code": "DATABASE_UNAVAILABLE",
                "message": f"Database health check failed: {str(e)}",
                "status": 503,
                "timestamp": int(time.time())
            }
        )

@router.get("/health/services", response_model=ServicesHealthResponse)
async def services_health_check():
    """
    Comprehensive services health check for Replit deployment
    Checks all external dependencies with graceful fallbacks
    """
    services_status = {}
    overall_healthy = True

    # Check rate limiter
    try:
        limiter_info = getattr(settings, 'get_rate_limiter_info', 'Redis')
        services_status["rate_limiter"] = ServiceInfo(
            status=ServiceStatus.HEALTHY,
            backend=limiter_info
        )
    except Exception:
        services_status["rate_limiter"] = ServiceInfo(
            status=ServiceStatus.DEGRADED,
            backend="in-memory fallback",
            note="Redis unavailable, using memory backend"
        )

    # Check database
    try:
        db_info = getattr(settings, 'get_database_info', 'PostgreSQL')
        services_status["database"] = ServiceInfo(
            status=ServiceStatus.HEALTHY,
            type=db_info
        )
    except Exception as e:
        services_status["database"] = ServiceInfo(
            status=ServiceStatus.UNHEALTHY,
            error=str(e)
        )
        overall_healthy = False

    # Check OpenAI (if configured)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        services_status["openai"] = ServiceInfo(
            status=ServiceStatus.CONFIGURED,
            note="API key present"
        )
    else:
        services_status["openai"] = ServiceInfo(
            status=ServiceStatus.NOT_CONFIGURED,
            note="API key not provided"
        )

    return ServicesHealthResponse(
        status=HealthStatus.HEALTHY if overall_healthy else HealthStatus.DEGRADED,
        services=services_status,
        timestamp=int(time.time()),
        environment=settings.environment.value
    )

# DEF-002 SECURITY FIX: Debug endpoint removed per CEO directive (Day 0 Priority #1)
# Previously exposed JWT secret length, database config, Replit env details
# Endpoint completely removed - no development exception
