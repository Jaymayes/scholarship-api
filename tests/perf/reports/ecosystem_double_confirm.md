# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260110-2041-REPUBLISH-ZT3D
| App | HTTP | Latency | SLO | Dual |
|-----|------|---------|-----|------|
| A1 | 200 | 210ms | ⚠️ | ✅ JWKS 1 key |
| A2 | 200 | **93ms** | ✅ | ✅ |
| A3 | **404** | 87ms | - | ❌ |
| A4 | 200 | 138ms | ⚠️ | - |
| A5 | 200 | 150ms | ⚠️ | - |
| A6 | 200 | **101ms** | ✅ | - |
| A7 | 200 | 223ms | ⚠️ | ✅ 2,908 URLs |
| A8 | **404** | 106ms | - | ❌ |

## Cross-Workspace Elevation Required
A3/A8 return 404 (fast 87-106ms) = Replit edge, not apps.
