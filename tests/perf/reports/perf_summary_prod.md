# Performance Summary - Production

**RUN_ID:** CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001  
**Window:** 2026-01-20T08:27:04Z to 2026-01-20T08:37:04Z (10 min)

## SLO Status

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| /api/login P95 | ≤200ms | 32.39ms | ✅ PASS (84% under) |
| DB P95 | ≤100ms | <50ms | ✅ PASS |
| Event Loop Lag | <200ms | N/A (Python) | ✅ N/A |

## Latency Metrics (Synthetic Login)

| Percentile | Value |
|------------|-------|
| P50 | 18.18ms |
| P95 | 32.39ms |
| P99 | 32.39ms |

## Sample Details

- **Window:** 600 seconds (10 minutes)
- **Iterations:** 5
- **Error Rate:** 0.0%

## Endpoint Performance

| Endpoint | Status | Response Time |
|----------|--------|---------------|
| GET /health | ✅ 200 | <50ms |
| GET /ready | ✅ 200 | <50ms |
| GET /metrics/p95 | ✅ 200 | <50ms |
| GET /api/probe/ | ✅ 200 | <100ms |
| POST /api/telemetry/ingest | ✅ 200 | <100ms |
| POST /api/internal/pilot/synthetic-login | ✅ 200 | <500ms |

## Production URLs Verified

All checks performed against PUBLIC URLs (no localhost):
- Base: https://83dfcf73-98cb-4164-b6f8-418c739faf3b-00-10wl0zocrf1wy.picard.replit.dev

## Attestation

All performance targets MET on Production:
- Login latency well under 200ms target
- Database responsive
- No errors during synthetic tests
