# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260109-2100-REPUBLISH  
**Generated**: 2026-01-09T21:10:12Z

## Fleet Status (Post-Republish)
| App | Probe 1 | Probe 2 | Latency | Status |
|-----|---------|---------|---------|--------|
| A1 | ✅ 200 | ✅ JWKS valid | 112ms | PASS |
| A2 | ✅ 200 (prod) | ✅ 200 (local) | 125/69ms | PASS |
| A3 | ❌ 404 | ❌ 404 | - | FAIL |
| A4 | ✅ 200 | N/A | 228ms | SINGLE |
| A5 | ✅ 200 | N/A | 143ms | SINGLE |
| A6 | ✅ 200 | N/A | 130ms | SINGLE |
| A7 | ✅ 200 | ✅ sitemap | 184ms | PASS |
| A8 | ❌ 404 | ❌ 404 | - | FAIL |

## Conflicts
- A3: 404 (unreachable)
- A8: 404 (unreachable)
