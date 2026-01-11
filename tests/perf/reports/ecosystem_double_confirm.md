# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3G | **Protocol**: AGENT3_HANDSHAKE v27
| App | HTTP | Latency | SLO | 2nd Confirm |
|-----|------|---------|-----|-------------|
| A1 | 200 | 250ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | **107ms** | ✅ | ✅ |
| A3 | **404** | 76ms | - | ❌ |
| A4 | 200 | 222ms | ⚠️ | - |
| A5 | 200 | 163ms | ⚠️ | - |
| A6 | 200 | **91ms** | ✅ | - |
| A7 | 200 | 162ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 61ms | - | ❌ |

## Second Confirmation Summary
- **A1**: HTTP 200 + OIDC JWKS (1 key) ✅
- **A2**: HTTP 200 + 107ms SLO ✅
- **A6**: HTTP 200 + 91ms SLO ✅
- **A7**: HTTP 200 + Sitemap (2,908 URLs) ✅
- **A3/A8**: HTTP 404 - NO-GO ❌
