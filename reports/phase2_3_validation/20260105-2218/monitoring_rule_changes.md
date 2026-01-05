# Monitoring Rule Changes
**Phase**: 2 (Implementation)
**Date**: 2026-01-05T22:20:00Z

## Current Issues (from Phase 1 Audit)

| Alert | Issue | Fix |
|-------|-------|-----|
| AUTH_FAILURE | Single failures trigger alert | Require >5% error rate |
| A2_DOWN | Transient 404s trigger | Increase `for` duration |
| Revenue Blocked | Persists after recovery | Add auto-clear logic |

## Proposed Changes

### 1. AUTH_FAILURE Rate-Based Alert

**Before**:
```yaml
- alert: AuthFailure
  expr: auth_errors > 0
  for: 1m
```

**After**:
```yaml
- alert: AuthFailure
  expr: rate(auth_errors_total[5m]) > 0.05  # 5% threshold
  for: 3m  # Sustained
  labels:
    severity: warning
  annotations:
    summary: "Auth error rate exceeds 5% for 3+ minutes"
```

### 2. Service Down Duration

**Before**:
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 1m
```

**After**:
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 5m  # Wait longer for transient issues
  labels:
    severity: critical
```

### 3. Latency Alert with Proper P95

```yaml
- alert: HighP95Latency
  expr: |
    histogram_quantile(0.95, 
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le, app)
    ) > 0.150
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "{{ $labels.app }} P95 latency exceeds 150ms"
```

### 4. Revenue Blocked - Operational Mode Detection

```yaml
- alert: RevenueBlocked
  expr: |
    revenue_events_total{stripe_mode="live", namespace=""} == 0
    AND on() a3_orchestration_last_run_seconds > 3600
  for: 15m
  labels:
    severity: info
    type: operational_mode
  annotations:
    summary: "No revenue - A3 orchestration may need to run"
```

## Noise Reduction Estimates

| Alert | Before (daily) | After (daily) | Reduction |
|-------|----------------|---------------|-----------|
| AUTH_FAILURE | ~20 | ~2 | 90% |
| ServiceDown | ~5 | ~1 | 80% |
| HighLatency | ~10 | ~3 | 70% |

## Implementation Notes

1. Changes require access to monitoring config (Prometheus/Alertmanager)
2. Test in staging first
3. Monitor alert volume for 48 hours post-change
4. Adjust thresholds if needed

---

**Status**: READY FOR APPLICATION
