"""
Stabilization Countdown Router - CEO Directive (2026-01-15)

Endpoints for final 5-minute stabilization countdown with:
- Real-time status
- Manual tick trigger
- Gate 3 evaluation
- CEO page at 09:21:13Z
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from services.stabilization_countdown import stabilization, StabilizationState
from services.a3_a6_circuit_breaker import FEATURE_FLAG_ENABLED
from utils.logger import get_logger

logger = get_logger("stabilization_router")
router = APIRouter(prefix="/stabilization", tags=["Stabilization Countdown"])


@router.get("/status")
async def get_stabilization_status():
    """
    Get current stabilization countdown status.
    
    Returns full state including:
    - Green window tracking
    - Gate 3 criteria
    - Breaker flag status
    - Freeze status
    - Recent A8 events
    """
    return stabilization.get_status()


@router.post("/tick")
async def trigger_tick():
    """
    Trigger one tick of the stabilization countdown.
    
    This performs:
    - Metrics check
    - Green window update
    - Gate 3 criteria update
    - A8 heartbeat (every 60s)
    - State transitions
    """
    result = await stabilization.tick()
    return result


@router.post("/evaluate-gate3")
async def evaluate_gate3():
    """
    Evaluate Gate 3 criteria.
    
    Pass requires:
    - 30-min green window
    - Breaker CLOSED for 10 min
    - Backlog <10 for 10 min
    - Budget <80%
    - Compute ≤2x baseline
    
    On pass: Provider canary 1% → 5% → 25% → 100%
    On miss: Continue Student-Only; reschedule
    """
    result = await stabilization.evaluate_gate3()
    return result


@router.get("/ceo-page")
async def ceo_page():
    """
    CEO Page at 09:21:13Z
    
    Returns:
    - "Green Achieved" or "Timer Reset"
    - A8 event_id
    - evidence_hash
    """
    status = stabilization.get_status()
    
    if status["green_window"]["meets_30m"]:
        page_type = "Green Achieved"
        message = "30-minute continuous green window achieved. No-change freeze active until Gate 3 (10:11:13Z)."
    elif status["green_window"]["last_breach_reason"]:
        page_type = "Timer Reset"
        message = f"Timer reset due to: {status['green_window']['last_breach_reason']}. New stabilization window started."
    else:
        page_type = "Countdown Active"
        message = f"Green window in progress: {status['green_window']['duration_sec']:.1f}s / 1800s"
    
    recent_event = status["recent_a8_events"][-1] if status["recent_a8_events"] else {}
    
    return {
        "page_time": datetime.utcnow().isoformat() + "Z",
        "page_type": page_type,
        "message": message,
        "a8_event_id": recent_event.get("event_id", "pending"),
        "evidence_hash": status["evidence_hash"],
        "green_window": status["green_window"],
        "gate3_criteria": status["gate3_criteria"],
        "breaker_flag_status": status["breaker_flag_status"],
        "freeze_active": status["freeze_active"],
        "student_only_mode": status["student_only_mode"],
        "provider_canary_pct": status["provider_canary_pct"]
    }


@router.post("/start-countdown")
async def start_countdown(background_tasks: BackgroundTasks):
    """
    Start the 5-minute stabilization countdown.
    
    This arms the countdown timer and begins:
    - Continuous green window tracking
    - 60s A8 heartbeat publishing
    - Auto-actions on green/breach
    """
    logger.info("Stabilization countdown started")
    
    async def countdown_loop():
        for i in range(300):
            await stabilization.tick()
            await asyncio.sleep(1)
        logger.info("5-minute countdown complete")
    
    background_tasks.add_task(countdown_loop)
    
    return {
        "status": "COUNTDOWN_STARTED",
        "duration_sec": 300,
        "actions_armed": [
            "Green window tracking (30-min target)",
            "Timer reset on breach",
            "Maintenance auto-send",
            "A8 heartbeat every 60s",
            "Probe tapering at 5 consecutive minutes ≤1.0s P95"
        ],
        "gate3_time": "10:11:13Z"
    }


@router.post("/simulate-breach")
async def simulate_breach(p95_ms: float = 1500.0, error_rate: float = 0.01):
    """
    Simulate a breach for testing timer reset logic.
    
    WARNING: This will trigger maintenance auto-send if in countdown state.
    """
    from services.stabilization_countdown import stabilization
    
    is_green, breach_reason = stabilization.green_window.update(p95_ms, error_rate)
    
    if not is_green and breach_reason:
        result = await stabilization.handle_timer_reset(breach_reason)
        return result
    
    return {"status": "NO_BREACH", "metrics": {"p95_ms": p95_ms, "error_rate": error_rate}}


@router.post("/simulate-green-30m")
async def simulate_green_30m():
    """
    Simulate 30-minute green window achievement for testing.
    
    This will trigger:
    - Cancel Maintenance auto-send
    - Enter no-change freeze
    - Post success event to A8
    """
    stabilization.green_window.started_at = stabilization.green_window.last_check - 1801
    stabilization.green_window.consecutive_green_seconds = 1801
    stabilization.green_window.meets_30m = True
    
    import hashlib
    import json
    metrics = stabilization.get_metrics()
    evidence_hash = hashlib.sha256(
        json.dumps(metrics, sort_keys=True, default=str).encode()
    ).hexdigest()
    
    result = await stabilization.handle_green_achieved(evidence_hash)
    return result
