# PR Proposal: Issue C - A8 Stale Incident Banners

## Status: ⚠️ REQUIRES A8 PROJECT ACCESS

### Problem

Incident banners persist in A8 dashboard even after services recover. This causes "false positive" alerts where dashboard shows red/warning states despite all 8 apps being healthy.

### Evidence

**Current State (2026-01-05T18:43:00Z)**:
- All 8 apps: /health = 200, /ready = 200
- Dashboard still shows: "Revenue Blocked", "A2 Down" banners (stale)

### Root Cause

No TTL or auto-clear mechanism on incident records. Banners require manual clearing.

### Proposed Fix

```python
from datetime import datetime, timedelta

INCIDENT_TTL_MINUTES = 15

# 1. Add TTL to incident schema
class Incident(Base):
    id = Column(Integer, primary_key=True)
    app_id = Column(String)
    severity = Column(String)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_unhealthy_at = Column(DateTime, default=datetime.utcnow)
    current_status = Column(String, default='red')  # red, yellow, green

# 2. Auto-clear reconciliation job (every 5 minutes)
async def reconcile_incidents():
    """Clear stale incidents after sustained green period"""
    cutoff = datetime.utcnow() - timedelta(minutes=INCIDENT_TTL_MINUTES)
    
    await db.execute("""
        UPDATE incidents 
        SET current_status = 'cleared'
        WHERE last_unhealthy_at < $1 
        AND current_status = 'green'
    """, cutoff)

# 3. Admin clear endpoint
@router.post("/api/admin/clear-stale-incidents")
async def clear_stale_incidents(admin_token: str = Header(...)):
    verify_admin(admin_token)
    result = await db.execute(
        "DELETE FROM incidents WHERE current_status IN ('green', 'cleared')"
    )
    return {"cleared": result.rowcount}
```

### UX Acceptance Tests

1. Service goes unhealthy → Banner appears within 60s
2. Service recovers → Status changes to 'green' within 60s
3. After 15 minutes of green → Banner auto-clears
4. Admin can manually clear stale banners

### Rollback Plan

1. Remove auto-clear job
2. Keep manual admin clear as safety net
3. Revert schema migration

### Action Required

This fix requires access to the A8 (auto_com_center) project. Cannot be implemented from A2.
