# Ecosystem Double Confirmation
**RUN_ID**: CEOSPRINT-20260110-0921-REPUBLISH-ZT3B
| App | Probe 1 (HTTP) | Probe 2 | Result |
|-----|----------------|---------|--------|
| A1 | ✅ 200 (261ms) | ✅ JWKS 1 key | PASS |
| A2 | ✅ 200 (**110ms**) | ✅ Local | **SLO** |
| A3 | ❌ 404 (80ms) | ❌ N/A | **FAIL** |
| A4 | ✅ 200 (148ms) | - | PARTIAL |
| A5 | ✅ 200 (154ms) | - | PARTIAL |
| A6 | ✅ 200 (154ms) | - | PARTIAL |
| A7 | ✅ 200 (191ms) | ✅ 2,908 URLs | PASS |
| A8 | ❌ 404 (73ms) | ❌ N/A | **FAIL** |

## Zero-Trust Analysis
- A3/A8 fast 404s (73-80ms) = Replit edge responding, apps not running
- Orchestration BLOCKED: cannot achieve run_progress ≥ 1
