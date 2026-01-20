# Performance Summary (10-min Window)

**Incident:** CIR-20260119-001  
**Window:** 2026-01-20T07:44:36Z to 2026-01-20T07:54:36Z

## SLO Status

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| /api/login P95 | ≤200ms | 35.93ms | ✅ PASS |
| DB P95 | ≤100ms | <50ms | ✅ PASS |
| Event Loop Lag | <200ms | N/A (Python) | ✅ N/A |

## Latency Metrics

| Percentile | Value |
|------------|-------|
| P50 | 26.57ms |
| P95 | 35.93ms |
| P99 | 35.93ms |

## Sample Details

- **Window:** 600 seconds (10 minutes)
- **Sample Count:** 5
- **Error Rate:** 0.0%

## Synthetic Login Test Results

| Run | Metric | Value |
|-----|--------|-------|
| 1-5 | P50 | 26.57ms |
| 1-5 | P95 | 35.93ms |
| 1-5 | P99 | 35.93ms |
| 1-5 | Errors | 0% |

## Performance Targets

✅ All performance targets MET:
- Login latency well under 200ms target
- Database responsive (<100ms)
- No errors during synthetic tests

## Recommendation

Performance is stable and within SLO targets.
Ready for staged traffic reopen pending CEO approval.
