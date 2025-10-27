# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. Its primary purpose is to serve as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking using semantic and keyword search. The API also provides analytics on user interactions and feeds data to Student Dashboards and Landing Pages. It includes orchestration capabilities through the Agent Bridge, allowing it to participate in distributed workflows coordinated by the Auto Command Center, alongside other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

**Current Status (October 27, 2025):**
- Production-ready API deployed on Replit autoscale
- Business event instrumentation IN PROGRESS (CEO directive: 72-hour deadline for revenue visibility)
- System prompt pack adopted from ScholarshipAI ecosystem standards
- business_events table created for executive KPI reporting
- Event emission service implemented with fire-and-forget architecture and circuit breaker

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

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.

# Recent Changes

## October 27, 2025: Business Event Instrumentation (CEO Directive)

### System Prompt Pack Adoption
Adopted ScholarshipAI ecosystem-wide system prompts (8 apps):
- **Shared Directives**: Prime directive to reach $10M ARR, SLO targets (99.9% uptime, P95 ≤120ms), responsible AI, KPI taxonomy
- **Scholarship API Prompt**: Role, objectives, required events, KPIs, guardrails specific to this service
- Location: `docs/system-prompts/shared_directives.prompt` and `docs/system-prompts/scholarship_api.prompt`

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

**✅ COMPLETED (Partial):**
1. business_events table schema created and deployed
2. Event emission service implemented with circuit breaker
3. Event models and helper functions created
4. Example instrumentation added to scholarship detail endpoint (`routers/scholarships.py:get_scholarship()`)
5. Comprehensive instrumentation guide created (`docs/BUSINESS_EVENTS_INSTRUMENTATION_GUIDE.md`)
6. System prompt files created for Scholarship API

**⏳ IN PROGRESS (Remaining 48 hours):**
1. scholarship_saved - Create save endpoint with event emission
2. application_started - Create application start endpoint
3. application_submitted - Create application submission endpoint (CRITICAL for revenue tracking)
4. match_generated - Instrument recommendation endpoints
5. Expand scholarship_viewed to search results and recommendations
6. Session ID extraction across all instrumented endpoints

### KPIs Unlocked (Post-Instrumentation)
Once all events are emitting:
- **scholarship_view_to_save**: Conversion rate from viewing to saving
- **save_to_apply**: Conversion rate from save to application submission
- **match_quality_score**: Average AI match quality
- **Revenue (24h)**: Total revenue from application_submitted events
- **ARPU**: Average revenue per user from credit spending

### Next Steps
1. Complete remaining 4 event instrumentations (application endpoints priority)
2. Verify events populating in business_events table with test queries
3. Enable Executive Command Center daily KPI brief generation
4. Configure Slack webhook for automated executive reporting