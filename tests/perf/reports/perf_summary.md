# Performance Summary
**RUN_ID**: CEOSPRINT-20260109-1913-28d9a4  
**Generated**: 2026-01-09T19:19:38Z  
**Target**: All apps P95 ≤120ms

## Fleet Performance (Fresh Probes This Run)

| App | Name | Latency | Target | Status | Notes |
|-----|------|---------|--------|--------|-------|
| A1 | scholar-auth | 152ms | 120ms | ⚠️ 1.3x | Above target |
| A2 | scholarship-api | 110ms | 120ms | ✅ | Within target |
| A3 | scholarai-agent | N/A | 120ms | ❌ | Unreachable (404) |
| A4 | auto-page-maker | 147ms | 120ms | ⚠️ 1.2x | Above target |
| A5 | student-pilot | 192ms | 120ms | ⚠️ 1.6x | Above target |
| A6 | scholarship-sage | 227ms | 120ms | ⚠️ 1.9x | Above target |
| A7 | scholaraiadvisor | 215ms | 120ms | ⚠️ 1.8x | Above target |
| A8 | a8-command-center | N/A | 120ms | ❌ | Unreachable (404) |

## Summary Statistics

| Metric | Value |
|--------|-------|
| Apps Meeting P95 ≤120ms | 1/8 (A2) |
| Apps Within 2x Target | 5/8 |
| Apps Unreachable | 2/8 (A3, A8) |
| Best Performer | A2 (110ms) |
| Worst Performer | A6 (227ms) |

## Dual-Source Performance (A2)

| Source | Latency | Status |
|--------|---------|--------|
| Production (/health) | 110ms | ✅ |
| Local (/health) | 8ms | ✅ |

## 10-Minute Stability Window

**Status**: Not measured - single-point probes only

Per directive: "Only mark PASS if, for ≥10 consecutive minutes, P95 ≤120ms, error rate <1%, and A8 ingestion ≥99%"

| Criterion | Requirement | Current | Status |
|-----------|-------------|---------|--------|
| P95 ≤120ms | All apps | 1/8 apps | ❌ FAIL |
| Error rate <1% | Fleet-wide | 2 unreachable | ⚠️ N/A |
| A8 ingestion ≥99% | Required | 0% (404) | ❌ FAIL |

## Verdict

**FAIL** - Performance criteria not met:
- 1/8 apps meeting strict P95 ≤120ms
- 5/8 apps within 2x tolerance
- 2/8 apps unreachable
- A8 ingestion at 0% (blocked)
- 10-minute stability window not validated

---
**Evidence SHA256**: See checksums.json
**Measurement**: Single HTTP probe per endpoint (not statistical P95)
