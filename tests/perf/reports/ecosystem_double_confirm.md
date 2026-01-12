# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-005 | **Protocol**: AGENT3_HANDSHAKE v27
| App | HTTP | Latency | SLO | 2nd Confirm |
|-----|------|---------|-----|-------------|
| A1 | 200 | 292ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | **113ms** | ✅ | ✅ |
| A3 | **404** | 90ms | - | ❌ |
| A4 | 200 | **112ms** | ✅ | - |
| A5 | 200 | 156ms | ⚠️ | - |
| A6 | 200 | 124ms | ⚠️ | ✅ Stable |
| A7 | 200 | 176ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 96ms | - | ❌ |

## At SLO (≤120ms): A4=112ms, A2=113ms ✅
## A6 Final Stability: VERIFIED (HTTP 200) ✅
