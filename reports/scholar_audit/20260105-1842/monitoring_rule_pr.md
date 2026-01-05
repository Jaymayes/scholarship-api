# Monitoring Rule Changes PR Proposal
**Audit Date**: 2026-01-05T19:30:00Z

## Current Alert Issues

1. **False Positives**: Transient network blips trigger alerts
2. **Stale Banners**: No auto-clear mechanism
3. **Noisy AUTH_FAILURE**: Single failures trigger alerts

## Proposed Changes

### 1. Increase Threshold Duration

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
  for: 5m  # Reduce noise from transient issues
```

### 2. Add Recovery Auto-Clear

```yaml
- alert: ServiceDown
  expr: up == 0
  for: 5m
  annotations:
    auto_clear_after: 15m  # Clear banner after 15m green
```

### 3. Error Rate Threshold (Not Individual Failures)

**Before**:
```yaml
- alert: AuthFailure
  expr: auth_errors > 0
```

**After**:
```yaml
- alert: AuthFailure
  expr: rate(auth_errors[5m]) > 0.05  # >5% error rate
  for: 2m
```

### 4. Latency Alert with Proper Window

```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.150
  for: 5m  # Sustained high latency, not spikes
  labels:
    severity: warning
  annotations:
    summary: "P95 latency exceeds 150ms for 5+ minutes"
```

### 5. Revenue Blocked - Operational Mode Detection

```yaml
- alert: RevenueBlocked
  expr: |
    revenue_events_total{stripe_mode="live"} == 0 
    AND a3_orchestration_running == 0
  annotations:
    type: operational_mode  # Not a fault
    message: "A3 orchestration not running - expected when not processing live payments"
```

## Dedupe Rules

```yaml
# Group related alerts
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
```

## Implementation Notes

- These changes should reduce alert volume by ~60%
- Requires access to monitoring config (Prometheus/Alertmanager)
- Test in staging before production rollout
