"""
A7 Async Ingestion Implementation
File: app/routes/ingest.py

This implementation moves third-party calls off the hot path using FastAPI BackgroundTasks.
"""
import os
import uuid
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/v1", tags=["ingestion"])

# Feature flag
ASYNC_INGESTION_ENABLED = os.getenv("ASYNC_INGESTION_ENABLED", "false").lower() == "true"

# Idempotency store (in production, use Redis)
_idempotency_store: Dict[str, dict] = {}
IDEMPOTENCY_TTL_SECONDS = 86400  # 24 hours

# Circuit breaker state
_circuit_state = {
    "state": "closed",  # closed, open, half-open
    "failures": 0,
    "last_failure": 0,
    "threshold": 5,
    "recovery_time": 30
}

class IngestEvent(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    actor_id: Optional[str] = None
    source: Optional[str] = None

class IngestResponse(BaseModel):
    accepted: bool
    event_id: str
    processing: str  # "sync" or "async"
    status: str

def check_circuit_breaker() -> bool:
    """Check if circuit breaker allows requests"""
    state = _circuit_state
    
    if state["state"] == "closed":
        return True
    
    if state["state"] == "open":
        if time.time() - state["last_failure"] > state["recovery_time"]:
            state["state"] = "half-open"
            return True
        return False
    
    # half-open: allow one request
    return True

def record_failure():
    """Record a failure for circuit breaker"""
    state = _circuit_state
    state["failures"] += 1
    state["last_failure"] = time.time()
    
    if state["failures"] >= state["threshold"]:
        state["state"] = "open"

def record_success():
    """Record success, reset circuit breaker"""
    state = _circuit_state
    state["failures"] = 0
    state["state"] = "closed"

async def process_event_async(event_id: str, event: IngestEvent):
    """
    Background task to process event with retries and circuit breaker.
    This runs AFTER the 202 response is sent.
    """
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        if not check_circuit_breaker():
            # Circuit open, skip external calls
            _idempotency_store[event_id]["status"] = "circuit_open"
            return
        
        try:
            # Process the event (e.g., SendGrid, DB write, A8 telemetry)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Example: Send to A8 telemetry
                a8_url = os.getenv("EVENT_BUS_URL", "https://auto-com-center-jamarrlmayes.replit.app")
                response = await client.post(
                    f"{a8_url}/events",
                    json={
                        "event_type": event.event_type,
                        "event_id": event_id,
                        "payload": event.payload,
                        "source": event.source or "A7",
                        "occurred_at": datetime.utcnow().isoformat()
                    },
                    headers={
                        "x-scholar-protocol": "v3.5.1",
                        "x-app-label": "auto_page_maker",
                        "x-event-id": event_id
                    }
                )
                
                if response.status_code in (200, 201, 202):
                    record_success()
                    _idempotency_store[event_id]["status"] = "completed"
                    return
                else:
                    raise Exception(f"A8 returned {response.status_code}")
                    
        except Exception as e:
            record_failure()
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)
            else:
                _idempotency_store[event_id]["status"] = "failed"
                _idempotency_store[event_id]["error"] = str(e)

@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest_event(
    event: IngestEvent,
    background_tasks: BackgroundTasks,
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Ingest an event with async processing.
    
    Returns 202 Accepted immediately; processing happens in background.
    Use X-Idempotency-Key header to prevent duplicate processing.
    """
    # Generate or use provided idempotency key
    event_id = x_idempotency_key or str(uuid.uuid4())
    
    # Check idempotency
    if event_id in _idempotency_store:
        existing = _idempotency_store[event_id]
        return IngestResponse(
            accepted=True,
            event_id=event_id,
            processing="cached",
            status=existing.get("status", "processing")
        )
    
    # Store idempotency record
    _idempotency_store[event_id] = {
        "created_at": time.time(),
        "status": "processing",
        "event_type": event.event_type
    }
    
    if ASYNC_INGESTION_ENABLED:
        # Async path: queue for background processing
        background_tasks.add_task(process_event_async, event_id, event)
        return IngestResponse(
            accepted=True,
            event_id=event_id,
            processing="async",
            status="queued"
        )
    else:
        # Sync path (fallback): process immediately
        await process_event_async(event_id, event)
        return IngestResponse(
            accepted=True,
            event_id=event_id,
            processing="sync",
            status=_idempotency_store[event_id]["status"]
        )

@router.get("/ingest/{event_id}/status")
async def get_event_status(event_id: str):
    """Check the processing status of an ingested event"""
    if event_id not in _idempotency_store:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return _idempotency_store[event_id]
