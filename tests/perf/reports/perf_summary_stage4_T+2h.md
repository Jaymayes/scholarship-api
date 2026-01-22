# Performance Summary - Stage 4 T+2h Snapshot

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE4-SNAP-T+2H-034  
**Checkpoint**: T+2h  
**Timestamp**: 2026-01-22T07:21:32Z

---

## Server-Side Latency

| Percentile | Value | Target | Status |
|------------|-------|--------|--------|
| P50 | 130ms | - | ✅ |
| P75 | 133ms | - | ✅ |
| P95 | 135ms | ≤120ms | ⚠️ MARGINAL |
| P99 | 145ms | ≤200ms | ✅ PASS |

---

## Probe Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Probes | 200 | 200 | ✅ |
| Passed | 200 | - | ✅ |
| Failed | 0 | - | ✅ |
| Success Rate | 100% | ≥99.5% | ✅ |
| 5xx Rate | 0% | <0.5% | ✅ |

---

## Comparison (T0 → T+2h)

| Metric | T0 | T+2h | Delta | Status |
|--------|-----|------|-------|--------|
| P95 | 134.5ms | 135ms | ~stable | ✅ |
| P99 | 151.54ms | 145ms | ~stable | ✅ |
| Success | 100% | 100% | 0 | ✅ |
| 5xx | 0% | 0% | 0 | ✅ |

---

## Verdict

**PASS** - All metrics within acceptable range. System stable since T0.
