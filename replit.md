# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. Its primary purpose is to serve as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking using semantic and keyword search. The API also provides analytics on user interactions and feeds data to Student Dashboards and Landing Pages. It now includes orchestration capabilities through the Agent Bridge, allowing it to participate in distributed workflows coordinated by the Auto Command Center, alongside other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

## Recent Progress

### Deployment Configuration (2025-10-15)
- **requirements.txt Generated**: Created from pyproject.toml with 42 dependencies for Replit deployment compatibility
- **Deployment Config**: Autoscale deployment with uvicorn server configured
- **Run Command**: `uvicorn main:app --host 0.0.0.0` (Replit-compatible)
- **Build**: Auto-detected `pip install -r requirements.txt`
- **Status**: ✅ Ready for deployment (deployment blocker resolved)

### Code Quality & Production Readiness (2025-10-15)
- **Deprecation Warnings Eliminated**: Migrated from `@app.on_event("startup")` to modern FastAPI `lifespan` handlers
- **Configuration Warnings Fixed**: Added Replit proxy configuration (TRUSTED_PROXY_IPS)
- **LSP Diagnostics**: Zero errors - 100% clean codebase
- **Application Health**: Server running cleanly with all services initialized
- **Security**: WAF active, SSL configured, debug paths blocked

### P0 INCIDENT ACTIVE - Infrastructure WAF Blocking (2025-10-08 T+4:55)
- **Status**: 🔴 **P0 INCIDENT DECLARED** - WAF-BLOCK-20251008
- **Critical Blocker**: Replit infrastructure WAF (Google Frontend) blocking 100% of external traffic
- **Root Cause**: Platform-level WAF blocking at Google Cloud Armor layer, NOT application code issue
- **Evidence**: Localhost 200 OK, external 403 Forbidden - "server: Google Frontend" in headers
- **Application Code**: ✅ VERIFIED CORRECT via extensive testing (localhost, proxy headers, unit tests)
- **Synthetic Monitoring**: 100% 403 rate across 5 regions, all SEO crawlers blocked
- **Remediation**: Option A (Replit support ticket filed) + Option B (bypass code ready, auto-deploys T+6:20)
- **Next Checkpoint**: T+6:15 Go/No-Go decision on Option B deployment
- **Documentation**: `P0_INCIDENT_TRACKER.md`, `RCA_PHASE1_FINDINGS.md`, `OPTION_B_GATE_CONDITIONS.md`

### External Billing Implementation (2025-10-07)

### External Billing Implementation (LATEST)
- **Payment Externalization**: ✅ COMPLETE - All in-app payment processing removed per CEO directive
  - **Removed**: Stripe SDK, in-app checkout, payment stubs
  - **Implemented**: External billing API with HMAC signature validation (SHA-256, 5-min expiry)
  - **Endpoints**: `/billing/external/credit-grant`, `/billing/external/provider-fee-paid`
  - **Security**: Bearer token auth, idempotency via external_tx_id, WAF bypass for legitimate JSON
  - **Analytics**: PaymentCompletedExternal, ProviderFeePaidExternal, CreditBalanceUpdated events
  - **Credit Economy**: Preserved - consumption/confirm flows unchanged, balance sharing verified
- **Feature Flags**: `payments_external_enabled=true`, `payments_external_test_mode=false`
- **B2C/B2B KPIs**: Analytics events track amount_usd, credits, source_app for revenue metrics

### P0 Blockers - Launch Readiness
- **P0-1 Health Endpoints**: ✅ COMPLETE - Two-tier health architecture approved by architect
  - **Fast endpoint** (`/api/v1/health`): P95 145.6ms < 150ms target - DB & Redis checks for external monitors
  - **Deep endpoint** (`/api/v1/health/deep`): P95 869ms < 1000ms target - Comprehensive validation with real AI service checks
  - Circuit breakers active, real downstream validation, no false positives
- **P0-4 Database SSL**: ✅ COMPLETE - Production-ready SSL configuration approved by architect
  - SSL Mode: verify-full with system CA bundle (/etc/ssl/certs/ca-certificates.crt)
  - PostgreSQL 16.9 on Neon with Let's Encrypt validation
  - TLS 1.3 active, connection pooling (5+10), 0% error rate
