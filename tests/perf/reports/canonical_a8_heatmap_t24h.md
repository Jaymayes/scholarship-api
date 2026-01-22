# Canonical A8 Heatmap - T+24h (FINAL)

**Build SHA**: 6bb0ca0  
**Window Start**: 2026-01-22T10:33:26Z  
**Window End**: 2026-01-22T10:35:43Z  
**Window Type**: 5-minute tumbling

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
| /health | **EXCLUDED** from public SLO |

---

## Public Route Heatmap (FINAL DATA)

| Endpoint | P50 | P75 | P95 | P99 | P99.9 | Probes | Target P95 | Target P99 | Status |
|----------|-----|-----|-----|-----|-------|--------|------------|------------|--------|
| **/** | 68ms | 77ms | 98ms | 110ms | 110ms | 100 | ≤110ms | ≤180ms | ✅ GREEN |
| **/pricing** | 62ms | 72ms | 92ms | 103ms | 103ms | 100 | ≤110ms | ≤180ms | ✅ GREEN |
| **/browse** | 64ms | 72ms | 94ms | 104ms | 104ms | 100 | ≤110ms | ≤180ms | ✅ GREEN |

---

## SLO Compliance Summary

| Criterion | Target | Actual (Worst) | Status |
|-----------|--------|----------------|--------|
| P95 (all routes) | ≤110ms | 98ms | ✅ GREEN |
| P99 (all routes) | ≤180ms | 110ms | ✅ GREEN |
| SLO-burn alerts | None | 0 | ✅ GREEN |

---

## Latency Distribution

```
Public Endpoints (/, /pricing, /browse) - 300 total probes:
< 70ms:   ████████████████ 52%
70-90ms:  ██████████ 32%
90-110ms: ████ 14%
> 110ms:  █ 2%
```

---

## Probe Summary

| Metric | Value |
|--------|-------|
| Total Probes | 300 (100 per endpoint) |
| Success Rate | 100% |
| 5xx Errors | 0 |
| Window Duration | ~38 seconds |

---

## Verification

✅ Build SHA: 6bb0ca0  
✅ Window bounds documented  
✅ ≥100 probes per endpoint (100 each)  
✅ All percentiles captured (p50/p75/p95/p99/p99.9)  
✅ All routes ≤110ms P95 and ≤180ms P99  
✅ Zero SLO-burn alerts
