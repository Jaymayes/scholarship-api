# Performance Summary - ZT3G Verification

**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027  
**Protocol**: AGENT3_HANDSHAKE v30  
**Window**: 2026-01-22T19:19:31Z → 2026-01-22T19:20:46Z

---

## SLO Targets

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| P95 (public routes) | ≤110ms | 86ms | ✅ PASS |
| P99 (public routes) | ≤180ms | 96ms | ✅ PASS |
| Success Rate | ≥99.5% | 100.00% | ✅ PASS |
| 5xx Rate | <0.5% | 0% | ✅ PASS |

---

## Per-Endpoint Heatmap

### Public SLO Endpoints

| Endpoint | P50 | P75 | P95 | P99 | Probes | Status |
|----------|-----|-----|-----|-----|--------|--------|
| / | 59ms | 68ms | 86ms | 96ms | 150 | ✅ GREEN |
| /pricing | 52ms | 62ms | 81ms | 89ms | 150 | ✅ GREEN |
| /browse | 53ms | 60ms | 81ms | 99ms | 150 | ✅ GREEN |

### Internal Endpoints (Excluded from SLO)

| Endpoint | P50 | P75 | P95 | P99 | Notes |
|----------|-----|-----|-----|-----|-------|
| /health | 179ms | 187ms | 207ms | 237ms | DB check included |

---

## Probe Summary

| Metric | Value |
|--------|-------|
| Total Probes | 600 |
| Successful | 600 |
| 5xx Errors | 0 |
| Success Rate | 100.00% |
| 5xx Rate | 0% |

---

## Raw Samples

Raw latency data collected with X-Trace-Id headers for verification.
See: tests/perf/evidence/raw_curl_evidence.txt

---

## Verdict

**✅ ALL SLO TARGETS MET**

- P95 ≤110ms: 86ms ✅
- P99 ≤180ms: 96ms ✅
- Success ≥99.5%: 100.00% ✅
- 5xx <0.5%: 0% ✅
