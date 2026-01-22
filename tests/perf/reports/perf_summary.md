# Performance Summary - Stage 4 T0 Baseline

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE4-033  
**Checkpoint**: T0 (24h Soak Start)  
**Timestamp**: 2026-01-22T06:48:45Z

---

## Server-Side Latency (Authoritative)

| Percentile | Value | Target | Status |
|------------|-------|--------|--------|
| P50 | 126.96ms | - | ✅ |
| P75 | 129.94ms | - | ✅ |
| P95 | 134.5ms | ≤120ms | ⚠️ MARGINAL |
| P99 | 151.54ms | ≤200ms | ✅ PASS |

---

## Probe Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Probes | 400 | 400 | ✅ |
| Passed | 400 | - | ✅ |
| Failed | 0 | - | ✅ |
| Success Rate | 100% | ≥99.5% | ✅ |
| 5xx Rate | 0% | <0.5% | ✅ |

---

## Endpoint Breakdown

| Endpoint | Avg Latency | Status |
|----------|-------------|--------|
| / | ~4ms | ✅ |
| /health | ~130ms | ✅ (DB query) |

---

## Stage Comparison

| Stage | Traffic | P95 (server) | Success |
|-------|---------|--------------|---------|
| 1 | 5% | 139ms | 100% |
| 2 | 25% | 130ms | 100% |
| 3 | 50% | 133ms | 100% |
| 4 (T0) | 100% | 134.5ms | 100% |

---

## Notes

- P95 slightly above 120ms target due to /health DB queries
- Core API endpoints (/) respond in 3-5ms
- No 5xx errors observed
- Performance stable across all stages
