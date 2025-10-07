import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware as RateLimitMiddleware

from config.settings import Environment, settings
from middleware.api_rate_limiting import APIRateLimitMiddleware
from middleware.error_handling import (
    general_exception_handler,
    http_exception_handler,
    trace_id_middleware,
    validation_exception_handler,
)
from middleware.rate_limiting import limiter
from middleware.request_id import RequestIDMiddleware
from middleware.waf_protection import WAFProtection
from observability.metrics import setup_metrics
from observability.tracing import tracing_service
from observability.dashboards import router as observability_router
from routers.agent import router as agent_router
from routers.ai import router as ai_router
from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.auto_page_seo import router as auto_seo_router
from routers.b2b_commercial import router as b2b_commercial_router
from routers.b2b_partner_portal import b2b_router
from routers.b2b_partner_portal import router as b2b_partner_router
from routers.ceo_marketing_dashboard import router as ceo_dashboard_router
from routers.commercialization import commercialization_router, public_router
from routers.commercialization import router as commercialization_router
from routers.compliance import router as compliance_router
from routers.database import router as database_router
from routers.db_status import router as db_status_router
from routers.devrel import router as devrel_router
from routers.disaster_recovery import router as disaster_recovery_router
from routers.eligibility import router as eligibility_router
from routers.external_billing import router as external_billing_router
from routers.health import router as health_router
from routers.infrastructure_status import router as infrastructure_router
from routers.operations_framework import router as operations_framework_router
from routers.partner_sla_trust_center import partner_sla_router
from routers.partner_sla_trust_center import router as partner_sla_trust_center_router
from routers.priority_3_validation import router as priority3_router
from routers.production_launch import router as launch_router
from routers.recommendations import router as recommendations_router
from routers.replit_health import router as replit_health_router
from routers.scholarship_pages import router as scholarship_pages_router
from routers.scholarships import router as scholarships_router
from routers.search import router as search_router
from routers.week2_acceleration import router as week2_router
from routers.week3_execution import router as week3_router
from routers.week4_global_expansion import router as week4_router
from schemas.error_responses import ERROR_RESPONSES
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Lifespan event handler (FastAPI modern approach)
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events"""
    # Startup - CEO P1 DIRECTIVE: Validate SSL verify-full before proceeding
    from utils.startup_healthcheck import run_startup_healthchecks
    
    logger.info("🏥 Running startup healthchecks (CEO P1 directive)")
    if not run_startup_healthchecks():
        logger.critical("🚨 CRITICAL: Startup healthchecks failed - SSL verify-full not configured")
        raise RuntimeError("Startup healthcheck failure: SSL verify-full validation failed")
    
    from services.orchestrator_service import orchestrator_service

    logger.info("🔗 Initializing Agent Bridge for Command Center integration")

    # Force import scholarship_service to guarantee metrics initialization
    logger.info("🔧 Force importing scholarship_service for metrics initialization")
    from observability.metrics import metrics_service
    from services.scholarship_service import scholarship_service
    scholarship_count = len(scholarship_service.scholarships)
    metrics_service.update_scholarship_count(scholarship_count)
    logger.info(f"🎯 Forced metrics initialization: active_scholarships_total set to {scholarship_count}")

    # Start Command Center registration in background (non-blocking)
    import asyncio

    async def register_with_command_center():
        try:
            await asyncio.wait_for(
                orchestrator_service.register_with_command_center(),
                timeout=5.0
            )
            logger.info("✅ Agent Bridge startup completed")
        except Exception as e:
            logger.warning(f"⚠️ Command Center registration failed (will retry): {e}")

    asyncio.create_task(register_with_command_center())

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

# SEO endpoints - CEO Executive Directive: T+2h gate requirement
@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """Serve robots.txt for search engine crawl directives"""
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    """Serve sitemap.xml for search engine page discovery"""
    return FileResponse("static/sitemap.xml", media_type="application/xml")

# Setup observability FIRST (creates proper registry for metrics to bind to)
tracing_service.setup_tracing()
tracing_service.instrument_app(app)

# Setup metrics AFTER instrumentation (binds to correct registry)
setup_metrics(app)

# Agent Bridge initialization moved to lifespan for reliability

# Defensive startup hook fallback (for environments where lifespan doesn't execute)
@app.on_event("startup")
async def reconcile_metrics():
    """Fallback metrics reconciliation for production reliability"""
    try:
        from observability.metrics import metrics_service
        from services.scholarship_service import scholarship_service
        scholarship_count = len(scholarship_service.scholarships)
        metrics_service.update_scholarship_count(scholarship_count)
        logger.info(f"🔄 Startup hook: Reconciled active_scholarships_total to {scholarship_count}")
    except Exception as e:
        logger.warning(f"Failed startup hook metrics reconciliation: {e}")

# CEO DIRECTIVE: Phase 1 - Route Inventory for /_debug/config RCA
@app.on_event("startup")
async def log_route_inventory():
    """
    Day 0 Security Directive: Log all registered routes to identify /_debug/config source
    Incident ID: DEF-002 | Priority: P0 | Owner: Security Lead
    """
    logger.info("=" * 80)
    logger.info("🔍 ROUTE INVENTORY - Security Audit for DEF-002")
    logger.info("=" * 80)
    
    debug_routes_found = []
    total_routes = 0
    
    for route in app.routes:
        total_routes += 1
        path = getattr(route, "path", "N/A")
        name = getattr(route, "name", "N/A")
        methods = getattr(route, "methods", set())
        
        # Log all routes for audit trail
        logger.info(f"Route: {path} | Methods: {methods} | Name: {name}")
        
        # Flag debug routes for incident investigation
        if "debug" in path.lower():
            debug_routes_found.append({
                "path": path,
                "name": name,
                "methods": methods,
                "endpoint": getattr(route, "endpoint", None)
            })
            logger.critical(f"🚨 DEBUG ROUTE DETECTED: {path} | Name: {name} | Endpoint: {getattr(route, 'endpoint', 'Unknown')}")
    
    logger.info("=" * 80)
    logger.info(f"📊 Total routes registered: {total_routes}")
    logger.info(f"⚠️  Debug routes found: {len(debug_routes_found)}")
    
    if debug_routes_found:
        logger.critical("🔴 SECURITY INCIDENT: Debug routes detected in production!")
        for debug_route in debug_routes_found:
            logger.critical(f"   Path: {debug_route['path']}")
            logger.critical(f"   Name: {debug_route['name']}")
            logger.critical(f"   Endpoint Module: {debug_route['endpoint'].__module__ if debug_route['endpoint'] else 'Unknown'}")
            logger.critical(f"   Endpoint Name: {debug_route['endpoint'].__name__ if debug_route['endpoint'] else 'Unknown'}")
    else:
        logger.info("✅ No debug routes detected in route registry")
    
    logger.info("=" * 80)

# QA-001 fix: Add middleware in correct order (outermost first, applied last)
# Order: CEO Pre-Filter → Security & Host Protection → CORS → Request Processing → Rate Limiting → Routing
from middleware.body_limit import BodySizeLimitMiddleware
from middleware.database_session import DatabaseSessionMiddleware
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.trusted_host import TrustedHostMiddleware
from middleware.url_length import URLLengthMiddleware
from middleware.debug_block_prefilter import DebugPathBlockerMiddleware

# 0. CEO DIRECTIVE DEF-002: Pre-Router Debug Path Blocker (TOP OF STACK - FAIL CLOSED)
# This MUST be first to prevent any routing/mounting bypass scenarios
app.add_middleware(DebugPathBlockerMiddleware)

# 1. Security and host protection middleware (outermost - first line of defense)
# DAY 0 CEO DIRECTIVE: WAF AFTER AUTH (DEF-003 fix - auth middleware must execute before WAF for authenticated routes)
app.add_middleware(SecurityHeadersMiddleware)  # Security headers (must be first)
# CRITICAL FIX: ForwardedHeadersMiddleware breaks route matching on Replit - corrupts ASGI scope paths
app.add_middleware(TrustedHostMiddleware)      # Validate Host header against whitelist
# app.add_middleware(ForwardedHeadersMiddleware) # DISABLED: Breaks routing on Replit proxy
# Temporarily disabled for debugging - suspect it's blocking custom routes
# app.add_middleware(DocsProtectionMiddleware)   # Block docs in production
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

# 4. Request identification and tracing (before error handling)
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(trace_id_middleware)

# 4.5 CRITICAL SECURITY: API Rate Limiting Enforcement
app.add_middleware(APIRateLimitMiddleware)  # Global API rate limiting enforcement

# DEF-003 CEO DIRECTIVE: WAF must execute AFTER authentication (authenticated routes need auth context)
# This prevents WAF from blocking legitimate authenticated requests
app.add_middleware(WAFProtection, enable_block_mode=True)  # WAF with auth context available

# 5. Rate limiting handled by decorators (applied at route level)

# Add rate limiter middleware for proper enforcement
if limiter:
    app.state.limiter = limiter
    app.add_middleware(RateLimitMiddleware)
else:
    print("⚠️ Rate limiter not configured")

# 6. HTTP Metrics (AFTER authentication/authorization middleware)
# This ensures HTTP errors are properly recorded but not converted to 500s
from middleware.http_metrics import HTTPMetricsMiddleware
app.add_middleware(HTTPMetricsMiddleware, enable_metrics=True)

# Global exception handlers with unified error format
from middleware.error_handlers import (
    general_exception_handler,
    http_exception_handler,
    method_not_allowed_handler,
    not_found_handler,
    validation_exception_handler,
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
    # Try APIError handler first
    from middleware.error_handlers import api_error_handler
    from middleware.error_handling import APIError
    
    if isinstance(exc, APIError):
        return await api_error_handler(request, exc)
    
    # Fall back to general exception handler
    return await general_exception_handler(request, exc)

# Specific status code handlers - ENABLED FOR UNIFIED ERROR SCHEMA
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
app.include_router(priority3_router, tags=["Priority 3 Production Validation"])
app.include_router(launch_router, tags=["Production Launch"])
app.include_router(agent_router, tags=["agent"])  # Agent Bridge for Command Center integration

# Agent Bridge / Orchestration endpoint for Command Center
from routers.orchestration import router as orchestration_router
app.include_router(orchestration_router, tags=["orchestration"])

# QA-003 fix: Include interaction wrapper endpoints
from routers.interaction_wrapper import router as interaction_wrapper_router

app.include_router(interaction_wrapper_router, tags=["interactions"])

# AI Scholarship Playbook: Magic Onboarding endpoints
from routers.onboarding import router as onboarding_router

app.include_router(onboarding_router, tags=["Magic Onboarding"])

# AI Scholarship Playbook: Monetization endpoints (Credit System)
from routers.monetization import router as monetization_router

app.include_router(external_billing_router, tags=["External Billing"])
app.include_router(monetization_router, tags=["Monetization"])

# AI Scholarship Playbook: B2B Partner Portal endpoints
app.include_router(b2b_partner_router, tags=["B2B Partners"])
app.include_router(b2b_commercial_router, tags=["B2B Commercial"])
app.include_router(partner_sla_trust_center_router, tags=["Partner SLA & Trust Center"])

# CRITICAL: Missing B2B routes that were causing 404 errors
app.include_router(b2b_router, tags=["B2B Partners - Providers"])
app.include_router(commercialization_router, tags=["Commercialization Status"])
app.include_router(partner_sla_router, tags=["Partner SLA Status"])

# B2B COMMERCIAL EXECUTION ENGINE: Operations Framework (Lead Routing, Pipeline, Sales Enablement)
app.include_router(operations_framework_router, tags=["Operations Framework"])

# CRITICAL SECURITY: API Commercialization & Billing System
app.include_router(commercialization_router, tags=["API Commercialization"])
app.include_router(devrel_router, tags=["Developer Relations"])
app.include_router(auto_seo_router, tags=["Auto SEO Pages"])
app.include_router(scholarship_pages_router, tags=["Canonical Scholarship Pages"])
app.include_router(public_router, tags=["Public Status"])  # Status page and docs

# Observability dashboards for monitoring
app.include_router(observability_router, tags=["Observability"])

# Metrics already setup above - this was the wrong location causing route shadowing

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
            "documentation": "/docs"
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

# DEF-002 SECURITY FIX: Debug endpoint removed per CEO directive (Day 0 Priority #1)
# Exposed JWT secret length, database config, and internal architecture
# All exposed secrets must be rotated immediately

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
    logger.info("Database: PostgreSQL")

    uvicorn.run(
        app,  # Run app object directly to avoid double-import
        host=host,
        port=port,  # Use dynamic port from environment
        reload=False,  # Hard disable to ensure single-process
        workers=1,  # Force single process for shared metrics registry
        log_level="info",
        access_log=True,
        proxy_headers=False,  # CRITICAL FIX: Disable to prevent ASGI scope corruption on Replit
        # forwarded_allow_ips removed - was security risk and breaking routing
        lifespan='on'  # Force lifespan execution
    )
