"""
Backlog Drain Router

Endpoints for controlled backlog drain operations with:
- Start/pause controls
- 10-minute heartbeat generation
- Status monitoring
- Item validation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from services.backlog_drain import drain_service

router = APIRouter(prefix="/drain", tags=["Backlog Drain"])


class DrainItemRequest(BaseModel):
    idempotency_key: str
    transaction_id: Optional[str] = None
    provider_id: Optional[str] = None
    provider_account_status: str = "active"
    provider_capabilities: List[str] = ["transfers"]
    amount: float = 0.0


class DrainResultRequest(BaseModel):
    item: DrainItemRequest
    success: bool
    amount: float = 0.0


class MetricsRequest(BaseModel):
    dlq_depth: int = 0
    provider_backlog_depth: int = 0
    p95_ms: float = 0.0
    error_rate_1m: float = 0.0
    breaker_state: str = "HALF_OPEN"
    autoscaling_reserves_pct: float = 20.0


@router.post("/start")
async def start_drain():
    """
    Start controlled backlog drain.
    
    Initiates drain at ≤5 rps with:
    - Rate guard active
    - Stop-loss gates armed
    - Evidence cadence enabled
    - Quiet period awareness
    """
    return drain_service.start_drain()


@router.post("/pause")
async def pause_drain(reason: str = "manual"):
    """Pause the drain with reason."""
    return drain_service.pause_drain(reason)


@router.get("/status")
async def get_drain_status():
    """Get current drain status."""
    return drain_service.get_status()


@router.post("/validate-item")
async def validate_drain_item(item: DrainItemRequest):
    """
    Validate item before drain execution.
    
    Checks:
    - X-Idempotency-Key present and not seen in 30 days
    - transaction_id not in settled_ledger
    - Provider account status active + capabilities=transfers
    """
    return drain_service.validate_drain_item(item.model_dump())


@router.post("/record-result")
async def record_drain_result(request: DrainResultRequest):
    """Record result of a drain operation."""
    drain_service.record_drain_result(
        request.item.model_dump(),
        request.success,
        request.amount
    )
    return {
        "recorded": True,
        "success": request.success,
        "amount": request.amount
    }


@router.post("/heartbeat")
async def generate_heartbeat(metrics: MetricsRequest):
    """
    Generate 10-minute drain heartbeat.
    
    Includes:
    - drain_rps and drain_mode
    - GMV_recovered_10m, platform_fee_10m, cumulative totals
    - duplicate_prevented_10m, DLQ_depth, backlog_depth
    - stripe_success_pct_10m
    - breaker_state, autoscaling_reserves_pct, P95, error_rate_1m
    - evidence_hash and emitting_nodes
    
    Also checks stop-loss gates and quiet period.
    """
    return drain_service.generate_10min_heartbeat(metrics.model_dump())


@router.post("/check-stop-loss")
async def check_stop_loss(metrics: MetricsRequest):
    """
    Check stop-loss gates.
    
    Gates:
    - DLQ > 0
    - provider_backlog_depth > 30
    - P95 ≥ 1.25s for 60s OR error_rate_1m ≥ 0.5% for 60s
    - Stripe success < 99.5% over last 50 drain transactions
    """
    result = drain_service.check_stop_loss_gates(metrics.model_dump())
    if result:
        return result
    return {
        "stop_loss_triggered": False,
        "all_gates_pass": True,
        "metrics": metrics.model_dump()
    }


@router.post("/check-rate-guard")
async def check_rate_guard(reserves_pct: float):
    """
    Check and adjust rate based on reserves.
    
    - Auto-reduce to 2 rps if reserves 15-17% for 3 consecutive minutes
    - Resume to 5 rps after reserves ≥20% for 5 minutes
    """
    return drain_service.check_rate_guard(reserves_pct)


@router.get("/heartbeats")
async def get_heartbeats():
    """Get all recorded heartbeats."""
    return {
        "total_heartbeats": len(drain_service.heartbeats),
        "heartbeats": drain_service.heartbeats[-10:]
    }


@router.get("/quiet-period")
async def check_quiet_period():
    """Check quiet period status."""
    return drain_service.check_quiet_period()
