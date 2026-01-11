# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G-RERUN-001 | **Protocol**: AGENT3_HANDSHAKE v27
| App | HTTP | Latency | SLO | 2nd Confirm |
|-----|------|---------|-----|-------------|
| A1 | 200 | 322ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | 217ms | ⚠️ | ✅ |
| A3 | **404** | 98ms | - | ❌ |
| A4 | 200 | 133ms | ⚠️ | - |
| A5 | 200 | 152ms | ⚠️ | - |
| A6 | 200 | **118ms** | ✅ | - |
| A7 | 200 | 198ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 87ms | - | ❌ |

## At SLO (≤120ms): A6=118ms ✅
