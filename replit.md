# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. Its primary purpose is to serve as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking. The system uses semantic and keyword search to match user profiles against eligibility criteria, provides analytics on user interactions, and feeds APIs for Student Dashboards and Landing Pages. 

**NEW: Agent Bridge Integration** - The API now includes orchestration capabilities through the Agent Bridge, enabling it to participate in distributed workflows coordinated by the Auto Command Center. This allows the scholarship service to be orchestrated alongside other services like Auto Page Maker, Student Pilot, and Scholarship Sage for complex multi-service workflows.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## 2025-08-21 - Production Canary Rollout in Progress
- **5-10% CANARY ACTIVE**: Successfully deployed with all validation gates green
- **SECURITY FIXES VALIDATED**: CORS hardening and rate limiting working correctly in production
- **QA MEDIUM ISSUES RESOLVED**: Both QA-1342 (CORS) and QA-1343 (Rate Limiting) fully implemented
- **MONITORING FRAMEWORK**: 60-120 minute validation window with comprehensive gate tracking
- **RATE LIMITING EVIDENCE**: 429 responses correctly triggered on /api/v1/search endpoint
- **NEXT PHASE**: Ready for 25-50% promotion pending full monitoring window completion
- **100% PROMOTION HOLD**: Blocked until production Redis backend configured and validated

## 2025-08-19 - Production-Ready Agent Bridge with Security Hardening
- **PRODUCTION SECURITY**: Enhanced JWT validation with jti, nbf, exp claims and replay protection foundation
- **RATE LIMITING**: Production-grade limits (50/min) with per-issuer and per-IP controls
- **CORRELATION TRACING**: Distributed tracing support with X-Correlation-Id headers for end-to-end monitoring
- **FEATURE FLAGS**: Orchestration control with traffic percentage and individual endpoint toggles
- **COMPREHENSIVE TESTING**: Production Postman collection, k6 load tests, and integration test suite
- **DEPLOYMENT READY**: Complete production deployment guide with canary, blue-green, and progressive strategies
- **OPERATIONAL PROCEDURES**: SLO definitions, monitoring setup, secret rotation, and rollback procedures
- **SECURITY HARDENING**: Clock skew tolerance, key rotation support, and production security controls

## 2025-08-18 - Authentication Bug Fix
- Fixed critical authentication middleware APIError constructor signature mismatch
- Protected routes now return proper 401 responses instead of 500 TypeErrors
- Corrected 7 APIError instantiations across auth middleware
- App authentication system fully functional

# System Architecture

## Backend Framework
The application is built on FastAPI, chosen for its high performance, async capabilities, and automatic generation of OpenAPI documentation at `/docs` and `/redoc`.

## Data Models
Pydantic models are used for data validation and serialization across the system, including models for Scholarships, User Profiles, Eligibility, and Analytics.

## Service Layer Architecture
A service-oriented architecture is implemented to ensure clear separation of concerns, with dedicated services for Scholarship operations, Eligibility checking, Search functionalities, and Analytics tracking.

## Data Storage
A PostgreSQL database is used for data persistence, integrated via SQLAlchemy ORM. Key tables include Scholarships (with JSON eligibility criteria), User Interactions, User Profiles, Search Analytics, and Organizations.

## API Structure
The API follows a RESTful design with versioned endpoints (`/api/v1/`) organized into logical router modules.

### Core Endpoints (v1)
- **Search**: Endpoints for semantic and keyword search, supporting both query parameters and request body for complex filters.
- **Eligibility**: Endpoints for quick and bulk student-to-scholarship eligibility checking.
- **Scholarship Details**: Endpoint to retrieve detailed scholarship information.
- **Recommendations**: Provides hybrid content-based and eligibility-prioritized recommendations.
- **Interactions**: Logs user actions like viewing, saving, or applying for scholarships for analytics.
- **Analytics Hints**: Internal endpoint for improving user-facing content.

### AI-Powered Endpoints
- **Search Enhancement**: AI-powered query enhancement and intelligent search suggestions.
- **Eligibility Analysis**: AI-driven analysis of scholarship-student compatibility.
- **Scholarship Summaries**: AI-generated student-friendly summaries.
- **Trends Analysis**: AI insights into scholarship trends and funding patterns.
- **AI Service Status**: Endpoint to check AI service availability.

## Intelligence Layer
### Eligibility Engine
A deterministic, rules-based engine evaluates eligibility with detailed scoring and supports efficient bulk processing.

### Ranking System
A hybrid ranking approach combines content-based filtering with a strong emphasis on eligibility prioritization, resulting in "eligible-first" scholarship recommendations.

### Search Intelligence
Features semantic and keyword search across scholarship details, smart suggestions, and quality assessment for search results.

## Middleware and Cross-Cutting Concerns
Includes CORS middleware, structured logging, and a centralized error handling system that returns consistent HTTP error formats.

## Production Readiness
The API is fully functional on port 5000, supporting integration with Student Dashboards, landing pages, third-party developers, and analytics systems. It features enterprise-grade containerization, production middleware stack, strict production validation, and comprehensive CI/CD pipeline support.

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## Utility Libraries
- **Python Standard Library**: For core language functionalities.
- **Logging**: Built-in Python module for application logging.

## Development and Documentation
- **OpenAPI/Swagger**: For automated API documentation.
- **Redoc**: An alternative API documentation interface.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.