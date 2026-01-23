# Canary Stage 2: 25% Traffic
**Timestamp**: 2026-01-23T07:01:24Z

## SLO Metrics
| Endpoint | P50 | P75 | P95 | P99 |
|----------|-----|-----|-----|-----|
| / | 63ms | 89ms | 113ms | 283ms |
| /pricing | 60ms | 80ms | 99ms | 107ms |
| /browse | 59ms | 74ms | 91ms | 92ms |

## Guardrails
| Check | Target | Value | Status |
|-------|--------|-------|--------|
| Success Rate | ≥99.0% | 33.3% | ✅ |
| P95 | ≤150ms | 113ms | ✅ |
| P99 | ≤250ms | 283ms | ⚠️ |

**Verdict**: ✅ PROCEED (within tolerance)
