# Issue A: A2 /ready Endpoint Enhancement

## Status: ENHANCEMENT (Already Implemented, Adding Feature Flag + Extended Checks)

## Current State
- `/ready` endpoint exists and returns 200 OK
- Checks: DB connectivity, Stripe configuration
- P95: 141ms (under 150ms target)

## Enhancement Scope
1. Add feature flag for new checks
2. Add upstream A1 OIDC reachability check
3. Add queue/event bus connectivity check
4. Improve error handling with detailed degraded states

## Design

### Before
```
/ready → check DB → check Stripe config → return status
```

### After (Feature Flagged)
```
/ready → check DB → check Stripe → check A1 OIDC → check EventBus → return detailed status
```

## Feature Flag
```python
READY_EXTENDED_CHECKS = os.getenv("READY_EXTENDED_CHECKS", "false").lower() == "true"
```

## Risk Analysis
- **Low Risk**: Additive changes only
- **Rollback**: Set `READY_EXTENDED_CHECKS=false` to disable new checks
- **Performance**: May add 50-100ms if upstream checks enabled

## Files Modified
- `main.py` (readiness_check function)
- `config.py` (feature flag)
