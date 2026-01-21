# DataService Design Document

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-058  
**Service**: scholar-dataservice  
**Sprint**: V2 Sprint-1 (72h)

## Overview

DataService is the centralized data layer microservice that owns all database operations for the ScholarshipAI ecosystem. It provides a unified API for CRUD operations on core domain objects with strict access controls, FERPA compliance, and comprehensive audit trails.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│              (JWT/API Key Validation)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 scholar-dataservice                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Users     │  │  Providers  │  │ Scholarships│     │
│  │   Domain    │  │   Domain    │  │   Domain    │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│  ┌──────▼────────────────▼────────────────▼──────┐     │
│  │              PostgreSQL (Neon)                │     │
│  │         + Audit Trails + FERPA Flags          │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Endpoints

### Users Domain
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/users` | API Key | Create user |
| GET | `/api/v1/users/{id}` | JWT | Get user by ID |
| PUT | `/api/v1/users/{id}` | JWT | Update user |
| DELETE | `/api/v1/users/{id}` | JWT+Admin | Soft delete user |
| GET | `/api/v1/users/{id}/profile` | JWT | Get user profile (FERPA-aware) |

### Providers Domain
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/providers` | API Key | Create provider |
| GET | `/api/v1/providers/{id}` | JWT | Get provider by ID |
| PUT | `/api/v1/providers/{id}` | JWT+Provider | Update provider |
| GET | `/api/v1/providers/{id}/dashboard` | JWT+Provider | Get dashboard data |
| GET | `/api/v1/providers/{id}/listings` | JWT | Get provider listings |

### Scholarships Domain
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/scholarships` | JWT+Provider | Create scholarship |
| GET | `/api/v1/scholarships/{id}` | Public | Get scholarship by ID |
| PUT | `/api/v1/scholarships/{id}` | JWT+Provider | Update scholarship |
| DELETE | `/api/v1/scholarships/{id}` | JWT+Provider | Soft delete |
| GET | `/api/v1/scholarships/search` | Public | Search scholarships |

### Uploads Domain
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/uploads` | JWT | Create upload record |
| GET | `/api/v1/uploads/{id}` | JWT+Owner | Get upload by ID |
| PUT | `/api/v1/uploads/{id}/status` | API Key | Update upload status |
| GET | `/api/v1/users/{id}/uploads` | JWT+Owner | Get user uploads |

### Ledgers Domain
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/ledgers/entries` | API Key | Create ledger entry |
| GET | `/api/v1/ledgers/balance/{user_id}` | JWT | Get user balance |
| GET | `/api/v1/ledgers/reconciliation` | API Key+Finance | Get reconciliation report |

## FERPA Compliance

### Flags and Policies
| Flag | Description | Enforcement |
|------|-------------|-------------|
| `is_ferpa_covered` | User has FERPA-protected records | Restrict data access |
| `school_official_view` | Full access for school officials | Role-based |
| `consumer_view` | Limited access for general consumers | Default |

### Route Segregation
```
/api/v1/users/{id}/profile/school-official  → Full FERPA data
/api/v1/users/{id}/profile/consumer         → Redacted data
```

### Audit Trail Requirements
- All writes logged with: timestamp, user_id, action, resource, before/after
- FERPA access logged with: accessor_id, justification, scope
- 7-year retention for FERPA audit logs

## Database Schema Extensions

```sql
-- FERPA flags
ALTER TABLE users ADD COLUMN is_ferpa_covered BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN ferpa_institution_id UUID REFERENCES institutions(id);

-- Audit trail table
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts TIMESTAMPTZ DEFAULT NOW(),
  actor_id UUID,
  action VARCHAR(50),
  resource_type VARCHAR(50),
  resource_id UUID,
  before_state JSONB,
  after_state JSONB,
  ferpa_access BOOLEAN DEFAULT false,
  justification TEXT
);

-- Indexes for audit queries
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_ts ON audit_logs(ts);
```

## Infrastructure

### Binding
```
Host: 0.0.0.0
Port: $PORT (default 5001)
```

### Health Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/readyz` | Kubernetes readiness probe |
| `/metrics` | Prometheus metrics |

### Service Markers
```json
{
  "service": "scholar-dataservice",
  "version": "1.0.0",
  "app_label": "A7",
  "capabilities": ["users", "providers", "scholarships", "uploads", "ledgers"]
}
```

## OpenAPI Export

OpenAPI 3.0 specification exported to: `tests/perf/reports/dataservice_openapi.json`

## Security

- JWT validation via shared JWKS endpoint
- API key rotation every 90 days
- Rate limiting: 1000 req/min per client
- Request size limit: 10MB
- SQL injection prevention via parameterized queries

## Sprint-1 Deliverables

| Deliverable | Status |
|-------------|--------|
| Domain design | ✅ Complete |
| Endpoint specification | ✅ Complete |
| FERPA policy design | ✅ Complete |
| Audit trail design | ✅ Complete |
| OpenAPI export | ✅ Complete |

**Status**: ✅ DESIGN COMPLETE
