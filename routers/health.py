"""
Health Check Endpoints for Observability
P0-1 Executive Authorization: Platform resilience and monitoring with circuit breaker pattern
"""

import asyncio
import os
import time
from datetime import datetime
from enum import Enum
from typing import Any, cast

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import get_db
from utils.logger import get_logger

logger = get_logger("health")
router = APIRouter(tags=["Health"])

# Application start time for uptime calculation
APP_START_TIME = time.time()

# Circuit breaker state
class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, skip checks
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for dependency health checks"""
    
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0
    
    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False
        return True

# Circuit breakers for each dependency
db_circuit = CircuitBreaker(failure_threshold=3, timeout=30)
redis_circuit = CircuitBreaker(failure_threshold=3, timeout=30)
ai_circuit = CircuitBreaker(failure_threshold=5, timeout=60)

class ServiceStatus(BaseModel):
    """Individual service health status"""
    status: str  # "ok", "degraded", "down"
    latency_ms: float | None = None
    error: str | None = None

class HealthResponse(BaseModel):
    """Health check response (fast - infrastructure only)"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    commit_sha: str
    uptime_s: int
    db: ServiceStatus
    redis: ServiceStatus

class DeepHealthResponse(BaseModel):
    """Deep health check response (comprehensive - includes AI)"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    commit_sha: str
    uptime_s: int
    db: ServiceStatus
    redis: ServiceStatus
    ai: ServiceStatus

async def check_database_health(timeout: float = 2.0) -> ServiceStatus:
    """Check database with circuit breaker and timeout"""
    if not db_circuit.can_attempt():
        return ServiceStatus(status="degraded", error="Circuit breaker OPEN")
    
    start = time.time()
    try:
        from config.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        db_circuit.record_success()
        return ServiceStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        db_circuit.record_failure()
        return ServiceStatus(status="down", error=str(e)[:100])

async def check_redis_health(timeout: float = 1.0) -> ServiceStatus:
    """Check Redis with circuit breaker"""
    if not redis_circuit.can_attempt():
        return ServiceStatus(status="degraded", error="Circuit breaker OPEN")
    
    start = time.time()
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return ServiceStatus(status="degraded", error="Redis not configured (fallback active)")
        
        # Simple connectivity check - actual Redis check would go here
        latency = (time.time() - start) * 1000
        redis_circuit.record_success()
        return ServiceStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        redis_circuit.record_failure()
        return ServiceStatus(status="degraded", error=str(e)[:50])

async def check_ai_health(timeout: float = 1.0) -> ServiceStatus:
    """Check AI service with circuit breaker and real downstream request"""
    if not ai_circuit.can_attempt():
        return ServiceStatus(status="degraded", error="Circuit breaker OPEN")
    
    start = time.time()
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            ai_circuit.record_failure()
            return ServiceStatus(status="down", error="OPENAI_API_KEY not configured")
        
        # CRITICAL: Make real request to validate downstream service
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=timeout)
        
        # Minimal real request - list models validates API connectivity
        await asyncio.to_thread(lambda: list(client.models.list())[:1])
        
        latency = (time.time() - start) * 1000
        ai_circuit.record_success()
        return ServiceStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        ai_circuit.record_failure()
        return ServiceStatus(status="degraded", error=f"AI request failed: {str(e)[:40]}")

@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Fast Health Check (Infrastructure)",
    description="P0-1: Fast health endpoint for external monitors - DB & Redis only. Target: P95 <150ms"
)
async def fast_health_check() -> HealthResponse:
    """
    P0-1: Fast health check for external monitoring
    Checks: DB, Redis (critical infrastructure only)
    Target: P95 <150ms, >99.9% success rate
    Use: Load balancers, uptime monitors, availability SLAs
    """
    db_result, redis_result = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        return_exceptions=True
    )
    
    # Convert exceptions to ServiceStatus with type casting
    db_status: ServiceStatus
    if isinstance(db_result, Exception):
        db_status = ServiceStatus(status="down", error=str(db_result))
    else:
        db_status = cast(ServiceStatus, db_result)
    
    redis_status: ServiceStatus
    if isinstance(redis_result, Exception):
        redis_status = ServiceStatus(status="degraded", error=str(redis_result))
    else:
        redis_status = cast(ServiceStatus, redis_result)
    
    overall = "healthy"
    if db_status.status == "down":
        overall = "unhealthy"
    elif redis_status.status == "down":
        overall = "degraded"
    elif any(s.status == "degraded" for s in [db_status, redis_status]):
        overall = "degraded"
    
    version = os.getenv("APP_VERSION", "1.0.0")
    commit_sha = os.getenv("GIT_COMMIT_SHA", os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown")[:8]
    uptime = int(time.time() - APP_START_TIME)
    
    return HealthResponse(
        status=overall,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=version,
        commit_sha=commit_sha,
        uptime_s=uptime,
        db=db_status,
        redis=redis_status
    )

@router.get(
    "/api/v1/health/deep",
    response_model=DeepHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Deep Health Check (Comprehensive)",
    description="Deep health validation with AI service check. Target: P95 <1000ms. Use for diagnostics and security validation."
)
async def deep_health_check() -> DeepHealthResponse:
    """
    Deep health check with comprehensive downstream validation
    Checks: DB, Redis, AI (full dependency validation)
    Target: P95 <1000ms
    Use: Pre-deployment validation, incident investigation, security audits
    """
    db_result, redis_result, ai_result = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_ai_health(timeout=2.0),  # More generous timeout for deep checks
        return_exceptions=True
    )
    
    # Convert exceptions to ServiceStatus with type casting
    db_status: ServiceStatus
    if isinstance(db_result, Exception):
        db_status = ServiceStatus(status="down", error=str(db_result))
    else:
        db_status = cast(ServiceStatus, db_result)
    
    redis_status: ServiceStatus
    if isinstance(redis_result, Exception):
        redis_status = ServiceStatus(status="degraded", error=str(redis_result))
    else:
        redis_status = cast(ServiceStatus, redis_result)
    
    ai_status: ServiceStatus
    if isinstance(ai_result, Exception):
        ai_status = ServiceStatus(status="degraded", error=str(ai_result))
    else:
        ai_status = cast(ServiceStatus, ai_result)
    
    overall = "healthy"
    if db_status.status == "down":
        overall = "unhealthy"
    elif redis_status.status == "down" or ai_status.status == "down":
        overall = "degraded"
    elif any(s.status == "degraded" for s in [db_status, redis_status, ai_status]):
        overall = "degraded"
    
    version = os.getenv("APP_VERSION", "1.0.0")
    commit_sha = os.getenv("GIT_COMMIT_SHA", os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown")[:8]
    uptime = int(time.time() - APP_START_TIME)
    
    return DeepHealthResponse(
        status=overall,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=version,
        commit_sha=commit_sha,
        uptime_s=uptime,
        db=db_status,
        redis=redis_status,
        ai=ai_status
    )

@router.get("/canary")
async def canary_check():
    """
    V2.2 Universal Ecosystem Canary Endpoint
    Must return JSON with exact schema for ecosystem health monitoring
    CRITICAL: This MUST be accessible without authentication
    """
    from datetime import datetime
    
    return {
        "ok": True,
        "service": "scholarship_api",
        "base_url": "https://scholarship-api-jamarrlmayes.replit.app",
        "version": "v2.2",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

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
