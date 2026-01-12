# Raw Truth Summary

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-017
**Protocol**: AGENT3_HANDSHAKE v28 (Strict Mode)
**Timestamp**: 2026-01-12T19:06:43Z

## Fleet Status

| App | HTTP | Content | Latency | Status |
|-----|------|---------|---------|--------|
| A1 | 200 | ✅ YES | 224ms | ✅ PASS |
| A2 | 200 | ✅ YES | 187ms | ✅ PASS |
| A3 | **404** | ❌ NO | 95ms | ❌ BLOCKED |
| A4 | 200 | ✅ YES | 157ms | ✅ PASS |
| A5 | 200 | ✅ YES | 196ms | ✅ PASS |
| A6 | 200 | ✅ YES | 129ms | ✅ PASS |
| A7 | 200 | ✅ YES | 209ms | ✅ PASS |
| A8 | **404** | ❌ NO | 148ms | ❌ BLOCKED |

## Summary

- **Healthy**: 6/8
- **Blocked**: A3, A8
- **Cache-Busted**: Yes (?t=epoch)
- **Content Verified**: Yes (service markers checked)

## Blocked Apps

Per v28 Strict Mode: A3 and A8 are marked BLOCKED pending CEO manual intervention.
See: `tests/perf/reports/manual_intervention_manifest.md`
