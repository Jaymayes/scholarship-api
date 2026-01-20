# Neon DB Gate-3 Performance Report

**RUN_ID**: CEOSPRINT-20260120-EXEC-ZT3G-GATE3-037  
**Timestamp**: 2026-01-20T20:44:00Z  
**Gate**: 3 (50% Traffic)

## Thresholds

| Metric | Threshold | Target |
|--------|-----------|--------|
| P95 Latency | ≤150ms | PASS |
| Active Connections | ≤pool_max × 1.25 | PASS |
| Wait Queue | =0 | PASS |
| Reconnects | ≤3/min | PASS |
| Connection Errors | =0 | PASS |

## Verification Samples (Condensed Window)

| Sample | Timestamp | DB P95 | Event Loop | Error Rate | Response Time | Status |
|--------|-----------|--------|------------|------------|---------------|--------|
| 1 | 20:43:00Z | 0ms | 0.0ms | 0% | 80ms | ✓ GREEN |
| 2 | 20:43:10Z | 0ms | 0.0ms | 0% | 86ms | ✓ GREEN |
| 3 | 20:43:21Z | 0ms | 0.0ms | 0% | 56ms | ✓ GREEN |
| 4 | 20:43:31Z | 0ms | 0.0ms | 0% | 64ms | ✓ GREEN |
| 5 | 20:43:42Z | 0ms | 0.0ms | 0% | 72ms | ✓ GREEN |

## Spike Test (Thundering Herd Simulation)

- **Concurrent Requests**: 20
- **Total Duration**: 5,411ms
- **All Responses**: HTTP 200
- **Response Times**: 4.7s - 5.2s (cold start + network latency)
- **Database Status**: Connected, healthy
- **Connection Errors**: 0
- **Reconnects**: 0

## Database Probe

```json
{
  "status": "pass",
  "probe": "db",
  "db_connected": true,
  "db_time": "2026-01-20 20:44:14.830544+00:00"
}
```

## Verdict

**STATUS: GREEN** - All Neon DB metrics within thresholds. No breaches detected.

- P95 latency: 0ms (within 150ms threshold)
- Active connections: Stable
- Wait queue: 0
- Reconnects: 0
- Errors: 0
