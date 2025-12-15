# Overview

This project is a Scholarship Discovery & Search API built with FastAPI, acting as a system-of-record for scholarships. It offers advanced search, filtering, and eligibility checking using semantic and keyword search, and provides analytics on user interactions. The API feeds data to Student Dashboards and Landing Pages and integrates with an Agent Bridge for distributed workflows across other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to create a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to be a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

**Current Compliance Status**: Dual-compliant with Agent3 Master Prompt + v3.0 Section B (2025-11-28)

**Real-Time Data Status**: All Master Prompt endpoints now use LIVE database queries (no mock data)

**Readiness Status**: PRODUCTION READY - Autonomous operation, all endpoints secured

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The API supports integration with Student Dashboards, landing pages, and third-party developers. It adheres to a Global Identity Standard for consistent cross-app integration within the 8-app ScholarshipAI ecosystem, ensuring consistent identity headers and no cross-app identity bleed.

## Technical Implementations
The application uses FastAPI for high performance and async capabilities, with Pydantic models for data validation. A service-oriented architecture separates concerns for scholarship operations, eligibility, search, and analytics. Data is stored in a PostgreSQL database via SQLAlchemy ORM. The API follows a RESTful design with versioned endpoints (`/api/v1/`) and includes AI-powered endpoints.

## Feature Specifications
- **Eligibility Engine**: A deterministic, rules-based engine for evaluating eligibility with scoring and bulk processing.
- **Ranking System**: A hybrid approach combining content-based filtering with "eligible-first" prioritization.
- **Search Intelligence**: Features semantic and keyword search, smart suggestions, and quality assessment.
- **Business Event Instrumentation**: A central event tracking system for executive KPI reporting, including a `business_events` table and an event emission service using a fire-and-forget async approach with a circuit breaker pattern. Fixed 2025-11-30: asyncpg SSL/JSONB compatibility for proper event recording.
- **Telemetry Contract v3.5.1** (2025-12-15): Fleet-wide telemetry with Command Center integration:
  - **SYSTEM_DIAGNOSTIC Support (2025-12-15)**: Accepts diagnostic events from A3 with relaxed payload validation
  - `POST /api/telemetry/ingest` - **PRIMARY** fleet fallback endpoint (v3.5.1 Multi-App compliant)
  - `POST /api/analytics/events` - Legacy S2S event write endpoint (CSRF bypass enabled)
  - `POST /api/events` - Legacy fallback event write endpoint
  - `GET /api/stats?window=5m|1h|24h&group=event_type` - DB-backed aggregated stats
  - `GET /api/kpis/today` and `GET /api/kpis/rollup?days=7` - Revenue-aware KPI summaries
  - `app_heartbeat` emission every 60 seconds on startup
  - `KPI_SNAPSHOT` emission every 5 minutes with SLO tile metrics
  - **v3.5.1 Header Support (2025-12-14)**: Accepts fleet-wide headers AND legacy headers:
    - New: `x-scholar-protocol`, `x-app-label`, `x-event-type`, `x-event-id`, `x-sent-at`
    - Legacy: `X-Protocol-Version`, `X-Idempotency-Key`
  - **APP_IDENTITY**: `A2 scholarship_api https://scholarship-api-jamarrlmayes.replit.app protocol=v3.5.1`
  - **Role**: `telemetry_fallback` - Fleet fallback sink when A8 Command Center unavailable
- **Credits Ledger System**: A transactional credit ledger system enabling B2C monetization and paywalled AI features, featuring a database-backed ledger, transactional idempotency, row-level locking, API endpoints with JWT and RBAC, and security/compliance features.
- **Stripe Payment Integration** (2025-12-08): Centralized payment endpoints for ecosystem apps (Operation Vital Signs):
  - `POST /api/payment/create-checkout-session` - Create Stripe Checkout session (for A5/A6)
  - `GET /api/payment/publishable-key` - Get Stripe publishable key for frontend
  - `POST /api/payment/webhook` - Stripe webhook handler for payment events
  - `GET /api/payment/status` - Payment service health check
  - Uses Replit Stripe Connector for secure credential management (sandbox mode active)
  - Webhook signature verification: STRICT (rejects unsigned webhooks)
  - **Live Auth Test**: Scheduled Wednesday 2025-12-11 09:00 UTC ($1 test payment)
- **Legal Pages & Report Branding** (2025-12-01): Unified Business + Legal Pages specification implementation:
  - `GET /privacy` - Privacy Policy (FERPA/COPPA compliant, SEO-optimized HTML)
  - `GET /terms` - Terms of Service (binding arbitration, Maricopa County jurisdiction, class action waiver)
  - `GET /accessibility` - Accessibility Statement (WCAG 2.1 AA, 2-day response SLA, alternative formats)
  - JSON-LD Organization schema with sameAs entries for SEO
  - Report branding (`_report` field) in central-stats endpoint with legal links
  - Business identity: Scholar AI Advisor by Referral Service LLC, contact: support@referralsvc.com, 602-796-0177

## System Design Choices
- **Middleware**: Includes CORS, structured logging, and centralized error handling.
- **Production Readiness**: Functional on port 5000, with enterprise-grade containerization, production middleware, strict validation, and CI/CD support.
- **Universal E2E Testing Framework**: A read-only framework for 8 interconnected ScholarshipAI applications, featuring isolated modules, revenue-first rollout gates, a 120ms TTFB performance target, YAML output, FERPA/COPPA compliance, and graceful unknown host handling.
- **System Prompt Pack**: Adopts a ScholarshipAI ecosystem-wide universal system prompt pack (v1.1) with dual architecture support for consistent directives, guardrails, KPIs, and SLOs.
- **Sentry Error & Performance Monitoring**: Comprehensive integration for production-grade error and performance monitoring, including 10% performance sampling, PII redaction, `request_id` correlation, intelligent sampling, FastAPI integration, user context tracking, and performance monitoring for P95 latency tracking.

# External Dependencies

- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.
- **PostgreSQL**: Primary database for data persistence.
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.
- **scholar_auth**: Used for JWT/JWKS validation.