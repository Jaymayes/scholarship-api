# PR Proposal: Issue B - A7 Async Ingestion

## Status: ⚠️ CONFIRMED - REQUIRES A7 PROJECT ACCESS

### Problem Evidence

**A7 /health Latency (10 samples)**:

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| P50 | 163.2ms | ≤150ms | ❌ FAIL |
| P95 | 320.5ms | ≤150ms | ❌ FAIL |
| P99 | 320.5ms | ≤150ms | ❌ FAIL |

**Root Cause Hypothesis**: SendGrid or other synchronous third-party calls on request path add ~170ms+ latency.

### Proposed Fix (Option 1: BackgroundTasks)

```python
from fastapi import BackgroundTasks
import uuid

@router.post("/ingest", status_code=202)
async def ingest_event(event: Event, background_tasks: BackgroundTasks):
    """Return 202 immediately, process async"""
    event_id = str(uuid.uuid4())
    background_tasks.add_task(process_event_async, event, event_id)
    return {"accepted": True, "event_id": event_id}

async def process_event_async(event: Event, event_id: str):
    """Process in background - no blocking on request path"""
    # DB write with idempotency
    await db.execute(
        "INSERT INTO events (id, data) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
        event_id, event.dict()
    )
    # SendGrid or other third-party calls here (async)
    await send_notification_async(event)
```

### Proposed Fix (Option 2: Celery/RQ Worker)

```python
from celery import shared_task

@router.post("/ingest", status_code=202)
async def ingest_event(event: Event):
    event_id = str(uuid.uuid4())
    process_event_task.delay(event.dict(), event_id)
    return {"accepted": True, "event_id": event_id}

@shared_task
def process_event_task(event_data: dict, event_id: str):
    # All blocking I/O in worker
    db_write(event_id, event_data)
    sendgrid_notify(event_data)
```

### Expected Improvement

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| P95 | 320ms | ≤100ms | 70%+ reduction |

### Rollback Plan

1. Revert to synchronous endpoint
2. Remove background task/worker config
3. Restart A7 service

### Action Required

This fix requires access to the A7 (auto_page_maker) project. Cannot be implemented from A2.
