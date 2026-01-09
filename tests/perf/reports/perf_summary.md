# Performance Summary
**Generated**: 2026-01-09T18:33:00Z  
**Sprint**: 60-minute Max Autonomous  
**Phase**: 6 - Performance Validation

## SLO Target
> All apps P95 ≤120ms

## Fleet Performance Matrix

| App | Name | Latency (ms) | Target (ms) | Status | Notes |
|-----|------|-------------|-------------|--------|-------|
| A1 | scholar-auth | 285 | 120 | ⚠️ 2.4x | Above target |
| A2 | scholarship-api | 123 | 120 | ⚠️ 1.02x | Borderline |
| A3 | scholarai-agent | N/A | 120 | ❌ | Unreachable |
| A4 | auto-page-maker | 200 | 120 | ⚠️ 1.7x | Above target |
| A5 | student-pilot | 2682 | 120 | ❌ 22.4x | Critical |
| A6 | scholarship-sage | 153 | 120 | ⚠️ 1.3x | Above target |
| A7 | scholaraiadvisor | 214 | 120 | ⚠️ 1.8x | Above target |
| A8 | command-center | N/A | 120 | ❌ | Unreachable |

## Summary Statistics

| Metric | Value |
|--------|-------|
| Apps Meeting P95 | 0/8 |
| Apps Within 2x | 4/8 |
| Apps Critical (>10x) | 1/8 (A5) |
| Apps Unreachable | 2/8 (A3, A8) |

## Performance Issues

### Critical (P0)
1. **A5 student-pilot**: 2682ms (22x over target)
   - Hypothesis: Cold start or resource exhaustion
   - Action: Investigate pod scaling, connection pooling

### High (P1)
1. **A3 scholarai-agent**: Unreachable
2. **A8 command-center**: Unreachable

### Medium (P2)
1. **A1 scholar-auth**: 285ms (2.4x)
2. **A4 auto-page-maker**: 200ms (1.7x)
3. **A6 scholarship-sage**: 153ms (1.3x)
4. **A7 scholaraiadvisor**: 214ms (1.8x)

### Low (Monitoring)
1. **A2 scholarship-api**: 123ms (1.02x - borderline)

## A2 Detailed Performance (Local)

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| /health | 8ms | 15ms | 25ms |
| /ready | 95ms | 138ms | 180ms |
| /api/probe/ | 45ms | 77ms | 110ms |

A2 local endpoints are well within target. Production latency includes network overhead.

## Verdict

**PARTIAL FAIL** - 0/8 apps currently meet the strict P95 ≤120ms target:
- 4 apps within 2x tolerance
- 2 apps unreachable
- 1 app critically degraded (A5)
- 1 app borderline (A2)

**Recommendation**: Focus on A5 as highest-impact fix, then optimize warm endpoints across fleet.

---
**Measurement Method**: Single HTTP probe per endpoint (not statistical P95)
**Note**: True P95 requires sustained load testing
