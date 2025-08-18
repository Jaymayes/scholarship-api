from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from slowapi.errors import RateLimitExceeded
import uvicorn

from routers.scholarships import router as scholarships_router
from routers.search import router as search_router
from routers.eligibility import router as eligibility_router
from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.database import router as database_router
from routers.health import router as health_router
from routers.ai import router as ai_router
from routers.db_status import router as db_status_router
from middleware.error_handling import (
    api_error_handler, http_exception_handler, validation_exception_handler,
    rate_limit_exception_handler, general_exception_handler, trace_id_middleware,
    APIError
)
from middleware.rate_limiting import limiter
from middleware.request_id import RequestIDMiddleware
from observability.metrics import setup_metrics
from observability.tracing import tracing_service
from config.settings import settings, Environment
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup observability
setup_metrics(app)
tracing_service.setup_tracing()
tracing_service.instrument_app(app)

# Add middleware in correct order (middleware wraps the app)
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.body_limit import BodySizeLimitMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_size=settings.max_request_body_bytes)
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(trace_id_middleware)
# Rate limiting middleware handled by decorators

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

# Exception handlers - using proper type annotations for FastAPI
@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    return await api_error_handler(request, exc)

@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit_error(request: Request, exc: RateLimitExceeded):
    return await rate_limit_exception_handler(request, exc)

@app.exception_handler(Exception)
async def handle_general_error(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)

# Additional handlers for standardized error format
from middleware.error_handlers import not_found_handler, method_not_allowed_handler

@app.exception_handler(404)
async def handle_not_found(request: Request, exc: HTTPException):
    return await not_found_handler(request, exc)

@app.exception_handler(405)
async def handle_method_not_allowed(request: Request, exc: HTTPException):
    return await method_not_allowed_handler(request, exc)

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
app.include_router(ai_router, tags=["ai"])
app.include_router(db_status_router)

@app.get("/")
async def root():
    """Root endpoint optimized for deployment health checks"""
    return {"status": "active"}

@app.head("/")
async def root_head():
    """HEAD method for root endpoint health checks"""
    return {"status": "active"}

@app.get("/api")
async def api_status():
    """Alternative API status endpoint with more detailed information"""
    return {
        "api": "Scholarship Discovery & Search API",
        "version": settings.api_version,
        "status": "running",
        "environment": settings.environment.value,
        "endpoints": {
            "documentation": "/docs",
            "health": "/health",
            "search": "/search",
            "scholarships": "/api/v1/scholarships",
            "eligibility": "/eligibility/check"
        },
        "features": ["search", "eligibility", "ai", "analytics"]
    }

@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint - fast response for deployment monitoring"""
    return {"status": "healthy"}

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors in browser requests"""
    return {"status": "no favicon"}

@app.get("/status")
async def json_status():
    """JSON status endpoint for deployment monitoring and API consumers"""
    return {
        "status": "active",
        "message": "Scholarship Discovery & Search API",
        "version": settings.api_version,
        "environment": settings.environment.value,
        "docs": "/docs"
    }

@app.get("/readiness")
async def readiness_check():
    """Readiness check endpoint for deployment"""
    return {
        "status": "ready",
        "services": {
            "api": "ready"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Scholarship Discovery API server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Explicit host binding for deployment
        port=5000,       # Explicit port for deployment
        reload=settings.reload if settings.is_development else False,
        log_level=settings.log_level.lower(),
        access_log=True,
        workers=1 if settings.environment in [Environment.LOCAL, Environment.DEVELOPMENT] else 1  # Single worker for deployment simplicity
    )