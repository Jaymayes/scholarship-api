# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. Its primary purpose is to serve as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking using semantic and keyword search. The API also provides analytics on user interactions and feeds data to Student Dashboards and Landing Pages. It now includes orchestration capabilities through the Agent Bridge, allowing it to participate in distributed workflows coordinated by the Auto Command Center, alongside other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

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

**Soft Launch Status (2025-10-04):** LIVE - Conditional GO with 24-hour observability follow-up
- Structured JSON logging active (ts, method, path, status_code, latency_ms, auth_result, waf_rule, request_id)
- Security posture strong: WAF active, SSL enforced, auth required, no public endpoints
- Stop-loss triggers configured: 5xx≥1%, P95≥300ms, auth failures 3x baseline
- Performance: P95 latency 9.87ms (30x under threshold), 0% error rate
- Monitoring: Console + structured logs (dashboards T+24h deliverable)

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.