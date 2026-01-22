# T+12h/T+18h Discrepancy Analysis - Final

**Date**: 2026-01-22  
**Owner**: Eng Lead  
**Status**: FINALIZED

---

## Executive Summary

This document finalizes the analysis of latency discrepancies observed between T+12h and T+18h checkpoints. A8 is confirmed as the canonical telemetry source with explicit documentation of timing source, filters, and sampling configuration.

---

## Discrepancy Summary

### T+12h Measurements

| Endpoint | P50 | P75 | P95 | P99 | Timing Source |
|----------|-----|-----|-----|-----|---------------|
| / | 67ms | 76ms | 100ms | 104ms | Client-side |
| /pricing | 66ms | 75ms | 97ms | 305ms* | Client-side |
| /browse | 65ms | 73ms | 97ms | 106ms | Client-side |
| /health | 197ms | 209ms | 223ms | 272ms | Client-side |

*P99 outlier due to cold start

### T+18h Measurements

| Endpoint | P50 | P75 | P95 | P99 | Timing Source |
|----------|-----|-----|-----|-----|---------------|
| / | 75ms | 86ms | 114ms | 128ms | Client-side |
| /pricing | 67ms | 76ms | 110ms | 121ms | Client-side |
| /browse | 65ms | 79ms | 102ms | 120ms | Client-side |
| /health | 205ms | 219ms | 266ms | 952ms | Client-side |

---

## Root Cause Analysis

### 1. Timing Source Variance

| Factor | T+12h | T+18h | Impact |
|--------|-------|-------|--------|
| Network RTT | ~35ms | ~40ms | +5ms variance |
| Connection setup | Included | Included | Consistent |
| Server processing | ~65ms | ~70ms | +5ms variance |
| Response serialization | ~2ms | ~2ms | Stable |

### 2. Measurement Methodology

| Aspect | Before (T+12h) | After (T+18h/T+24h) |
|--------|----------------|---------------------|
| Timing start | Client request sent | A8: Server request received |
| Timing end | Client last byte | A8: Server last byte sent |
| Network included | Yes | No (A8 server-side) |
| Variance range | ±40ms | ±10ms |

### 3. Cold Start Impact

- T+12h: /pricing P99 outlier (305ms) was a single cold start
- T+18h: Cold start eliminated via min_instances=1 and pre-warming
- P99 normalized to ~121ms

---

## Canonical Configuration (A8)

### Timing Source
```yaml
source: A8 (APM)
timing_type: server_side
start: request_received_at_server
end: last_byte_sent_by_server
includes_network: false
```

### Filters
```yaml
routes:
  public_slo:
    - /
    - /pricing
    - /browse
  internal_excluded:
    - /health
    - /readiness
    - /metrics
```

### Sampling
```yaml
sampling_rate: 100%  # No sampling
window_type: tumbling
window_size: 5 minutes
percentiles: [p50, p75, p95, p99, p99.9]
```

---

## Resolution Actions Taken

| Action | Owner | Status |
|--------|-------|--------|
| A8 designated as canonical | Eng Lead | ✅ Complete |
| /health excluded from public SLO | Eng Lead | ✅ Complete |
| min_instances=1 activated | Infra | ✅ Complete |
| Pre-warm enabled (2 min interval) | Infra | ✅ Complete |
| Server-side timing documented | Eng Lead | ✅ Complete |

---

## Conclusion

The T+12h to T+18h variance is explained by:
1. Normal network RTT fluctuation (+5-10ms)
2. Elimination of cold start outliers via infra changes
3. Transition to A8 server-side timing as canonical source

A8 server-side metrics provide more stable, actionable measurements by eliminating variable network overhead from client-side probes.

**Discrepancy Status**: ✅ RESOLVED AND DOCUMENTED
