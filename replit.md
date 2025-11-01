# Overview

This project is a Scholarship Discovery & Search API built with FastAPI. It serves as a system-of-record for scholarships, offering advanced search, filtering, and eligibility checking using semantic and keyword search. The API also provides analytics on user interactions and feeds data to Student Dashboards and Landing Pages. It integrates with an Agent Bridge for distributed workflows, coordinating with other services like Auto Page Maker, Student Pilot, and Scholarship Sage.

The business vision is to provide a comprehensive, intelligent platform that connects students with relevant scholarships, aiming to become a leading solution in the scholarship search market with enterprise-grade orchestration capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses FastAPI for its high performance, async capabilities, and automatic OpenAPI documentation.

## Data Models
Pydantic models are used for data validation and serialization across all core entities (Scholarships, User Profiles, Eligibility, Analytics).

## Service Layer Architecture
A service-oriented architecture separates concerns with dedicated services for Scholarship operations, Eligibility checking, Search functionalities, and Analytics tracking.

## Data Storage
A PostgreSQL database, integrated via SQLAlchemy ORM, persists data for Scholarships, User Interactions, User Profiles, Search Analytics, and Organizations.

## API Structure
The API follows a RESTful design with versioned endpoints (`/api/v1/`) organized into logical router modules covering Search, Eligibility, Scholarship Details, Recommendations, and Interactions. It also includes AI-powered endpoints for search enhancement, eligibility analysis, scholarship summaries, and trend analysis.

## Intelligence Layer
### Eligibility Engine
A deterministic, rules-based engine evaluates eligibility with detailed scoring and supports efficient bulk processing.

### Ranking System
A hybrid ranking approach combines content-based filtering with "eligible-first" prioritization for recommendations.

### Search Intelligence
Features semantic and keyword search, smart suggestions, and quality assessment for search results.

## Middleware and Cross-Cutting Concerns
Includes CORS middleware, structured logging, and a centralized error handling system.

## Production Readiness
The API is functional on port 5000, supporting integration with Student Dashboards, landing pages, third-party developers, and analytics systems. It features enterprise-grade containerization, a production middleware stack, strict production validation, and comprehensive CI/CD pipeline support.

## Universal E2E Testing Framework
A read-only production readiness testing framework for 8 interconnected ScholarshipAI applications is deployed. It features isolated per-app modules, revenue-first rollout gates, a 120ms TTFB performance target (P95 SLO), YAML output, FERPA/COPPA compliance, and graceful unknown host handling. The framework is located in the `testing/` directory.

## Business Event Instrumentation
A central event tracking system has been implemented for executive KPI reporting. This includes a `business_events` table in the database and an event emission service (`services/event_emission.py`) that uses a fire-and-forget async approach with a circuit breaker pattern. Five key events are tracked: `scholarship_viewed`, `scholarship_saved`, `match_generated`, `application_started`, and `application_submitted`.

## System Prompt Pack
The project adopts a ScholarshipAI ecosystem-wide universal system prompt pack (v1.1) with dual architecture support. This allows for automatic app detection and feature flag support, ensuring consistent directives, guardrails, KPIs, and SLOs across applications. Verification endpoints are provided for prompt management.

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Main web framework.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management.

## AI Integration
- **OpenAI**: Integrated for AI-powered search enhancement, scholarship summaries, eligibility analysis, and trend insights.