# Canonical A8 Heatmap - T+24h

**Build SHA**: 3578e74  
**Timestamp**: 2026-01-22T10:03:15Z  
**Window**: 2026-01-22T09:58:15Z → 2026-01-22T10:03:15Z (5-min tumbling)

---

## Measurement Configuration

| Setting | Value |
|---------|-------|
| Source | **A8 (Canonical)** |
| Timing | Server-side (request start → last byte) |
| Window | 5-minute tumbling |
| Percentiles | p50, p75, p95, p99, p99.9 |
| Sampling | 100% (no sampling) |
| Filters | Public routes only (/, /pricing, /browse) |

---

## Public Route Heatmap

*Metrics to be populated after T+24h probe execution*

| Endpoint | P50 | P75 | P95 | P99 | P99.9 | Target P95 | Target P99 | Status |
|----------|-----|-----|-----|-----|-------|------------|------------|--------|
| / | TBD | TBD | TBD | TBD | TBD | ≤110ms | ≤180ms | ⏳ |
| /pricing | TBD | TBD | TBD | TBD | TBD | ≤110ms | ≤180ms | ⏳ |
| /browse | TBD | TBD | TBD | TBD | TBD | ≤110ms | ≤180ms | ⏳ |

---

## Internal Readiness Endpoints (Excluded from SLO)

| Endpoint | P50 | P75 | P95 | P99 | Notes |
|----------|-----|-----|-----|-----|-------|
| /health | TBD | TBD | TBD | TBD | DB pool check, not in SLO |

---

## Latency Distribution

*To be generated from A8 data after probe execution*

---

## Notes

- /health excluded from public SLO per CEO directive
- A8 is the single source of truth for all latency metrics
- Server-side timing eliminates network overhead variance
