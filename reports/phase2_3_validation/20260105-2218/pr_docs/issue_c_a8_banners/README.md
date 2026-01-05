# Issue C: A8 Stale Incident Banners

## Status: NEW IMPLEMENTATION (Requires A8 Project Access)

## Problem
- Incident banners persist in A8 dashboard after services recover
- Creates "false positive" perception where dashboard shows warnings despite 8/8 apps healthy
- Requires manual intervention to clear banners

## Solution
1. Add TTL (Time-To-Live) to incident records
2. Auto-clear banners when service recovers and stays green for TTL period
3. Add admin endpoint to manually clear stale banners
4. Protect admin endpoint with auth

## Design

### Before
```
Service unhealthy → Banner created → Banner persists forever
                                     (manual clear only)
```

### After
```
Service unhealthy → Banner created with TTL
Service recovers → Start grace period timer
After TTL (15min green) → Auto-clear banner
Admin → Can clear immediately via API
```

## Feature Flag
```python
BANNER_AUTO_CLEAR_ENABLED = os.getenv("BANNER_AUTO_CLEAR_ENABLED", "false").lower() == "true"
BANNER_TTL_MINUTES = int(os.getenv("BANNER_TTL_MINUTES", "15"))
```

## Risk Analysis
- **Low Risk**: Additive UX improvement
- **Rollback**: Set `BANNER_AUTO_CLEAR_ENABLED=false`
- **Edge Case**: Flapping services handled with reset logic

## Database Migration
```sql
ALTER TABLE incidents ADD COLUMN last_healthy_at TIMESTAMP NULL;
ALTER TABLE incidents ADD COLUMN auto_cleared BOOLEAN DEFAULT FALSE;
ALTER TABLE incidents ADD COLUMN cleared_at TIMESTAMP NULL;
```

## Files to Create/Modify
- `models/incident.py` (add TTL fields)
- `services/incident_reconciler.py` (auto-clear logic)
- `routes/admin.py` (admin clear endpoint)
- `tasks/banner_cleanup.py` (scheduled job)
