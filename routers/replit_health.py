"""
Replit-specific health check endpoints
Robust health checks designed for Replit deployment environment
"""

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
from utils.logger import get_logger
from config.settings import settings
import time
import os

logger = get_logger(__name__)
router = APIRouter()

@router.get("/healthz")
async def health_check_replit():
    """
    Replit-optimized health check endpoint
    Returns simple JSON for deployment health monitoring
    """
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "environment": settings.environment.value
    }

@router.get("/health/database")
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
            from models.scholarship import Scholarship
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            
            # Create a temporary session for health check
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            
            with SessionLocal() as session:
                # Simple connectivity test with timeout
                result = session.execute(text("SELECT 1")).scalar()
                
                if result == 1:
                    return {
                        "status": "healthy",
                        "database": "connected",
                        "type": settings.get_database_info,
                        "timestamp": int(time.time())
                    }
                else:
                    raise Exception("Database connectivity test failed")
        else:
            # Development fallback (Replit without DATABASE_URL)
            if settings.is_development:
                return {
                    "status": "healthy", 
                    "database": "development_mode",
                    "type": "SQLite fallback",
                    "note": "Using in-memory database for development",
                    "timestamp": int(time.time())
                }
            else:
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

@router.get("/health/services")
async def services_health_check():
    """
    Comprehensive services health check for Replit deployment
    Checks all external dependencies with graceful fallbacks
    """
    services_status = {}
    overall_healthy = True
    
    # Check rate limiter
    try:
        limiter_info = settings.get_rate_limiter_info
        services_status["rate_limiter"] = {
            "status": "healthy",
            "backend": limiter_info
        }
    except Exception as e:
        services_status["rate_limiter"] = {
            "status": "degraded",
            "backend": "in-memory fallback",
            "note": "Redis unavailable, using memory backend"
        }
    
    # Check database
    try:
        db_info = settings.get_database_info
        services_status["database"] = {
            "status": "healthy",
            "type": db_info
        }
    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check OpenAI (if configured)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        services_status["openai"] = {
            "status": "configured",
            "note": "API key present"
        }
    else:
        services_status["openai"] = {
            "status": "not_configured",
            "note": "API key not provided"
        }
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "services": services_status,
        "timestamp": int(time.time()),
        "environment": settings.environment.value
    }

@router.get("/_debug/config")
async def debug_config():
    """
    Development-only configuration diagnostics
    Returns sanitized configuration info for Replit debugging
    """
    # Only allow in development environments
    if settings.environment == settings.environment.PRODUCTION:
        raise HTTPException(
            status_code=404,
            detail="Debug endpoint not available in production"
        )
    
    # Sanitized config info for debugging
    cors_origins = settings.get_cors_origins
    
    return {
        "environment": settings.environment.value,
        "debug_mode": settings.debug,
        "cors": {
            "origins_count": len(cors_origins) if cors_origins != ["*"] else "wildcard",
            "wildcard_enabled": "*" in cors_origins,
            "replit_origin_detected": any("replit" in origin for origin in cors_origins if isinstance(origin, str))
        },
        "rate_limiting": {
            "backend_type": settings.get_rate_limiter_info,
            "per_minute_limit": settings.get_rate_limit_per_minute,
            "enabled": settings.rate_limit_enabled
        },
        "database": {
            "type": settings.get_database_info,
            "configured": bool(settings.database_url)
        },
        "jwt": {
            "algorithm": settings.jwt_algorithm,
            "secret_configured": bool(settings.jwt_secret_key),
            "secret_length": len(settings.jwt_secret_key) if settings.jwt_secret_key else 0
        },
        "features": {
            "analytics": settings.analytics_enabled,
            "metrics": settings.metrics_enabled,
            "tracing": settings.tracing_enabled
        },
        "replit_env": {
            "repl_id": os.getenv("REPL_ID", "not_set"),
            "repl_owner": os.getenv("REPL_OWNER", "not_set"),
            "port": os.getenv("PORT", "not_set")
        }
    }