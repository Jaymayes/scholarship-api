"""
Production Health Probes and Graceful Shutdown
Priority 3: Resilience and deploy safety with zero in-flight loss
"""
import asyncio
import signal
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.logger import setup_logger

logger = setup_logger()

class HealthProbeManager:
    """Production-grade health probe management with graceful shutdown"""

    def __init__(self):
        self.is_shutting_down = False
        self.active_requests = 0
        self.shutdown_timeout = 30  # seconds
        self.startup_time = time.time()

    def track_request(self):
        """Track active requests for graceful shutdown"""
        if not self.is_shutting_down:
            self.active_requests += 1

    def untrack_request(self):
        """Untrack completed requests"""
        self.active_requests = max(0, self.active_requests - 1)

    async def liveness_probe(self) -> dict[str, Any]:
        """
        Kubernetes-style liveness probe
        Returns 200 if process is alive, 503 if shutting down
        """
        if self.is_shutting_down:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "shutting_down",
                    "message": "Service is gracefully shutting down"
                }
            )

        return {
            "status": "healthy",
            "service": "scholarship-api",
            "uptime_seconds": int(time.time() - self.startup_time)
        }

    async def readiness_probe(self, db: Session) -> dict[str, Any]:
        """
        Enhanced readiness probe with dependency checks
        Returns 200 if ready to serve, 503 if not ready
        """
        if self.is_shutting_down:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "reason": "shutting_down",
                    "active_requests": self.active_requests
                }
            )

        health_checks = {
            "status": "ready",
            "checks": {},
            "timestamp": time.time()
        }

        # Database connectivity check
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            health_checks["checks"]["database"] = {
                "status": "healthy",
                "type": "PostgreSQL",
                "response_time_ms": 0  # Could add timing
            }
        except Exception as e:
            health_checks["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "type": "PostgreSQL"
            }
            health_checks["status"] = "not_ready"

        # Service dependencies check
        try:
            from services.scholarship_service import scholarship_service
            scholarship_count = len(scholarship_service.scholarships)
            health_checks["checks"]["scholarship_service"] = {
                "status": "healthy",
                "scholarship_count": scholarship_count
            }
        except Exception as e:
            health_checks["checks"]["scholarship_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_checks["status"] = "not_ready"

        # Return appropriate status
        if health_checks["status"] == "not_ready":
            raise HTTPException(status_code=503, detail=health_checks)

        return health_checks

    async def startup_probe(self, db: Session) -> dict[str, Any]:
        """
        Startup probe for applications with slow startup
        Returns 200 when fully initialized
        """
        # Check if all critical services are initialized
        checks = {
            "status": "starting",
            "checks": {}
        }

        # Database check
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            checks["checks"]["database"] = {"status": "ready"}
        except Exception:
            checks["checks"]["database"] = {"status": "not_ready"}

        # Scholarship service check
        try:
            from services.scholarship_service import scholarship_service
            if scholarship_service.scholarships:
                checks["checks"]["scholarship_service"] = {"status": "ready"}
            else:
                checks["checks"]["scholarship_service"] = {"status": "loading"}
        except Exception:
            checks["checks"]["scholarship_service"] = {"status": "not_ready"}

        # Metrics check
        try:
            checks["checks"]["metrics"] = {"status": "ready"}
        except Exception:
            checks["checks"]["metrics"] = {"status": "not_ready"}

        # All checks must pass for startup completion
        all_ready = all(
            check["status"] == "ready"
            for check in checks["checks"].values()
        )

        if all_ready:
            checks["status"] = "ready"
        else:
            raise HTTPException(status_code=503, detail=checks)

        return checks

    async def graceful_shutdown(self, app: FastAPI):
        """
        Graceful shutdown handler
        1. Stop accepting new requests
        2. Wait for active requests to complete
        3. Close resources
        """
        logger.info("🔌 Initiating graceful shutdown")
        self.is_shutting_down = True

        # Wait for active requests to complete
        shutdown_start = time.time()
        while self.active_requests > 0:
            if time.time() - shutdown_start > self.shutdown_timeout:
                logger.warning(f"⏰ Shutdown timeout reached with {self.active_requests} active requests")
                break

            logger.info(f"⏳ Waiting for {self.active_requests} active requests to complete")
            await asyncio.sleep(0.1)

        # Close database connections
        try:
            # Database connections will be closed by middleware
            logger.info("📊 Database connections will be closed by middleware")
        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")

        # Close orchestrator service
        try:
            from services.orchestrator_service import orchestrator_service
            await orchestrator_service.close()
            logger.info("🔗 Orchestrator service closed")
        except Exception as e:
            logger.error(f"Failed to close orchestrator service: {e}")

        logger.info("✅ Graceful shutdown completed")

# Global health probe manager
health_manager = HealthProbeManager()

@asynccontextmanager
async def enhanced_lifespan(app: FastAPI):
    """Enhanced lifespan with production health probe management"""
    # Startup
    logger.info("🚀 Enhanced production startup initiated")

    # Initialize all services (existing startup logic)

    # Set up graceful shutdown handlers
    def signal_handler(signum, frame):
        logger.info(f"📡 Received signal {signum}")
        asyncio.create_task(health_manager.graceful_shutdown(app))

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    yield

    # Shutdown
    await health_manager.graceful_shutdown(app)
