# Overview

This project is a Scholarship Discovery & Search API built with FastAPI, serving as a system-of-record for scholarships. It provides advanced search, filtering, and eligibility checking using semantic and keyword search, and offers analytics on user interactions. The API supplies data to Student Dashboards and Landing Pages and integrates with an Agent Bridge for distributed workflows across other services. The business vision is to create a comprehensive, intelligent platform connecting students with relevant scholarships, aiming to be a leading solution in the scholarship search market with enterprise-grade orchestration.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The API supports integration with Student Dashboards, landing pages, and third-party developers, adhering to a Global Identity Standard for consistent cross-app integration within the ScholarshipAI ecosystem.

## Technical Implementations
The application leverages FastAPI for performance and async capabilities, using Pydantic for data validation. It employs a service-oriented architecture to separate concerns for scholarship operations, eligibility, search, and analytics. Data is persisted in PostgreSQL via SQLAlchemy ORM. The API follows a RESTful design with versioned endpoints and incorporates AI-powered features. Key features include a deterministic, rules-based eligibility engine, a hybrid ranking system, and intelligent search capabilities with semantic and keyword search. It also includes business event instrumentation for KPI reporting and a transactional credits ledger system for monetization. A centralized Stripe payment integration handles checkout sessions and webhooks. Legal pages (Privacy Policy, Terms of Service, Accessibility Statement) are implemented with SEO optimization and compliance.

## System Design Choices
The system incorporates middleware for CORS, structured logging, and centralized error handling. It is designed for production readiness with enterprise-grade containerization and CI/CD support. A universal E2E testing framework ensures cross-application consistency. The project adheres to a ScholarshipAI ecosystem-wide universal system prompt pack for consistent directives. Sentry is integrated for comprehensive error and performance monitoring, including PII redaction and performance sampling.

# External Dependencies

- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.
- **PostgreSQL**: Primary database for data persistence.
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.
- **scholar_auth**: Used for JWT/JWKS validation.
- **Stripe**: Payment processing.
- **Sentry**: Error and performance monitoring.

# Production Status

## V2 100% Cutover (2026-01-13)

**Golden Record**: `ZT3G_GOLDEN_20260114_039`  
**Status**: LIVE at 100%  
**Hypercare**: 24h monitoring active

### Guardrails Active
- FREEZE_LOCK=1
- SEO-only acquisition
- Spend caps enforced
- Auto-rollback armed (Sev-1 or P95 > 110ms for 30+ min)

### Revenue Guardrails
- Per-user daily cap: $50
- Global daily cap: $1,500
- Max single charge: $49
- Provider payouts: $100/provider/day (Phase 3+)

### 24h Hypercare Reporting
- T+2h: Stability snapshot ✓ COMPLETE (P95: 99ms, 0% errors)
- T+6h: Include payout cap raise recommendation
- T+24h: "Mission Accomplished" packet

### Provider Payout Cap Raise (T+6h Decision)
- **Token**: CFO-20260114-PAYOUT-RAISE-250
- **New Limit**: Per-provider $250/day
- **Conditions**: auth/capture ≥98.5%, refunds ≤3%, disputes=0, fraud <0.5%

### 72h Success Targets
- **Stability**: P95 ≤110ms, error ≤0.5%, uptime ≥99.9%
- **Revenue**: 4x AI markup, ARPU ≥$20, refund ≤5%
- **Growth**: +1,000 pages indexed, Visitor→Signup ≥7%
- **Compliance**: 0 PII, 100% DoNotSell, 100% X-API-Key

### Performance Workstream
Target 20% latency reduction:
- /api/probe/: 465ms → 370ms
- /ready: 182ms → 145ms