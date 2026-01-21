"""
DataService V2 Sprint-2
FastAPI application for data management with FERPA compliance
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import get_db, SessionLocal, Base, engine

from .routers import (
    users_router,
    providers_router,
    uploads_router,
    ledgers_router,
)
from .models import (
    DataServiceUser,
    DataServiceProvider,
    DataServiceUpload,
    DataServiceLedger,
    DataServiceLedgerEntry,
    DataServiceEvent,
)


VERSION = "2.0.0-sprint2"
SERVICE_NAME = "dataservice"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    timestamp: str
    details: Optional[dict] = None


def create_dataservice_app() -> FastAPI:
    """Factory function to create the DataService FastAPI app"""
    
    app = FastAPI(
        title="DataService V2 API",
        description="Data management service with FERPA compliance for scholarship platform",
        version=VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        allowed_origins = [
            "https://scholaraiadvisor.com",
            "https://www.scholaraiadvisor.com",
            "https://scholarship-api-jamarrlmayes.replit.app",
            "https://scholar-auth-jamarrlmayes.replit.app",
            "https://provider-register-jamarrlmayes.replit.app",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Idempotency-Key", "X-Trace-Id", "X-User-Role", "X-API-Key"],
    )
    
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(providers_router, prefix="/api/v1")
    app.include_router(uploads_router, prefix="/api/v1")
    app.include_router(ledgers_router, prefix="/api/v1")
    
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        """
        Fast health check endpoint - no database connection required.
        Used by load balancers for basic service availability.
        """
        return HealthResponse(
            status="healthy",
            service=SERVICE_NAME,
            version=VERSION,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    @app.get("/readyz", response_model=ReadinessResponse, tags=["health"])
    async def readiness_check(db: Session = Depends(get_db)):
        """
        Readiness check endpoint - includes database connectivity test.
        Used by orchestrators to verify full service readiness.
        """
        db_status = "unknown"
        details = {}
        
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            db_status = "connected"
            
            user_count = db.query(DataServiceUser).count()
            provider_count = db.query(DataServiceProvider).count()
            upload_count = db.query(DataServiceUpload).count()
            ledger_count = db.query(DataServiceLedger).count()
            
            details = {
                "users": user_count,
                "providers": provider_count,
                "uploads": upload_count,
                "ledgers": ledger_count,
            }
            
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"
            return ReadinessResponse(
                status="unhealthy",
                service=SERVICE_NAME,
                version=VERSION,
                database=db_status,
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)[:200]},
            )
        
        return ReadinessResponse(
            status="ready",
            service=SERVICE_NAME,
            version=VERSION,
            database=db_status,
            timestamp=datetime.utcnow().isoformat(),
            details=details,
        )
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with service information"""
        return {
            "service": SERVICE_NAME,
            "version": VERSION,
            "description": "DataService V2 API - FERPA compliant data management",
            "docs": "/docs",
            "health": "/health",
            "readiness": "/readyz",
        }
    
    return app


def create_tables():
    """Create all DataService tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_dataservice_router():
    """Get the DataService as a router for mounting in parent app"""
    from fastapi import APIRouter
    
    router = APIRouter()
    
    @router.get("/health", response_model=HealthResponse, tags=["dataservice-health"])
    async def health_check():
        return HealthResponse(
            status="healthy",
            service=SERVICE_NAME,
            version=VERSION,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    @router.get("/readyz", response_model=ReadinessResponse, tags=["dataservice-health"])
    async def readiness_check(db: Session = Depends(get_db)):
        db_status = "unknown"
        
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"database": db_status}
            )
        
        return ReadinessResponse(
            status="ready",
            service=SERVICE_NAME,
            version=VERSION,
            database=db_status,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    router.include_router(users_router, prefix="/api/v1")
    router.include_router(providers_router, prefix="/api/v1")
    router.include_router(uploads_router, prefix="/api/v1")
    router.include_router(ledgers_router, prefix="/api/v1")
    
    return router


app = create_dataservice_app()


__all__ = [
    "app",
    "create_dataservice_app",
    "get_dataservice_router",
    "create_tables",
    "VERSION",
    "SERVICE_NAME",
    "HealthResponse",
    "ReadinessResponse",
]