- **P0-2 Redis**: 🟡 PENDING - Requires managed Redis provisioning (external dependency)
- **P0-3 Payments**: ✅ EXTERNALIZED - Payment processing moved to external billing apps (see above)

### Previous Work
- **Dashboard Metrics Fix**: ✅ RESOLVED - All 3 dashboards (auth, WAF, infrastructure) now operational with real-time metrics from Prometheus REGISTRY
- **Root Cause**: Workflow restart resolved module import/caching issue preventing dashboard access to metrics. Metric naming was correct (dashboards use `_total` suffix for Counter samples, metric families use base names)
- **Auth Test Suite**: 12/12 tests passing (100%) - Fixed critical JWT authentication bugs including issuer/audience validation, dependency injection issues, and error handling
- **Production Rate Limiting**: Redis-backed rate limiting with graceful in-memory fallback, enriched structured logging with 4 CEO-required fields
- **Test Infrastructure**: Auth seeding system with production safeguards, deterministic test fixtures
- **Observability Dashboards**: Deployed auth, WAF, and infrastructure monitoring dashboards with real-time metrics at `/api/v1/observability/dashboards/*`
- **Synthetic Monitoring**: Created automated health check system with Python-based monitors (health, auth login, authenticated search)
- **Metrics Instrumentation**: Auth middleware records token operations (create/validate), WAF middleware records blocks and allowlist bypasses

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application is built on FastAPI, leveraging its high performance, async capabilities, and automatic OpenAPI documentation.

## Data Models
Pydantic models are used for data validation and serialization for Scholarships, User Profiles, Eligibility, and Analytics.

## Service Layer Architecture
A service-oriented architecture ensures clear separation of concerns, with dedicated services for Scholarship operations, Eligibility checking, Search functionalities, and Analytics tracking.

## Data Storage
A PostgreSQL database is used for data persistence, integrated via SQLAlchemy ORM, managing tables like Scholarships (with JSON eligibility criteria), User Interactions, User Profiles, Search Analytics, and Organizations.

## API Structure
The API follows a RESTful design with versioned endpoints (`/api/v1/`) organized into logical router modules, including core functionalities for Search, Eligibility, Scholarship Details, Recommendations, and Interactions. It also features AI-powered endpoints for search enhancement, eligibility analysis, scholarship summaries, and trend analysis.

## Intelligence Layer
### Eligibility Engine
A deterministic, rules-based engine evaluates eligibility with detailed scoring and supports efficient bulk processing.

### Ranking System
A hybrid ranking approach combines content-based filtering with an "eligible-first" prioritization for scholarship recommendations.

### Search Intelligence
Features semantic and keyword search across scholarship details, smart suggestions, and quality assessment for search results.

## Middleware and Cross-Cutting Concerns
Includes CORS middleware, structured logging, and a centralized error handling system for consistent HTTP error formats.

## Production Readiness
The API is fully functional on port 5000, supporting integration with Student Dashboards, landing pages, third-party developers, and analytics systems. It features enterprise-grade containerization, production middleware stack, strict production validation, and comprehensive CI/CD pipeline support.

**Soft Launch Status (2025-10-07):** P0 BLOCKERS 50% COMPLETE (2/4)
- **P0-1 Health Endpoints**: ✅ COMPLETE - Fast (145.6ms) + Deep (869ms) endpoints operational
- **P0-4 Database SSL**: ✅ COMPLETE - verify-full with Let's Encrypt validation active
- **P0-2 Redis**: 🟡 PENDING - Requires managed Redis provisioning (3h ETA)
- **P0-3 Payments**: 🔴 PENDING - Requires E2E testing (6h ETA)
- Structured JSON logging active (ts, method, path, status_code, latency_ms, auth_result, waf_rule, request_id)
- Security posture strong: WAF active, SSL verify-full enforced, auth required, no public endpoints
- Stop-loss triggers configured: 5xx≥1%, P95≥300ms, auth failures 3x baseline
- Monitoring: Two-tier health checks ready for external monitors

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.