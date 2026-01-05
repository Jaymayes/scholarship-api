# Phase 2 PR Proposals (HUMAN_APPROVAL_REQUIRED)
**Audit Date**: 2026-01-05
**Mode**: Read-Only/Diagnostic - No production changes

---

## Issue A: A2 /ready Endpoint (P1)

### Status: ✅ ALREADY IMPLEMENTED

**Current State**:
```bash
$ curl http://localhost:5000/ready
{
    "status": "ready",
    "services": {
        "api": "ready",
        "database": "ready",
        "stripe": "configured"
    }
}
HTTP Status: 200
```

**Code Location**: `main.py` line 940

**Conclusion**: No PR needed. A2 /ready is fully functional with dependency checks.

---

## Issue B: A7 Ingestion Latency >150ms (P1)

### Status: ⚠️ REQUIRES A7 PROJECT ACCESS

**Proposal** (for A7 team):

```python
# Option 1: FastAPI BackgroundTasks (minimal change)
from fastapi import BackgroundTasks

@router.post("/ingest", status_code=202)
async def ingest_event(event: Event, background_tasks: BackgroundTasks):
    event_id = str(uuid.uuid4())
    background_tasks.add_task(persist_event_async, event, event_id)
    return {"accepted": True, "event_id": event_id}

async def persist_event_async(event: Event, event_id: str):
    # Idempotent DB write with event_id as key
    await db.execute(
        "INSERT INTO events (id, data) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
        event_id, event.dict()
    )
```

**Success Criteria**: P95 ≤100ms at 100-event load
**Rollback Plan**: Revert to synchronous writes

**Action Required**: A7 team to implement in provider-register project

---

## Issue C: A8 Stale Incident Banners (P2)

### Status: ⚠️ REQUIRES A8 PROJECT ACCESS

**Proposal** (for A8 team):

```python
# Auto-clear incidents after X minutes of green
INCIDENT_TTL_MINUTES = 15

async def reconcile_incidents():
    """Run every 5 minutes to clear stale banners"""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=INCIDENT_TTL_MINUTES)
    
    # Find incidents with last_unhealthy < cutoff AND current_status = 'green'
    await db.execute("""
        DELETE FROM incidents 
        WHERE last_unhealthy_at < $1 
        AND current_status = 'green'
    """, cutoff)
```

**Admin Action**: Add "Clear Stale Incidents" button in A8 dashboard

**Rollback Plan**: Remove auto-clear, keep manual button

**Action Required**: A8 team to implement in auto-com-center project

---

## Issue D: Revenue Visualization Drift (P0 perception)

### Status: ⚠️ REQUIRES A8 PROJECT ACCESS

**Proposal** (for A8 team):

```python
# Demo Mode toggle for test transactions
@router.get("/api/revenue/summary")
async def revenue_summary(demo_mode: bool = False):
    if demo_mode:
        # Include STRIPE_MODE=test events with "Test Data" label
        query = "SELECT * FROM revenue_events WHERE stripe_mode IN ('live', 'test')"
        label = "Demo Mode: Includes Test Data"
    else:
        # Production: Only live transactions
        query = "SELECT * FROM revenue_events WHERE stripe_mode = 'live'"
        label = "Live Data"
    
    return {"label": label, "data": await db.fetch_all(query)}
```

**Visual Treatment**: Clear "TEST DATA" badge overlay on Demo Mode tiles

**Rollback Plan**: Remove demo_mode parameter, keep live-only

**Action Required**: A8 team to implement in auto-com-center project

---

## Risk Matrix

| Issue | Priority | Risk | Effort | A2 Scope |
|-------|----------|------|--------|----------|
| A: A2 /ready | P1 | Low | Done | ✅ COMPLETE |
| B: A7 latency | P1 | Medium | 2-4h | ❌ A7 project |
| C: A8 banners | P2 | Low | 2h | ❌ A8 project |
| D: Revenue viz | P0 | Low | 4h | ❌ A8 project |

---

## Summary

**From A2 (scholarship_api) perspective**:
- ✅ Issue A is RESOLVED - /ready endpoint exists and returns 200
- ⚠️ Issues B, C, D require access to A7 and A8 projects respectively

**HUMAN_APPROVAL_REQUIRED** to proceed with Issues B, C, D in their respective projects.
