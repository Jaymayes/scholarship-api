# Raw Truth Summary

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-021
**Protocol**: AGENT3_HANDSHAKE v29 (Strict + Scorched Earth)
**Timestamp**: 2026-01-12T20:49:54Z

## Scorched Earth

All stale artifacts purged before probing.

## Fleet Status

| App | HTTP | Content | Latency | Status |
|-----|------|---------|---------|--------|
| A1 | 200 | ✅ | 262ms | PASS |
| A2 | 200 | ✅ | 200ms | PASS |
| A3 | **404** | ❌ | 160ms | **BLOCKED** |
| A4 | 200 | ✅ | 266ms | PASS |
| A5 | 200 | ✅ | 244ms | PASS |
| A6 | 200 | ✅ | 192ms | PASS |
| A7 | 200 | ✅ | 283ms | PASS |
| A8 | **404** | ❌ | 132ms | **BLOCKED** |

## Summary

- **Healthy**: 6/8
- **Blocked**: A3, A8
- **Cache-Busted**: Yes
- **Content Verified**: Yes
