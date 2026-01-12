# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-006 | **Protocol**: AGENT3_HANDSHAKE v27
**Mode**: Persistence Audit (Read-Only)

| App | HTTP | Latency | SLO | 2nd Confirm | Persistence |
|-----|------|---------|-----|-------------|-------------|
| A1 | 200 | 132ms | ⚠️ | ✅ JWKS 1 key | ✅ |
| A2 | 200 | **106ms** | ✅ | ✅ | ✅ |
| A3 | **404** | 82ms | - | ❌ | ❌ FAILED |
| A4 | 200 | 145ms | ⚠️ | - | ✅ |
| A5 | 200 | 161ms | ⚠️ | - | ✅ |
| A6 | 200 | **120ms** | ✅ | ✅ Stable | ✅ |
| A7 | 200 | 171ms | ⚠️ | ✅ 2,908 URLs | ✅ |
| A8 | **404** | 78ms | - | ❌ | ❌ FAILED |

## At SLO (≤120ms): A2=106ms, A6=120ms ✅
## Port 5000: CLEAN ✅
## A6 No-Touch: VERIFIED ✅
## A3/A8 Persistence: FAILED ❌ (never fixed)
