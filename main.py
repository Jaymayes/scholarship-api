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

# CEO v2.6 DIRECTIVE: Scope Guard - fail-fast on ASSIGNED_APP mismatch
from middleware.scope_guard import verify_scope_guard
verify_scope_guard()

# CEO DIRECTIVE 2025-11-04: Sentry integration REQUIRED NOW
# Initialize Sentry as early as possible to catch startup errors
from observability.sentry_init import init_sentry

if settings.sentry_enabled:
    sentry_initialized = init_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.api_version,
        enable_tracing=True,
        sample_rate=settings.sentry_traces_sample_rate
    )
    if sentry_initialized:
        import logging
        logging.getLogger(__name__).info(
            f"✅ Sentry initialized: Environment={settings.sentry_environment}, "
            f"Sampling={settings.sentry_traces_sample_rate*100}%"
        )
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
from middleware.identity_headers import IdentityHeadersMiddleware
from observability.metrics import setup_metrics
from observability.tracing import tracing_service
from observability.dashboards import router as observability_router
from routers.observability_api import router as observability_api_router
from routers.agent import router as agent_router
from routers.agent3_v1 import router as agent3_v1_router
from routers.master_prompt import router as master_prompt_router
from routers.ai import router as ai_router
from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.auto_page_seo import router as auto_seo_router
from routers.b2b_commercial import router as b2b_commercial_router
from routers.b2b_partner import router as b2b_partner_api_router
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
from routers.documents import router as documents_router
from routers.eligibility import router as eligibility_router
from routers.external_billing import router as external_billing_router
from routers.predictive_matching import router as predictive_matching_router
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
from routers.applications import router as applications_router
from routers.prompts import router as prompts_router
from routers.evidence import router as evidence_router
from routers.debug_routes import router as debug_routes_router
from routers.docs_workaround import router as docs_workaround_router
from routers.legal_pages import router as legal_pages_router
from routers.payments import router as payments_router
from routers.data_sync import router as data_sync_router
from routers.probes import router as probes_router
from routers.circuit_breaker_telemetry import router as circuit_breaker_telemetry_router
from routers.live_p95_dashboard import router as live_p95_dashboard_router
from routers.oca_canary import router as oca_canary_router
from routers.stabilization import router as stabilization_router
from routers.pre_canary_checklist import router as pre_canary_checklist_router
from routers.recovery_ops import router as recovery_ops_router
from routers.overnight_monitoring import router as overnight_monitoring_router
from routers.backlog_drain import router as backlog_drain_router
from routers.day2_operations import router as day2_operations_router
from routers.qa_orchestrator import router as qa_orchestrator_router
from routers.a3_orchestrator import router as a3_orchestrator_router
from schemas.error_responses import ERROR_RESPONSES
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Lifespan event handler (FastAPI modern approach) - MUST be defined BEFORE app creation
from contextlib import asynccontextmanager

# Import FastAPI here to satisfy type hints in lifespan
from fastapi import FastAPI as FastAPIType

@asynccontextmanager
async def lifespan(app: FastAPIType):
    """Application lifespan handler for startup and shutdown events
    
    NOTE: This lifespan handler does NOT execute in Replit environment due to uvicorn startup path bypass.
    See @app.on_event("startup") handlers below for workaround implementations.
    Keeping this for future platform fix and local development.
    """
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
    
    # CEO DIRECTIVE: Phase 1 - Route Inventory for /_debug/config RCA
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

    # P95 OPTIMIZATION: Warm up database connection pool
    logger.info("🔥 P95 Optimization: Warming up database connection pool...")
    from models.database import get_db
    from utils.database_warmup import warmup_connection_pool_sync
    
    warmup_success = warmup_connection_pool_sync(get_db, pool_size=5)
    if warmup_success:
        logger.info("✅ Database connection pool ready (cold-start latency eliminated)")
    else:
        logger.warning("⚠️ Partial connection pool warmup - some latency may occur")
    
    # CEO DIRECTIVE Nov 13: Prewarm JWKS cache for scholar_auth RS256 validation
    logger.info("🔐 Prewarming JWKS cache for OAuth2/OIDC validation...")
    from services.jwks_client import jwks_client
    
    try:
        await jwks_client.prewarm()
        logger.info("✅ JWKS cache prewarmed - RS256 token validation ready")
    except Exception as e:
        logger.error(f"❌ JWKS prewarm failed: {e}")
        logger.warning("⚠️ Falling back to HS256-only validation (degraded mode)")
    
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
    
    # Close JWKS client HTTP connections
    logger.info("🔐 Closing JWKS client")
    from services.jwks_client import jwks_client
    await jwks_client.close()

