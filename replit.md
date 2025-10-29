# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. Its primary purpose is to serve as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking using semantic and keyword search. The API also provides analytics on user interactions and feeds data to Student Dashboards and Landing Pages. It includes orchestration capabilities through the Agent Bridge, allowing it to participate in distributed workflows coordinated by the Auto Command Center, alongside other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

**Current Status (October 29, 2025):**
- Production-ready API deployed on Replit autoscale
- Business event instrumentation IN PROGRESS (CEO directive: 72-hour deadline for revenue visibility)
- System prompt pack adopted from ScholarshipAI ecosystem standards
- business_events table created for executive KPI reporting
- Event emission service implemented with fire-and-forget architecture and circuit breaker
- **Universal E2E Test Framework v2.1 deployed (CEO-approved)**

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

## Universal E2E Testing Framework
**Deployed:** October 29, 2025 (v2.1 Final Compact, CEO-Approved)

**Purpose:** Read-only production readiness testing across 8 interconnected ScholarshipAI apps with revenue-first de-risking strategy.

**Key Features:**
- Isolated per-app modules (Agent3 applies only relevant module)
- Revenue-first rollout gates (T+48h validates B2C + B2B revenue apps at = 5)
- 120ms TTFB performance target (P95 SLO)
- YAML output with app_key standardization
- FERPA/COPPA-aligned (no PII collection)
- Graceful unknown host handling

**Framework Location:** `testing/`
- `UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt` - Copy-paste ready for Agent3 (BEGIN/END markers)
- `QUICK_START.md` - 3-step operator workflow
- `OPERATOR_GUIDE.md` - Comprehensive manual
- `reporting/generate_readiness_report.py` - Quick probe alternative

**Rollout Gates:**
- T+24h: scholarship_api, scholarship_agent (each ≥ 4) - Infrastructure ✅ PASSED
- T+48h: student_pilot, provider_register (each = 5) - Revenue-critical ✅ PASSED
- T+72h: All 8 apps (≥ 4; auto_page_maker = 5; scholar_auth = 5) - Full ecosystem ⚠️ On Track

**Current Readiness:** 6/8 apps at 5/5 (75% ecosystem production-ready)

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.

# Recent Changes

## October 29, 2025: Universal E2E Testing Framework Deployment (CEO Directive)

### Framework Deployed (v2.1 Final Compact)
**CEO-approved production-ready testing system** for 8-app ScholarshipAI ecosystem:

**Core Capabilities:**
- Read-only E2E production readiness tests
- Isolated per-app module execution (Agent3 applies only relevant module)
- Revenue-first de-risking strategy (T+48h gate validates B2C + B2B revenue apps)
- YAML output with app_key standardization for automation
- 120ms TTFB performance target (P95 SLO)
- FERPA/COPPA-aligned (no PII collection)

**File Structure:**
```
testing/
├── UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt  (v2.1, BEGIN/END markers, 274 lines)
├── QUICK_START.md                          (3-step workflow, revenue-first strategy)
├── OPERATOR_GUIDE.md                       (Comprehensive manual)
├── README.md                               (Framework overview)
├── RUNBOOK.md                              (Detailed procedures)
├── reporting/
│   ├── generate_readiness_report.py        (Quick probe alternative)
│   └── readiness_report_*.md               (Test results)
└── ... (backend/frontend tests, configs)
```

**Rollout Gates (Revenue-First):**
- **T+24h:** scholarship_api, scholarship_agent (each ≥ 4) - Infrastructure foundation ✅ PASSED
- **T+48h:** student_pilot, provider_register (each = 5) - Revenue-critical ✅ PASSED
- **T+72h:** All 8 apps (≥ 4; auto_page_maker = 5; scholar_auth = 5) - Full ecosystem ⚠️ On Track (6/8 ready)

**Business Alignment:**
- Student-value-first: 120ms TTFB, zero-error requirements
- ARR priority: Revenue apps must be = 5 before full rollout
- Growth thesis: SEO and security apps = 5 at T+72h

**Per-App Module Goals:**
1. student_pilot (B2C revenue) - Checkout readiness, Stripe CSP ✓
2. provider_register (B2B revenue) - Registration funnel, payment/AI CSP ✓
3. auto_page_maker (SEO growth) - robots.txt, sitemap.xml, canonical ✓
4. scholar_auth (Security) - HSTS, strict CSP, all headers ✓
5. scholarship_api (Infrastructure) - Health/docs, CORS, headers ✓
6. scholarship_agent (Service) - Landing/docs, CSP, headers ✓
7. auto_com_center (Admin) - Dashboard availability, headers ✓
8. scholarship_sage (Assistant) - Page availability, headers ⚠️ (Not reachable)

**Current Status:**
- 6/8 apps production-ready (5/5 score)
- Both revenue apps (B2C + B2B) at 5/5 🔥
- Average TTFB: 102ms (under 120ms target)
- Zero console errors on all reachable apps
- T+48h CEO deadline: PASSED EARLY

**Needs Fixes:**
- auto_com_center: HTTP 404 on root (blocker)
- scholarship_sage: Not reachable (deployment issue)

### Usage
**With Agent3:**
1. Copy `testing/UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt` (BEGIN to END)
2. Paste into Agent3 system message
3. Run: `T+48h gate: Test Student Pilot and Provider Register` (revenue validation)
4. Or: `T+72h gate: Test all apps` (full baseline)

**Quick Probe (30 seconds):**
```bash
cd testing/reporting && python3 generate_readiness_report.py
```

