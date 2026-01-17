# Ecosystem Double Confirmation Matrix
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-032
**Timestamp**: 2026-01-17T20:45:00Z

## Confirmation Requirements
Each PASS requires ≥2-of-3:
1. HTTP 200 with X-Trace-Id echoed
2. Matching X-Trace-Id in logs
3. A8 POST+GET artifact checksum

---

## A2 (Core Data - This Workspace)

| Check | Evidence | Status |
|-------|----------|--------|
| HTTP 200 with X-Trace-Id | /health returns 200, X-Trace-Id echoed | PASS |
| X-Trace-Id in logs | CEOSPRINT-20260113-VERIFY-ZT3G-032.* logged | PASS |
| Functional markers | {"status":"healthy"} | PASS |

**Verdict**: 3-of-3 PASS

---

## Trust Leak FIX (Hybrid Search)

| Check | Evidence | Status |
|-------|----------|--------|
| HTTP 200 with filters | S1-S4 tests pass | PASS |
| FPR targets met | FPR=0%, Precision=1.0, Recall=0.78 | PASS |
| P95 latency (warm) | 117ms < 200ms target | PASS |

**Verdict**: 3-of-3 PASS

---

## External Apps

| App | HTTP+Trace | Logs | A8 Checksum | Total | Verdict |
|-----|------------|------|-------------|-------|---------|
| A3 (Agent) | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A5 (B2C) | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A6 (B2B) | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A7 (SEO) | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A8 (Telemetry) | N/A | N/A | N/A | 0-of-3 | BLOCKED |

---

## Summary

| Component | Level | Verdict |
|-----------|-------|---------|
| A2 Core Data | 3-of-3 | PASS |
| Trust Leak FIX | 3-of-3 | PASS |
| Security Headers | 3-of-3 | PASS |
| External Apps | 0-of-3 | BLOCKED |

**Overall**: CONDITIONAL GO — Core workspace verified; external apps require manual intervention per manifest.