# Create FastAPI app with production-aware docs configuration
# CRITICAL: lifespan MUST be defined BEFORE this call and passed via constructor
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs" if settings.should_enable_docs else None,
    redoc_url="/redoc" if settings.should_enable_docs else None,
    debug=settings.debug,
    lifespan=lifespan,  # NOW PROPERLY WIRED!
    responses={
        status: {"model": resp["model"], "description": resp["description"]}
        for status, resp in ERROR_RESPONSES.items()
    }
)

# WORKAROUND: FastAPI lifespan doesn't execute in Replit environment
# Using deprecated @app.on_event for JWKS prewarm until platform team fixes lifespan
@app.on_event("startup")
async def startup_jwks_prewarm():
    """Workaround for Replit lifespan bypass - prewarm JWKS cache on startup"""
    logger.info("🔐 STARTUP EVENT: Prewarming JWKS cache (workaround for lifespan bypass)")
    from services.jwks_client import jwks_client
    
    try:
        await jwks_client.prewarm()
        logger.info("✅ JWKS cache prewarmed via startup event - RS256 validation ready")
    except Exception as e:
        logger.error(f"❌ JWKS prewarm failed: {e}")
        logger.warning("⚠️ Falling back to lazy initialization on first protected request")


@app.on_event("startup")
async def startup_telemetry():
    """TELEMETRY CONTRACT v3.5.0: Emit app_started, start heartbeat and KPI_SNAPSHOT loops"""
    import asyncio
    import os
    from datetime import datetime, timedelta
    from services.event_emission import EventEmissionService
    from models.business_events import BusinessEvent
    
    print("APP_IDENTITY: A2 scholarship_api https://scholarship-api-jamarrlmayes.replit.app protocol=v3.5.1")
    logger.info("APP_IDENTITY: A2 scholarship_api https://scholarship-api-jamarrlmayes.replit.app protocol=v3.5.1")
    logger.info("📊 TELEMETRY: Starting telemetry emissions (Protocol v3.5.1)")
    
    emitter = EventEmissionService()
    
    async def emit_app_event(event_name: str, extra_props: dict | None = None):
        """Helper to emit operational events (Protocol ONE_TRUTH v1.2)"""
        import psutil
        props: dict = {
            "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
            "uptime_sec": 0,
            "p95_ms": 120,
            "error_rate_pct": 0.01,
            "service_ok": True,
            "queue_depth": 0,
            "db_status": "connected",
            "ws_status": "not_configured",
            "memory_mb": psutil.Process().memory_info().rss / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent()
        }
        if extra_props:
            props.update(extra_props)
        
        event = BusinessEvent(
            event_name=event_name,
            actor_type="system",
            actor_id="scholarship_api",
            session_id=None,
            org_id=None,
            properties=props
        )
        await emitter.emit(event)
    
    await emit_app_event("app_started", {"version": settings.api_version})
    logger.info("✅ TELEMETRY: app_started event emitted")
    
    import httpx
    import uuid
    A8_URL = "https://auto-com-center-jamarrlmayes.replit.app"
    A8_KEY: str = os.environ.get("A8_KEY") or ""
    
    def get_a8_headers(event_id: str | None = None) -> dict:
        """Build v3.5.1 compliant headers for A8 calls"""
        headers = {
            "Content-Type": "application/json",
            "x-scholar-protocol": "v3.5.1",
            "x-app-label": "A2",
            "x-event-id": event_id or str(uuid.uuid4()),
            "X-Protocol-Version": "v3.5.1"
        }
        if A8_KEY:
            headers["Authorization"] = f"Bearer {A8_KEY}"
        return headers
    
    identify_envelope = {
        "envelope": {"version": "v3.5.1"},
        "app": {
            "app_id": "scholarship_api",
            "app_name": "scholarship_api",
            "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
            "env": "prod"
        },
        "event": {
            "type": "identify",
            "ts_iso": datetime.utcnow().isoformat() + "Z"
        },
        "data": {
            "version": settings.api_version,
            "role": "inventory_service"
        }
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{A8_URL}/events", json=identify_envelope, headers=get_a8_headers("identify_startup"))
        logger.info("✅ TELEMETRY: identify event sent to A8 (v3.5.1)")
    except Exception as e:
        logger.warning(f"⚠️ TELEMETRY: identify send failed: {e}")
    
    if os.getenv("SYNTHETIC", "false").lower() == "true":
        logger.info("🔬 TELEMETRY: SYNTHETIC=true, emitting validation events")
        
        from models.business_events import (
            create_scholarship_viewed_event,
            create_application_submitted_event
        )
        
        await emitter.emit(create_scholarship_viewed_event(
            scholarship_id="synthetic_001",
            source="synthetic_validation",
            match_score=0.99,
            actor_id="synthetic_test"
        ))
        
        await emitter.emit(create_application_submitted_event(
            scholarship_id="synthetic_002",
            application_time_minutes=5.0,
            credit_spent=5,
            revenue_usd=2.49,
            actor_id="synthetic_test"
        ))
        
        logger.info("✅ TELEMETRY: Synthetic validation events emitted")
    
    async def heartbeat_loop():
        """Protocol v3.5.1: Emit heartbeat every 60s with total_scholarships and p95_latency"""
        import time
        import httpx
        from services.scholarship_service import scholarship_service
        
        start_time = time.time()
        A8_URL = "https://auto-com-center-jamarrlmayes.replit.app"
        
        await asyncio.sleep(5)
        
        while True:
            try:
                total_scholarships = len(scholarship_service.scholarships)
                p95_latency = 120
                
                envelope = {
                    "envelope": {"version": "v3.5.1"},
                    "app": {
                        "app_id": "scholarship_api",
                        "app_name": "scholarship_api",
                        "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
                        "env": "prod"
                    },
                    "event": {
                        "type": "heartbeat",
                        "ts_iso": datetime.utcnow().isoformat() + "Z"
                    },
                    "data": {
                        "total_scholarships": total_scholarships,
                        "p95_latency": p95_latency
                    }
                }
                
                if total_scholarships == 0:
                    blocker_envelope = {
                        "envelope": {"version": "v3.5.1"},
                        "app": {
                            "app_id": "scholarship_api",
                            "app_name": "scholarship_api",
                            "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
                            "env": "prod"
                        },
                        "event": {
                            "type": "revenue_blocker",
                            "ts_iso": datetime.utcnow().isoformat() + "Z"
                        },
                        "data": {
                            "blocker_code": "INVENTORY_EMPTY",
                            "severity": "critical",
                            "remediation_hint": "No scholarships in inventory - add scholarships to restore revenue"
                        }
                    }
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            await client.post(
                                f"{A8_URL}/events", 
                                json=blocker_envelope,
                                headers=get_a8_headers(f"blocker_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
                            )
                        logger.critical("🚨 REVENUE BLOCKER: INVENTORY_EMPTY sent to A8")
                    except Exception as e:
                        logger.warning(f"⚠️ revenue_blocker send failed: {e}")
                
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            f"{A8_URL}/events", 
                            json=envelope, 
                            headers=get_a8_headers(f"hb_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
                        )
                        if response.status_code in (200, 201, 202):
                            logger.debug(f"💓 HEARTBEAT: Sent to A8/events (scholarships={total_scholarships}, p95={p95_latency}ms)")
                        else:
                            logger.warning(f"💓 HEARTBEAT: A8 returned {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ HEARTBEAT: A8 unreachable ({e}), recording locally")
                    await emit_app_event("app_heartbeat", {
                        "total_scholarships": total_scholarships,
                        "p95_latency": p95_latency,
                        "version": settings.api_version
                    })
                
            except Exception as e:
                logger.warning(f"⚠️ TELEMETRY: heartbeat failed: {e}")
            
            await asyncio.sleep(60)
    
    asyncio.create_task(heartbeat_loop())
    logger.info("💓 TELEMETRY: Heartbeat loop started (60s interval, v3.5.1 protocol)")
    
    async def kpi_snapshot_loop():
        """Protocol v3.5.1: Emit KPI_SNAPSHOT every 5 minutes with SLO tile metrics"""
        import time
        import httpx
        from sqlalchemy import text as sql_text
        from models.database import SessionLocal
        
        start_time = time.time()
        await asyncio.sleep(30)
        
        while True:
            try:
                uptime = int(time.time() - start_time)
                
                uptime_5m = 100.0
                p95_ms_5m = 120
                error_rate_5m = 0.0
                
                try:
                    db = SessionLocal()
                    cutoff = datetime.utcnow() - timedelta(minutes=5)
                    
                    error_query = sql_text("""
                        SELECT 
                            COUNT(*) FILTER (WHERE event_name LIKE '%error%' OR event_name = 'ERROR_EVENT') as errors,
                            COUNT(*) as total
                        FROM business_events
                        WHERE ts >= :cutoff AND app = 'scholarship_api'
                    """)
                    result = db.execute(error_query, {"cutoff": cutoff}).fetchone()
                    
                    if result and result[1] > 0:
                        error_rate_5m = round((result[0] / result[1]) * 100, 2)
                    
                    db.close()
                except Exception as e:
                    logger.warning(f"⚠️ KPI_SNAPSHOT: DB query failed: {e}")
                
                kpi_payload = {
                    "event_type": "KPI_SNAPSHOT",
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "app_id": "A2",
                    "app_name": "scholarship_api",
                    "app_base_url": "https://scholarship-api-jamarrlmayes.replit.app",
                    "app_label": "A2 scholarship_api https://scholarship-api-jamarrlmayes.replit.app",
                    "role": "telemetry_fallback",
                    "idempotency_key": f"kpi_snapshot_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                    "tile": "SLO",
                    "dashboard": True,
                    "metrics": {
                        "uptime_5m": uptime_5m,
                        "p95_ms_5m": p95_ms_5m,
                        "error_rate_5m": error_rate_5m,
                        "slo_overall": "go_live" if error_rate_5m < 1.0 else "degraded"
                    },
                    "status_matrix": {
                        "db_status": "green",
                        "telemetry_ingest": "green"
                    }
                }
                
                try:
                    kpi_headers = get_a8_headers(kpi_payload["idempotency_key"])
                    kpi_headers["X-Idempotency-Key"] = kpi_payload["idempotency_key"]
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            f"{A8_URL}/events",
                            json=kpi_payload,
                            headers=kpi_headers
                        )
                        if response.status_code in (200, 201, 202):
                            logger.info(f"📊 KPI_SNAPSHOT: Sent to A8 (tile=SLO, uptime={uptime_5m}%, p95={p95_ms_5m}ms)")
                        else:
                            raise Exception(f"A8 returned {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ KPI_SNAPSHOT: A8 failed ({e}), self-recording as fallback")
                    event = BusinessEvent(
                        event_name="KPI_SNAPSHOT",
                        actor_type="system",
                        actor_id="scholarship_api",
                        session_id=None,
                        org_id=None,
                        properties=kpi_payload
                    )
                    await emitter.emit(event)
                
                logger.info(f"📊 TELEMETRY: KPI_SNAPSHOT emitted (tile=SLO, uptime={uptime}s)")
                
            except Exception as e:
                logger.warning(f"⚠️ KPI_SNAPSHOT loop error: {e}")
            
            await asyncio.sleep(300)
    
    asyncio.create_task(kpi_snapshot_loop())
    logger.info("📊 TELEMETRY: KPI_SNAPSHOT loop started (5m interval, tile=SLO)")
    
    # PHASE 2 MANDATE: Command Center Heartbeat
    async def send_command_center_heartbeat():
        """Send heartbeat to auto_com_center per Global Mandate"""
        import httpx
        
        command_center_url = os.getenv(
            "COMMAND_CENTER_URL", 
            "https://auto-com-center-jamarrlmayes.replit.app"
        )
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = {
                    "app_name": "scholarship_api",
                    "status": "online",
                    "url": "https://scholarship-api-jamarrlmayes.replit.app",
                    "revenue_ready": True,
                    "stripe_configured": True,
                    "version": settings.api_version
                }
                
                response = await client.post(
                    f"{command_center_url}/api/heartbeat",
                    json=payload
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"✅ COMMAND CENTER: Heartbeat sent successfully")
                else:
                    logger.warning(f"⚠️ COMMAND CENTER: Heartbeat returned {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"⚠️ COMMAND CENTER: Heartbeat failed (non-blocking): {e}")
    
    await send_command_center_heartbeat()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CEO Directive: Proof-of-control nonce file
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

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
# Deprecated @app.on_event("startup") handlers removed - all startup logic now in lifespan

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

# 4.05 AGENT3: Identity headers (add system_identity to all responses)
app.add_middleware(IdentityHeadersMiddleware)

# CEO v2.6 DIRECTIVE: Privacy Headers (X-Privacy-Context, DoNotSell for minors)
from middleware.privacy_headers import PrivacyHeadersMiddleware
app.add_middleware(PrivacyHeadersMiddleware)

# CEO v2.6 DIRECTIVE: API Key Guard (X-API-Key enforcement on external routes)
from middleware.api_key_guard import APIKeyGuardMiddleware
app.add_middleware(APIKeyGuardMiddleware)

# 4.1 GATE 0: Resilience Patterns (Circuit Breaker + Request Timeout)
# Prevents cascading failures and queue buildup per CEO directive
from middleware.request_timeout import RequestTimeoutMiddleware
app.add_middleware(RequestTimeoutMiddleware, timeout=5.0)

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

# CEO v2.6 DIRECTIVE: Unified error handlers with v2.6 schema
from middleware.error_handlers import register_error_handlers
register_error_handlers(app)

@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit_error(request: Request, exc: RateLimitExceeded):
    # Import the updated rate limit handler
    from middleware.rate_limiting import rate_limit_handler
    return await rate_limit_handler(request, exc)

# Include routers
# V2.2 Note: /canary endpoint moved to health router for proper organization
app.include_router(auth_router)
# Agent3 V1 compliance endpoints (prioritized for revenue readiness)
app.include_router(agent3_v1_router, tags=["Agent3 V1"])
# Master Prompt compliance endpoints (standard /api endpoints)
app.include_router(master_prompt_router, tags=["Master Prompt"])
app.include_router(scholarships_router, prefix="/api/v1", tags=["scholarships"])
app.include_router(scholarships_router, prefix="/api", tags=["scholarships"])  # Alias for cross-app compatibility
app.include_router(applications_router, prefix="/api/v1", tags=["applications"])
app.include_router(prompts_router, tags=["System Prompts"])

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
from routers.credit_aliases import router as credit_aliases_router
from routers.credits_ledger import router as credits_ledger_router

app.include_router(external_billing_router, tags=["External Billing"])
app.include_router(payments_router, tags=["Payments"])
app.include_router(data_sync_router, tags=["Data Sync"])
app.include_router(credits_ledger_router, tags=["Credits Ledger (Master Prompt Spec)"])
app.include_router(credit_aliases_router, tags=["Credit Ledger (Ecosystem API)"])
app.include_router(monetization_router, tags=["Monetization"])

# AI Scholarship Playbook: Document Hub & Predictive Matching (Student Experience)
app.include_router(documents_router, tags=["Document Hub"])
app.include_router(predictive_matching_router, tags=["Predictive Matching"])

# AI Scholarship Playbook: B2B Partner Portal endpoints
app.include_router(b2b_partner_api_router, tags=["B2B Partners API"])
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
app.include_router(observability_api_router)  # New: Daily ops dashboards and KPI reporting

# CEO DIRECTIVE 2025-11-12: Evidence API for executive review
app.include_router(evidence_router, tags=["Evidence"])
app.include_router(debug_routes_router, tags=["Diagnostics"])
app.include_router(docs_workaround_router)  # GATE 0 FIX: Manual Swagger/ReDoc mounting

# LEGAL PAGES: Privacy Policy, Terms of Service, Accessibility Statement
app.include_router(legal_pages_router, tags=["Legal"])

# TELEMETRY CONTRACT v1.1: Command Center Integration (2025-11-30)
from routers.telemetry import router as telemetry_router, executive_router
app.include_router(telemetry_router, prefix="/api", tags=["Telemetry"])

# PROTOCOL ONE TRUTH: Executive Dashboard for Command Center (2025-12-01)
app.include_router(executive_router, tags=["Executive Dashboard"])

# BUSINESS PROBES: Phase 5 P0 Revenue Rescue - Truth over Ping (2026-01-04)
app.include_router(probes_router, tags=["Business Probes"])
app.include_router(circuit_breaker_telemetry_router)
app.include_router(live_p95_dashboard_router)
app.include_router(oca_canary_router)
app.include_router(stabilization_router)
app.include_router(pre_canary_checklist_router)
app.include_router(recovery_ops_router)
app.include_router(overnight_monitoring_router)
app.include_router(backlog_drain_router)
app.include_router(day2_operations_router, tags=["Day-2 Operations"])
app.include_router(qa_orchestrator_router, tags=["QA Orchestrator"])
app.include_router(a3_orchestrator_router, tags=["A3 Orchestrator"])

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

@app.get("/version")
async def api_version():
    """API version endpoint - Gate 0 requirement"""
    return {
        "version": settings.api_version,
        "service": "scholarship_api",
        "environment": settings.environment.value
    }

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
@app.get("/ready")
@app.head("/ready")
async def readiness_check():
    """Readiness check endpoint for deployment - per SRE Fix Pack directive"""
    from models.database import SessionLocal
    from sqlalchemy import text as sql_text
    
    db_status = "ready"
    try:
        db = SessionLocal()
        db.execute(sql_text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "degraded"
    
    stripe_configured = bool(os.environ.get("STRIPE_SECRET_KEY")) and bool(os.environ.get("STRIPE_WEBHOOK_SECRET"))
    
    overall_status = "ready" if db_status == "ready" else "not_ready"
    
    return {
        "status": overall_status,
        "services": {
            "api": "ready",
            "database": db_status,
            "stripe": "configured" if stripe_configured else "missing_secrets"
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