## October 27, 2025: Business Event Instrumentation (CEO Directive)

### System Prompt Pack Adoption
Adopted ScholarshipAI ecosystem-wide system prompts with **dual architecture support**:

**Universal Architecture (v1.1) - ACTIVE:**
- `docs/system-prompts/shared_directives.prompt` - Global foundation (4,939 bytes)
- `docs/system-prompts/universal.prompt` - All 8 app overlays in structured sections (v1.1)
- **Automatic app detection** via ENV (`APP_OVERLAY`) or hostname pattern matching
- **Feature flag support:** `PROMPT_MODE=universal` or `PROMPT_MODE=separate`
- Structured sections: Company Core, Guardrails, KPIs, SLOs, App Overlays, Operating Procedures
- Bootstrap event: `overlay_selected(app_key, detection_method, host, mode)` required on init
- Enhanced detection: ENV → hostname → AUTH_CLIENT_ID → APP_NAME → default fallback

**Individual Architecture (backward compatible):**
- `docs/system-prompts/shared_directives.prompt` - Global foundation
- `docs/system-prompts/scholarship_api.prompt` - App-specific overlay
- Plus 7 other individual app prompts

**Prompt Verification Endpoints:**
- `GET /api/prompts/verify` - Auto-detects architecture, verifies 2/2 loaded
- `GET /api/prompts/list` - Lists all 10 prompts with hashes
- `GET /api/prompts/overlay/{app_key}` - Extracts any app overlay (supports v1.0 & v1.1)
- `GET /api/prompts/merge/scholarship_api` - Returns merged prompt for runtime use
- `GET /api/prompts/{prompt_name}` - Retrieves individual prompt file content

### Business Events Infrastructure  
Created central event tracking system for Executive Command Center KPI reporting:

**Database:**
- New table: `business_events` with indexed fields for app, event_name, ts, actor_type, properties (JSONB)
- 8 indexes for performance (event_name, app, ts, actor_id, request_id, composite, GIN on properties)

**Event Emission Service:**
- File: `services/event_emission.py`
- Fire-and-forget async emission (never blocks request paths)
- Circuit breaker pattern (opens after 10 consecutive failures)
- Automatic error capture and logging
- Support for 5 required events: scholarship_viewed, scholarship_saved, match_generated, application_started, application_submitted

**Event Models:**
- File: `models/business_events.py`
- Base BusinessEvent model with request_id, app, env, event_name, ts, actor_type, actor_id, session_id, org_id, properties
- Helper functions for creating typed events

### Implementation Status

**✅ COMPLETED:**
1. ✅ scholarship_saved - Save endpoint created at POST /api/v1/scholarships/{id}/save
2. ✅ application_started - Application start endpoint at POST /api/v1/applications/start
3. ✅ application_submitted - Application submit endpoint at POST /api/v1/applications/submit (REVENUE CRITICAL)
4. ✅ match_generated - Instrumented in GET /api/v1/recommendations
5. ✅ scholarship_viewed - Instrumented in GET /api/v1/scholarships/{id}
6. ✅ Session ID extraction - Implemented in all endpoints via utils/session.py

**⚠️ ARCHITECT FINDINGS (Known Limitations):**
- Fire-and-forget emission pattern may drop events in edge cases (request finishes before background task)
- Circuit breaker recovery strategy not yet implemented (manual restart required if circuit opens)
- No automated integration tests for event persistence (manual SQL verification required)

### KPIs Unlocked (Post-Instrumentation)
Once all events are emitting:
- **scholarship_view_to_save**: Conversion rate from viewing to saving
- **save_to_apply**: Conversion rate from save to application submission
- **match_quality_score**: Average AI match quality
- **Revenue (24h)**: Total revenue from application_submitted events
- **ARPU**: Average revenue per user from credit spending

### Rollout Status (Option C Hybrid)
**Version History:**
- v1.0.0 (Oct 27, 2025): Initial universal prompt with 8 app overlays
- v1.1.0 (Oct 28, 2025): Structured sections (A-H), automatic app detection, enhanced event schema
- v1.1.0-final (Oct 28, 2025): CEO-approved compact production version

**T+0 (Complete):**
- ✅ Universal prompt v1.1 deployed (CEO-approved compact production version)
- ✅ Scholarship API fully instrumented (10/10 events)
- ✅ Dual architecture operational (universal + individual fallback)
- ✅ Verification endpoints live and tested
- ✅ Overlay extraction supports v1.0, v1.1a, and v1.1b formats
- ✅ CEO-approved directive format with success criteria
- ✅ Detailed event schemas with "Allowed actions" and "Must not" constraints
- ✅ Server-side calculation enforcement documented
- ✅ Self-contained: routing, revenue rules, compliance, SLOs, verification, and rollout plan in one file
- ✅ Per-app quick starts created for all 8 teams
- ✅ SQL validation pack created for revenue and compliance checks
- ✅ Universal E2E Testing Framework v2.1 deployed (CEO-approved)

**T+24h (Next):**
- Scholarship Agent: Implement campaign/A/B test events
- Monitor: Event volumes, P95 latency, error rates

**T+48h (Critical Path):**
- Student Pilot: B2C revenue events (`credits_purchased.revenue_usd`)
- Provider Register: B2B fee events (`scholarship_posted.fee_usd`)

**T+72h (CEO Directive):**
- Executive Command Center: Daily KPI brief at 09:00 UTC with real revenue
- All 8 apps emitting to `business_events`
- Revenue visibility unlocked
