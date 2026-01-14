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
- **Token**: CFO-20260114-PAYOUT-RAISE-250 ✓ CONSUMED
- **New Limit**: Per-provider $250/day, Global $5,000/day
- **Guardrails**: 10% holdback, auto-pause >1% refund/dispute, 4hr manual review

### Cost Governance
- COST_THROTTLE=ACTIVE until 24h projection ≤$280 for 3 consecutive hours
- Step-down: 75% background tasks → 100% if ≤$300
- 60s TTL cache on search/match through T+24h
- Queue depth /documents/analyze < 30, P95 ≤ 1.5s

### T+24h Packet Requirements (for paid pilot)
- SLO rollup, error histograms, revenue split (B2C/B2B)
- ARPU, refund rate, AI gross margin
- SEO net pages + CTR, LTV:CAC
- Cost vs cap, payout utilization/holds
- Security/privacy samples, incident log

### Paid Pilot Pre-Authorization
- **Token**: CEO-20260114-PAID-PILOT-72H
- **Conditions**: Daily budget ≤$150, CAC ceiling $12, ARPU ≥$18 within 7d
- **Scope**: Retargeting only, no prospecting, privacy/compliance green

### Finance Ops
- Reserve ledger: 10% holdback confirmed
- Payout schedule: Net-14 (simulation until T+24h green)
- Reconciliation: Stripe = Platform ledger ± $0

### 72h Success Targets
- **Stability**: P95 ≤110ms, error ≤0.5%, uptime ≥99.9%
- **Revenue**: 4x AI markup, ARPU ≥$20, refund ≤5%
- **Growth**: +1,000 pages indexed, Visitor→Signup ≥7%
- **Compliance**: 0 PII, 100% DoNotSell, 100% X-API-Key

### Performance Workstream
Target 20% latency reduction:
- /api/probe/: 465ms → 370ms
- /ready: 182ms → 145ms

## Mission Accomplished (2026-01-14)

**Status**: V2 is system of record, revenue flowing, Paid Pilot LIVE  
**Acceptance**: CEO directive 2026-01-14

### 90-Day Scale Plan ($10M ARR Target)

#### North-Star Targets (Rolling)
- **Reliability**: ≥99.9% uptime, P95 ≤110ms (≤100ms stretch), error ≤0.5%
- **Unit Economics**: AI gross margin ≥60%, refund ≤5%, chargebacks = 0
- **Growth Mix**: ≥85% organic SEO sessions
- **B2C Revenue**: ARPU ≥$22 near-term, ≥$28 by Day 90
- **B2B Revenue**: 3% provider fees, 150 active providers, ≥500 listings

#### Next 7 Days (Post-Cutover Stabilization)
- Cost governance: auto-throttle rules, daily spend report
- Payouts: simulation continues, CFO approval for LIVE after 7d observation
- V1 retirement: Day 7 archive, checksum + data retention manifest
- Security: privacy mini-audit, key rotation at T+48h

#### Paid Acquisition Pilot - Day 2 (Step-Up Active)
- **Token**: CEO-20260114-PAID-PILOT-STEPUP ✓ CONSUMED
- **Budget**: $300/day rolling 24h (stepped up from $150)
- **Pacing**: 30/30/40 split AM/PM/evening

##### Operating Rules
- **Auto-Downshift**: $150/day if 6h avg breaches CAC >$10, Stripe <98.5%, fraud ≥0.5%, or refund ≥4%
- **Segments**: First-upload abandoners, checkout abandoners, high-intent viewers
- **Frequency Caps**: ≤3 impressions/user/day, ≤7/week; suppress converters 14d
- **Creative Mix**: 70% winner, 20% challenger, 10% exploratory
- **Kill Criteria**: After 500 impressions, drop if CTR −30% vs control or CAC +25% vs cohort for 6h

##### Success Gates (Sustained)
- CAC ≤$8 for 24h continuous
- ARPU ≥1.8× CAC
- Refunds ≤4%
- Stripe success ≥98.5%

#### SEO Growth Engine (Auto Page Maker)
- Weekly goal: +7,500 net pages indexed
- Quality guardrails: dedupe, thin-content filters, bounce rate monitoring

#### Reporting Cadence
- Paid Pilot: T+12h and T+24h daily reports
- Weekly 1-pager (Fridays): KPI rollup, incidents, cost, SEO growth, funnel deltas

#### Finance & Forecasting
- Daily revenue rollup: B2C net, B2B fees, ARPU, refunds, margin
- Reconciliation: Stripe ↔ platform ledger ± $0
- 30/60/90-day run-rate forecast with confidence bands