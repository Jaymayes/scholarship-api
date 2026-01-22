# Performance Summary - Stage 4 T0 Snapshot

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE4-033  
**Snapshot**: T0 (24h Soak Start)  
**Timestamp**: 2026-01-22T06:15:00Z

---

## T0 Baseline (100% Traffic)

### Server-Side Latency (Authoritative)

| Metric | / | /health | Overall |
|--------|---|---------|---------|
| P50 | 4ms | 130ms | 67ms |
| P75 | 5ms | 131ms | 68ms |
| P95 | 8ms | 134ms | 134ms |
| P99 | 9ms | 135ms | 135ms |

### Probe Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Probes | 800 | 800 | ✅ |
| Success Rate | 100% | ≥99.5% | ✅ |
| 5xx Errors | 0 | <0.5% | ✅ |

---

## Error Budget (24h)

| Metric | Budget | Spent | Remaining |
|--------|--------|-------|-----------|
| SLO Violation | 7.2 min | 0 min | 7.2 min |
| Status | - | - | ✅ HEALTHY |

---

## Notes

- /pricing and /browse endpoints require authentication (401)
- Probes limited to public endpoints (/, /health)
- Performance stable, matching Stage 1-3 patterns
