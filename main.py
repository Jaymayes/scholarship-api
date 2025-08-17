from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
import uvicorn

from routers.scholarships import router as scholarships_router
from routers.search import router as search_router
from routers.eligibility import router as eligibility_router
from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.database import router as database_router
from routers.health import router as health_router
from middleware.error_handling import (
    api_error_handler, http_exception_handler, validation_exception_handler,
    rate_limit_exception_handler, general_exception_handler, trace_id_middleware,
    APIError
)
from middleware.rate_limiting import limiter, set_rate_limit_context
from middleware.request_id import RequestIDMiddleware
from observability.metrics import setup_metrics
from observability.tracing import tracing_service
from config.settings import settings
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Create FastAPI app with settings
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

# Setup observability
setup_metrics(app)
tracing_service.setup_tracing()
tracing_service.instrument_app(app)

# Add middleware in correct order (middleware wraps the app)
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(trace_id_middleware)
app.middleware("http")(set_rate_limit_context)

# Add CORS middleware with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add rate limiter
app.state.limiter = limiter

# Exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth_router)
app.include_router(scholarships_router, prefix="/api/v1", tags=["scholarships"])

# Search endpoints - available at both root and /api/v1 for backward compatibility
app.include_router(search_router, tags=["search"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])

# Eligibility endpoints - available at both root and /api/v1 for backward compatibility
app.include_router(eligibility_router, tags=["eligibility"])
app.include_router(eligibility_router, prefix="/api/v1", tags=["eligibility"])

app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(database_router, tags=["database"])
app.include_router(health_router)

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Scholarship Discovery & Search API",
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": "/docs",
        "status": "active",
        "authentication": "JWT Bearer tokens required for protected endpoints"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "environment": settings.environment
    }

@app.get("/readiness")
async def readiness_check():
    """Readiness check endpoint for deployment"""
    # Add database connectivity checks here when implemented
    return {
        "status": "ready",
        "services": {
            "api": "ready",
            "database": "ready" if settings.database_url else "not_configured",
            "redis": "ready" if settings.redis_url else "not_configured"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Scholarship Discovery API server")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )