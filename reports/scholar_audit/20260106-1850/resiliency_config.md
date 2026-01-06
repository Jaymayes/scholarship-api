# Resiliency Configuration Report
**Scholar Ecosystem**
**Date**: 2026-01-06

---

## Circuit Breakers

| App | Component | State | Failures | Last Failure | Healthy |
|-----|-----------|-------|----------|--------------|---------|
| A1 | auth_db | CLOSED | 0 | null | YES |
| A2 | telemetry | CLOSED | 0 | N/A | YES |
| A4 | email_provider | CLOSED | 0 | N/A | YES |

## Timeouts & Retries

| App | Timeout | Retry | Backoff | Notes |
|-----|---------|-------|---------|-------|
| A1 | 30s | 3 | Exponential | Auth DB connection |
| A2 | 10s | 2 | Linear | A8 event emission |
| A4 | 10s | 3 | Exponential | SendGrid calls |

## Rate Limiting

| App | Backend | Limits | Notes |
|-----|---------|--------|-------|
| A2 | In-memory | Configured | Redis optional |

## Failure Simulations

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| DB disconnect | Circuit opens | N/A | NOT RUN |
| Auth timeout | Fallback | N/A | NOT RUN |
| A8 unavailable | Fire-and-forget | PASS | Silent failure |

---

## Alert Classification

| Alert | Classification | Evidence |
|-------|----------------|----------|
| A6 500 Error | CONFIRMED ISSUE | HTTP 500 on all endpoints |
| AUTH_FAILURE | FALSE POSITIVE | OIDC discovery working |
| REVENUE BLOCKED | STALE | $179.99 revenue exists |
