# Resiliency Configuration Report
**A2 Scholar API Aggregator**
**Date**: 2026-01-06

---

## A2 Resiliency Configuration

### Circuit Breakers

| Component | State | Failures | Threshold | Recovery Time |
|-----------|-------|----------|-----------|---------------|
| A8 telemetry | CLOSED | 0 | 5 | 30s |
| PostgreSQL | CLOSED | 0 | 3 | 10s |
| Stripe API | CLOSED | 0 | 3 | 60s |

### Timeouts

| Endpoint | Timeout | Notes |
|----------|---------|-------|
| /health | 5s | Fast check |
| /ready | 10s | Deep check (DB + Stripe) |
| A8 ingest | 10s | Fire-and-forget |
| DB queries | 30s | SQLAlchemy default |

### Retry Configuration

| Component | Retries | Backoff | Notes |
|-----------|---------|---------|-------|
| A8 events | 2 | Linear (1s, 2s) | Fire-and-forget fallback |
| DB connections | 3 | Exponential | Pool retry |

### Rate Limiting

| Scope | Backend | Limit | Notes |
|-------|---------|-------|-------|
| Global | In-memory | 100/min | DISABLE_RATE_LIMIT_BACKEND=true |
| API | In-memory | 60/min | Per-IP |

---

## A2 → A8 Ingest Path

### Latency Profile (10 samples)

| Metric | Value | SLO Target | Status |
|--------|-------|------------|--------|
| P50 | 103ms | - | - |
| P95 | 125ms | ≤150ms | ✅ PASS |
| P99 | 140ms | - | - |
| Max | 140ms | - | - |

### Ingest Validation

| Check | Status |
|-------|--------|
| A8_KEY present | ✅ (64 chars) |
| TLS connection | ✅ HTTPS |
| Event persistence | ✅ 100% |
| Protocol v3.5.1 headers | ✅ Accepted |

---

## WAF / Security Rules

| Test | Result | Notes |
|------|--------|-------|
| JWT Authorization header | PASS | Accepted |
| Telemetry ingest headers | PASS | Requires x-event-id |
| CORS preflight | PASS | scholaraiadvisor.com allowed |

### Exemptions Required

None. All internal tokens and JWTs are properly accepted.

---

## Resiliency Probes (Staging)

| Probe | Expected | Actual | Status |
|-------|----------|--------|--------|
| 500ms latency injection | Circuit stays closed | N/A | NOT RUN |
| 503 simulation | Exponential backoff | N/A | NOT RUN |
| DB disconnect | Graceful degradation | N/A | NOT RUN |

**Note**: Resiliency probes require staging deployment access for injection testing.

---

## Recommendations

1. **A8 Ingest**: Current P95 (125ms) is well within 150ms SLO. No changes needed.
2. **Ready Endpoint**: Consider caching DB/Stripe checks to reduce P95 from 691ms.
3. **Rate Limiting**: In-memory mode is acceptable for single-instance; add Redis for horizontal scaling.
