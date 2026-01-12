# Performance Summary

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-017
**Timestamp**: 2026-01-12T19:09:09Z

## Health Endpoint Latencies

| App | Latency | Status |
|-----|---------|--------|
| A1 | 224ms | ⚠️ Above 120ms |
| A2 | 187ms | ⚠️ Above 120ms |
| A3 | N/A | ❌ BLOCKED (404) |
| A4 | 157ms | ⚠️ Above 120ms |
| A5 | 196ms | ⚠️ Above 120ms |
| A6 | 129ms | ⚠️ Above 120ms |
| A7 | 209ms | ⚠️ Above 120ms |
| A8 | N/A | ❌ BLOCKED (404) |

## A1 Warmup Results

| Metric | Value | Target |
|--------|-------|--------|
| P95 | 159ms | ≤120ms |

## Notes

- Initial cold-start latencies are higher
- After warmup, A1 P95 improved but remains above 120ms target
- A2 (scholarship-api) shows best performance at 94-187ms
- A3/A8 blocked - cannot measure

## Recommendations

1. Enable keep-alive connections
2. Implement connection pooling
3. Add caching for static responses
4. Consider Replit Reserved VM for consistent performance
