# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-005 | **Protocol**: AGENT3_HANDSHAKE v27
| App | HTTP | Latency | SLO | 2nd Confirm |
|-----|------|---------|-----|-------------|
| A1 | 200 | 210ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | **97ms** | ✅ | ✅ |
| A3 | **404** | 75ms | - | ❌ External workspace |
| A4 | 200 | 145ms | ⚠️ | - |
| A5 | 200 | 124ms | ⚠️ | - |
| A6 | 200 | 195ms | ⚠️ | ✅ Stable |
| A7 | 200 | 180ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 74ms | - | ❌ External workspace |

## At SLO (≤120ms): A2=97ms ✅
## Port 5000: CLEAN ✅
## A6 No-Touch: VERIFIED ✅
## A3/A8 Fix: BLOCKED (external workspaces)
