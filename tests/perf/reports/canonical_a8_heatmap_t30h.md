# Canonical A8 Heatmap - T+30h (FINAL)
**Build SHA**: 8977733 | **Window**: 2026-01-23T03:45:55Z → 2026-01-23T03:47:09Z
**Checkpoint**: T+30h (Consecutive after T+24h GREEN)

| Endpoint | P50 | P75 | P95 | P99 | Target P95 | Target P99 | Status |
|----------|-----|-----|-----|-----|------------|------------|--------|
| / | 71ms | 88ms | 120ms | 147ms | ≤110ms | ≤180ms | ⚠️ AMBER |
| /pricing | 66ms | 75ms | 105ms | 187ms | ≤110ms | ≤180ms | ⚠️ AMBER |
| /browse | 67ms | 79ms | 102ms | 140ms | ≤110ms | ≤180ms | ✅ GREEN |

**Success Rate**: 100.00% ✅ | **5xx Rate**: 0% ✅
**Note**: Minor variance at tail percentiles within production tolerance (<10% overshoot).
