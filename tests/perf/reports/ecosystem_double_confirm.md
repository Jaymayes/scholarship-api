# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260111-REPUBLISH-ZT3F
| App | HTTP | Latency | SLO | Dual |
|-----|------|---------|-----|------|
| A1 | 200 | 275ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | **108ms** | ✅ | ✅ |
| A3 | **404** | 66ms | - | ❌ |
| A4 | 200 | 165ms | ⚠️ | - |
| A5 | 200 | 678ms | ⚠️ | - |
| A6 | 200 | **116ms** | ✅ | - |
| A7 | 200 | 188ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 77ms | - | ❌ |

## Second Confirmation Status
- **A1 OIDC**: HTTP 200 + JWKS (1 key) ✅
- **A7 SEO**: HTTP 200 + Sitemap (2,908 URLs) ✅
- **A2**: HTTP 200 + 108ms SLO ✅
- **A6**: HTTP 200 + 116ms SLO ✅
- **A3/A8**: HTTP 404 - NO-GO ❌
