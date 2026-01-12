# Raw Truth Summary

**RUN_ID**: CEOSPRINT-20260113-0100Z-ZT3G-RERUN-009-E2E
**Collected**: 2026-01-12T17:27:32Z

## Fleet Status

| App | /health | Latency |
|-----|---------|---------|
| A1 | 200 ✅ | 461ms |
| A2 | 200 ✅ | 325ms |
| A3 | 404 ❌ | 154ms |
| A4 | 200 ✅ | 215ms |
| A5 | 200 ✅ | 325ms |
| A6 | 200 ✅ | 283ms |
| A7 | 200 ✅ | 267ms |
| A8 | 404 ❌ | 100ms |

## Critical Apps Gate

| App | Required | Actual | Status |
|-----|----------|--------|--------|
| A3 | 200 | 404 | ❌ FAIL |
| A6 | 200 | 200 | ✅ PASS |
| A8 | 200 | 404 | ❌ FAIL |

## Verdict

**Fleet Health**: 6/8
**Critical Gate**: ❌ FAIL
