# Overview

This project is a Scholarship Discovery & Search API built with FastAPI, acting as a system-of-record for scholarships. It offers advanced search, filtering, and eligibility checking using semantic and keyword search, and provides analytics on user interactions. The API feeds data to Student Dashboards and Landing Pages and integrates with an Agent Bridge for distributed workflows across other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to create a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to be a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

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
- **Business Event Instrumentation**: A central event tracking system for executive KPI reporting, including a `business_events` table and an event emission service using a fire-and-forget async approach with a circuit breaker pattern.
- **Credits Ledger System**: A transactional credit ledger system enabling B2C monetization and paywalled AI features, featuring a database-backed ledger, transactional idempotency, row-level locking, API endpoints with JWT and RBAC, and security/compliance features.

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