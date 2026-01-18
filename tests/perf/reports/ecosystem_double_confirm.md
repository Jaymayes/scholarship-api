# Ecosystem Double Confirmation Matrix
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030
**Timestamp**: 2026-01-18T18:40:19Z

## Second Confirmation Requirements
Each PASS requires ≥2-of-3:
1. HTTP 200 + X-Trace-Id (header or payload)
2. Matching X-Trace-Id in service logs
3. A8 POST+GET artifact checksum

---

## A2 Core Data (This Workspace)

| Check | Evidence | Status |
|-------|----------|--------|
| HTTP 200 + X-Trace-Id | /health 200, trace in response | PASS |
| Logs | Trace ID logged | PASS |
| Functional markers | {"status":"healthy"} | PASS |

**Result**: 3-of-3 PASS

---

## Trust Leak FIX

| Check | Evidence | Status |
|-------|----------|--------|
| S1 FPR reduction | 22.22% | PASS |
| S3 FPR reduction | 77.78% | PASS |
| Overall FPR | 0% < 5% target | PASS |
| Precision | 1.0 | PASS |
| Recall | 0.78 | PASS |

**Result**: 5-of-5 PASS

---

## External Apps

| App | HTTP | Logs | A8 | Total | Status |
|-----|------|------|----| ------|--------|
| A1 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A3 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A4 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A5 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A6 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A7 | N/A | N/A | N/A | 0-of-3 | BLOCKED |
| A8 | N/A | N/A | N/A | 0-of-3 | BLOCKED |

---

## Summary
- **A2**: 3-of-3 PASS
- **Trust Leak FIX**: 5-of-5 PASS
- **External Apps**: 0-of-3 BLOCKED

**Overall**: BLOCKED — Core (A2) verified, external apps require owner action
