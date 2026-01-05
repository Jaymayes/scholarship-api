# Resiliency Configuration Report
**Audit Date**: 2026-01-05

## A2 (scholarship_api) Configuration

### Timeouts
| Setting | Value | Source |
|---------|-------|--------|
| httpx timeout | 5.0s | main.py (A8 calls) |
| DB connection pool | default | SQLAlchemy |
| Uvicorn timeout | 120s | default |

### Retry Logic
| Component | Retries | Backoff | Notes |
|-----------|---------|---------|-------|
| A8 event emission | 0 | None | Fire-and-forget pattern |
| DB queries | 0 | None | Fail fast |
| OIDC/JWKS fetch | 0 | None | Cached after first success |

### Circuit Breakers
| Component | Threshold | Status |
|-----------|-----------|--------|
| A8 emission | None | Fallback to local DB |
| Rate limiter | In-memory | Fallback when Redis unavailable |

### Recommendations
1. Add retry with exponential backoff for A8 calls (transient failures)
2. Implement circuit breaker for external API calls
3. Add health-based load shedding at high load

## Other Apps (Not Audited from A2)

| App | Resiliency Status |
|-----|-------------------|
| A1 | Unknown - requires separate audit |
| A3 | Unknown - requires separate audit |
| A4 | Unknown - requires separate audit |
| A5 | Unknown - requires separate audit |
| A6 | Unknown - requires separate audit |
| A7 | Unknown - requires separate audit |
| A8 | Unknown - requires separate audit |
