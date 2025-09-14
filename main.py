from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware as RateLimitMiddleware
import uvicorn
import os

from routers.scholarships import router as scholarships_router
from routers.search import router as search_router
from routers.eligibility import router as eligibility_router
from routers.recommendations import router as recommendations_router
from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.database import router as database_router
from routers.health import router as health_router
from routers.ai import router as ai_router
from routers.db_status import router as db_status_router
from routers.replit_health import router as replit_health_router
from routers.agent import router as agent_router
from routers.week2_acceleration import router as week2_router
from routers.week3_execution import router as week3_router
from routers.week4_global_expansion import router as week4_router
from routers.disaster_recovery import router as disaster_recovery_router
from routers.compliance import router as compliance_router
from routers.ceo_marketing_dashboard import router as ceo_dashboard_router
from routers.infrastructure_status import router as infrastructure_router
from middleware.error_handling import (
    api_error_handler, http_exception_handler, validation_exception_handler,
    rate_limit_exception_handler, general_exception_handler, trace_id_middleware,
    APIError
)
from middleware.rate_limiting import limiter
from middleware.request_id import RequestIDMiddleware
from middleware.waf_protection import WAFProtection
from observability.metrics import setup_metrics
from observability.tracing import tracing_service
from config.settings import settings, Environment
from schemas.error_responses import ERROR_RESPONSES
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Lifespan event handler (FastAPI modern approach)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events"""
    # Startup
    from services.orchestrator_service import orchestrator_service
    
    logger.info("🔗 Initializing Agent Bridge for Command Center integration")
    
    # Register with Command Center on startup
    try:
        await orchestrator_service.register_with_command_center()
        logger.info("✅ Agent Bridge startup completed")
    except Exception as e:
        logger.warning(f"⚠️ Command Center registration failed (will retry): {e}")
    
    # Startup reconciliation: Set active scholarships metric in each worker
    try:
        from services.scholarship_service import scholarship_service
        from observability.metrics import metrics_service
        scholarship_count = len(scholarship_service.scholarships)
        metrics_service.update_scholarship_count(scholarship_count)
        logger.info(f"🎯 Startup reconciliation: active_scholarships_total set to {scholarship_count}")
    except Exception as e:
        logger.warning(f"Failed startup metrics reconciliation: {e}")
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down Agent Bridge")
    await orchestrator_service.close()

# Create FastAPI app with production-aware docs configuration
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs" if settings.should_enable_docs else None,
    redoc_url="/redoc" if settings.should_enable_docs else None,
    debug=settings.debug,
    lifespan=lifespan,
    responses={
        status: {"model": resp["model"], "description": resp["description"]}
        for status, resp in ERROR_RESPONSES.items()
    }
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup observability
setup_metrics(app)
tracing_service.setup_tracing()
tracing_service.instrument_app(app)

# QA-001 fix: Add middleware in correct order (outermost first, applied last)
# Order: Security & Host Protection → CORS → Request Processing → Rate Limiting → Routing
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.body_limit import BodySizeLimitMiddleware
from middleware.url_length import URLLengthMiddleware
from middleware.trusted_host import TrustedHostMiddleware
from middleware.forwarded_headers import ForwardedHeadersMiddleware
from middleware.docs_protection import DocsProtectionMiddleware
from middleware.database_session import DatabaseSessionMiddleware

# 1. Security and host protection middleware (outermost - first line of defense)
app.add_middleware(WAFProtection, enable_block_mode=True)  # WAF - FIRST LINE OF DEFENSE
app.add_middleware(SecurityHeadersMiddleware)  # Security headers (must be first)
app.add_middleware(TrustedHostMiddleware)      # Validate Host header against whitelist
app.add_middleware(ForwardedHeadersMiddleware) # Handle X-Forwarded-* headers safely
app.add_middleware(DocsProtectionMiddleware)   # Block docs in production
app.add_middleware(DatabaseSessionMiddleware)  # Database lifecycle management

# 2. CORS (must be early to handle preflight requests) - Replit compatible
cors_config = settings.get_cors_config
cors_origins = cors_config["allow_origins"]

# Log CORS configuration for Replit debugging
logger.info(f"CORS origins configured: {len(cors_origins) if cors_origins != ['*'] else 'wildcard'} origins")
if settings.is_development and "*" in cors_origins:
    logger.info("Development mode: CORS wildcard enabled for Replit compatibility")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_config["allow_credentials"], 
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
    max_age=cors_config["max_age"]
)

# 3. Request validation (check request before processing)
app.add_middleware(URLLengthMiddleware, max_length=settings.max_url_length)
app.add_middleware(BodySizeLimitMiddleware, max_size=settings.max_request_size_bytes)

# 4. Request identification (for tracing/logging)
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(trace_id_middleware)

# 5. Rate limiting handled by decorators (applied at route level)

# Add rate limiter middleware for proper enforcement
if limiter:
    app.state.limiter = limiter
    app.add_middleware(RateLimitMiddleware)
else:
    print("⚠️ Rate limiter not configured")

# Global exception handlers with unified error format
from middleware.error_handlers import (
    http_exception_handler, validation_exception_handler,
    rate_limit_exception_handler, general_exception_handler,
    not_found_handler, method_not_allowed_handler
)

# Unified error handlers (all return standardized format)
@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit_error(request: Request, exc: RateLimitExceeded):
    # Import the updated rate limit handler
    from middleware.rate_limiting import rate_limit_handler
    return await rate_limit_handler(request, exc)

@app.exception_handler(Exception)
async def handle_general_error(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)

# Specific status code handlers
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

# Recommendations endpoint
app.include_router(recommendations_router, tags=["recommendations"])

app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(database_router, tags=["database"])
app.include_router(health_router)
app.include_router(replit_health_router, tags=["health"])
app.include_router(ai_router, tags=["ai"])
app.include_router(db_status_router)
app.include_router(week2_router, tags=["Week 2 Acceleration"])
app.include_router(week3_router, tags=["Week 3 Execution"])
app.include_router(week4_router, tags=["Week 4 Global Expansion"])
app.include_router(disaster_recovery_router, tags=["Disaster Recovery"])
app.include_router(compliance_router, tags=["SOC2 Compliance"])
app.include_router(ceo_dashboard_router, tags=["CEO/Marketing Dashboard"])
app.include_router(infrastructure_router, tags=["Infrastructure Status"])
app.include_router(agent_router, tags=["agent"])  # Agent Bridge for Command Center integration

# QA-003 fix: Include interaction wrapper endpoints  
from routers.interaction_wrapper import router as interaction_wrapper_router
app.include_router(interaction_wrapper_router, tags=["interactions"])

# AI Scholarship Playbook: Magic Onboarding endpoints
from routers.onboarding import router as onboarding_router
app.include_router(onboarding_router, tags=["Magic Onboarding"])

# AI Scholarship Playbook: Monetization endpoints (Credit System)
from routers.monetization import router as monetization_router
app.include_router(monetization_router, tags=["Monetization"])

# AI Scholarship Playbook: B2B Partner Portal endpoints
from routers.b2b_partner import router as b2b_partner_router
app.include_router(b2b_partner_router, tags=["B2B Partners"])

@app.get("/")
async def root():
    """Root endpoint with helpful API information"""
    return {
        "status": "active",
        "message": "Scholarship Discovery & Search API",
        "version": settings.api_version,
        "endpoints": {
            "health": "/healthz",
            "api_info": "/api", 
            "search": "/api/v1/search?q=<query>",
            "documentation": "/docs",
            "debug": "/_debug/config"
        },
        "example": "Try: /api/v1/search?q=engineering"
    }

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
async def health_check(request: Request):
    """Health check endpoint - fast response for deployment monitoring"""
    from utils.error_utils import get_trace_id
    return {
        "status": "healthy",
        "trace_id": get_trace_id(request)
    }

@app.get("/healthz")
@app.head("/healthz")
async def kubernetes_health_check():
    """Kubernetes/deployment-style health check endpoint - minimal dependencies"""
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

@app.get("/_debug/config")
async def debug_config():
    """Development-only debug endpoint showing sanitized runtime configuration"""
    if settings.environment == Environment.PRODUCTION:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "environment": settings.environment.value,
        "host": settings.host,
        "port": settings.port,
        "cors_mode": "wildcard" if settings.environment != Environment.PRODUCTION else "strict",
        "rate_limiter": {
            "enabled": settings.rate_limit_enabled,
            "backend_type": "redis" if not settings.disable_rate_limit_backend else "memory",
            "per_minute": settings.get_rate_limit_per_minute
        },
        "database": {
            "engine": "PostgreSQL",
            "configured": bool(settings.database_url)
        },
        "security": {
            "jwt_configured": bool(settings.jwt_secret_key),
            "docs_enabled": settings.should_enable_docs,
            "public_read_endpoints": settings.public_read_endpoints
        },
        "middleware_order": [
            "SecurityHeaders", "TrustedHost", "ForwardedHeaders", 
            "DocsProtection", "DatabaseSession", "RequestID", 
            "CORS", "URLLength", "BodySize", "RateLimit"
        ]
    }

if __name__ == "__main__":
    # Replit-specific port handling - must use PORT environment variable
    port = int(os.getenv("PORT", "5000"))  # Replit sets PORT=5000 in workflows
    host = "0.0.0.0"  # Required for Replit accessibility
    
    # Startup logging for Replit diagnostics
    logger.info("🚀 Starting Scholarship Discovery API server")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Host/Port: {host}:{port}")
    logger.info(f"CORS mode: {'dev (wildcard)' if settings.environment != Environment.PRODUCTION else 'prod (strict whitelist)'}")
    logger.info(f"Rate limiter: {'Redis' if limiter and hasattr(limiter, 'storage') and 'redis' in str(limiter.storage) else 'in-memory fallback (Redis unavailable)'}")
    logger.info(f"Database: PostgreSQL")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,  # Use dynamic port from environment
        reload=settings.reload,
        log_level="info",
        access_log=True,
        proxy_headers=True,  # Handle X-Forwarded-* headers correctly for Replit
        forwarded_allow_ips="*"  # Replit proxy requirement
    )