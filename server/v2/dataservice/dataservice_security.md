# DataService V2 Sprint-2 Security & FERPA Controls

## Overview

This document describes the security controls and FERPA compliance mechanisms implemented in the DataService V2 Sprint-2.

## FERPA Compliance

### Role-Based Access Control (RBAC)

The DataService implements field-level access control based on user roles:

| Role | Description | FERPA Access |
|------|-------------|--------------|
| `consumer` | End users (students) | Limited - own data only |
| `school_official` | Institutional staff with legitimate educational interest | Full - with audit logging |
| `admin` | Platform administrators | Full - with audit logging |
| `system` | Internal service accounts | Full - no restrictions |

### Field Visibility Matrix

#### DataServiceUser Fields

| Field | Consumer | School Official | Admin |
|-------|----------|-----------------|-------|
| id | ✓ | ✓ | ✓ |
| email | ✗ | ✓ | ✓ |
| display_name | ✓ | ✓ | ✓ |
| status | ✓ | ✓ | ✓ |
| role | ✗ | ✓ | ✓ |
| is_ferpa_covered | ✗ | ✓ | ✓ |
| profile_data | ✗ | ✓ | ✓ |
| preferences | ✗ | ✓ | ✓ |

#### DataServiceUpload Fields

| Field | Consumer | School Official | Admin |
|-------|----------|-----------------|-------|
| id | ✓ | ✓ | ✓ |
| owner_id | ✗ | ✓ | ✓ |
| filename | ✓ | ✓ | ✓ |
| mime_type | ✓ | ✓ | ✓ |
| size_bytes | ✓ | ✓ | ✓ |
| is_ferpa_covered | ✗ | ✓ | ✓ |
| status | ✓ | ✓ | ✓ |

### FERPA Flag Behavior

When `is_ferpa_covered = true` on an entity:

1. **Consumers** see only minimal public fields
2. **School Officials** see full data with audit logging
3. All access to FERPA-covered data is logged in `ds_events`

### Audit Trail

Every access to FERPA-covered data generates an event:

```json
{
  "event_type": "ferpa_access",
  "user_id": "uuid-of-accessor",
  "entity_type": "DataServiceUser",
  "entity_id": "uuid-of-accessed-record",
  "action": "read",
  "is_ferpa_access": true,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2026-01-21T10:00:00Z"
}
```

## API Security Controls

### Idempotency Keys

All mutation endpoints require `X-Idempotency-Key` header:

- Minimum 16 characters
- Prevents duplicate operations
- Enables safe retries

```http
POST /api/v1/users
X-Idempotency-Key: abc123def456ghi789
Content-Type: application/json

{"email": "user@example.com"}
```

### Input Validation

All inputs are validated using Pydantic models:

- Email format validation
- UUID format validation
- Enum value restrictions
- Size/length constraints

### Rate Limiting

Recommended rate limits (to be configured at gateway):

| Endpoint Pattern | Rate Limit |
|-----------------|------------|
| `/health` | Unlimited |
| `/readyz` | 10/minute |
| `GET /api/v1/*` | 100/minute |
| `POST /api/v1/*` | 30/minute |
| `PATCH /api/v1/*` | 30/minute |
| `DELETE /api/v1/*` | 10/minute |

## Double-Entry Ledger Security

### Zero-Sum Validation

All ledger entries must balance to zero:

```python
# Validation in LedgerCreate
total = sum(entry.amount for entry in entries)
if abs(total) > 0.0001:
    raise ValueError("Ledger entries must sum to zero")
```

### Immutable Entries

- Ledger entries cannot be modified after creation
- Corrections require new balancing entries
- Full audit trail via `ds_events`

### Trace ID Uniqueness

- Each trace_id is unique across the system
- Enables reconciliation across related transactions
- `/api/v1/ledgers/reconcile?trace_id=...` validates balance

## File Upload Security

### Allowed MIME Types

```python
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
```

### Size Limits

- Maximum file size: 50MB
- Validated at API layer before storage

### Integrity

- SHA-256 checksum stored for verification
- Used to detect corruption or tampering

## Database Security

### Connection Security

```python
# SSL/TLS configuration (from models/database.py)
connect_args = {
    "sslmode": "verify-full",
    "sslrootcert": "/etc/ssl/certs/ca-certificates.crt",
}
```

### Soft Deletes

All records use soft deletion:

- `is_deleted` flag (default: false)
- `deleted_at` timestamp
- `deleted_by` audit field
- Queries automatically filter deleted records

### SQL Injection Prevention

- All queries use SQLAlchemy ORM
- Parameterized queries via SQLAlchemy
- No raw SQL string interpolation

## Error Handling

### Safe Error Messages

Error responses never expose:

- Internal paths
- Stack traces
- Database schema details
- Credentials or secrets

### Standard Error Format

```json
{
  "detail": "User not found"
}
```

## Monitoring & Alerting

### Security Events to Monitor

| Event | Severity | Action |
|-------|----------|--------|
| Multiple failed auth attempts | High | Alert + block IP |
| FERPA access by non-authorized role | Critical | Alert + audit |
| Unusual data access patterns | Medium | Review logs |
| Ledger imbalance detected | High | Alert + investigate |

### Log Retention

| Log Type | Retention |
|----------|-----------|
| Access logs | 90 days |
| Error logs | 1 year |
| FERPA access logs | 7 years |
| Security events | 7 years |

## Compliance Checklist

### FERPA Requirements

- [x] Role-based field filtering
- [x] Audit trail for all data access
- [x] Consent tracking (`ferpa_consent_date`)
- [x] Legitimate educational interest validation
- [x] Data minimization in responses

### Security Best Practices

- [x] Input validation on all endpoints
- [x] Idempotency for mutations
- [x] Soft deletes for data recovery
- [x] SSL/TLS for database connections
- [x] No sensitive data in error messages
- [x] UUID identifiers (non-guessable)

## Incident Response

### FERPA Breach Protocol

1. Immediately notify security team
2. Identify scope of exposed data
3. Document affected records
4. Notify affected individuals within 72 hours
5. Report to institution's FERPA compliance officer
6. Implement remediation measures
7. Update security controls as needed
