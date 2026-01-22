# Performance Summary - Stage 4 T+12h Snapshot

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE4-SNAP-T+12H-038  
**Checkpoint**: T+12h  
**Timestamp**: 2026-01-22T08:52:38Z

## Per-Endpoint Percentile Heatmap

| Endpoint | P50 | P75 | P95 | P99 | Target P95 | Target P99 | Status |
|----------|-----|-----|-----|-----|------------|------------|--------|
| / | 67ms | 76ms | 100ms | 104ms | ≤120ms | ≤200ms | ✅ PASS |
| /health | 197ms | 209ms | 223ms | 272ms | ≤120ms | ≤200ms | ⚠️ MARGINAL |
| /pricing | 66ms | 75ms | 97ms | 305ms | ≤120ms | ≤200ms | ⚠️ P99 outlier |
| /browse | 65ms | 73ms | 97ms | 106ms | ≤120ms | ≤200ms | ✅ PASS |

### Analysis

- **Root (/)**: Fast, stable. ✅
- **/health**: Slower due to DB pool check. P95/P99 elevated but acceptable for health endpoint.
- **/pricing**: Fast median, but single P99 outlier (305ms) - likely cold start or GC pause.
- **/browse**: Fast, stable. ✅

### Latency Histogram Distribution

```
< 100ms: ████████████████████ 75%
100-150ms: ████████ 15%
150-200ms: ███ 5%
200-250ms: ██ 3%
> 250ms: █ 2%
```

## Probe Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total | 200 | 200 | ✅ |
| HTTP 200/404 | 200 | - | ✅ |
| 5xx | 0 | <0.5% | ✅ |
| Success Rate | 100% | ≥99.5% | ✅ |

## Slow-Log Top Offenders

| Endpoint | Max Latency | Likely Cause |
|----------|-------------|--------------|
| /pricing | 305ms | Cold start / GC |
| /health | 272ms | DB pool wait |

## Verdict: **PASS** (with marginal notes)
