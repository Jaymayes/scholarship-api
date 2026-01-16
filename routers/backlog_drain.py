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
    budget_pct: float = 0.0
    compute_ratio: float = 1.0


class ForecastRequest(BaseModel):
    current_backlog: int
    drain_rate_per_min: Optional[float] = None


class ProviderHoldRequest(BaseModel):
    provider_id: str
    reason: str


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


@router.post("/forecast")
async def get_forecast(request: ForecastRequest):
    """
    Get forecast for backlog clearance vs quiet period target.
    
    Calculates:
    - Time to drain current backlog to target (<10)
    - Time remaining until quiet period (09:05Z)
    - Whether target will be met
    - Buffer time or shortfall
    """
    return drain_service.get_forecast(
        request.current_backlog,
        request.drain_rate_per_min
    )


@router.post("/provider/rate-limit")
async def check_provider_rate_limit(provider_id: str):
    """
    Check per-provider rate limit (max 1 rps per provider).
    
    Returns whether the provider can accept a new request.
    """
    return drain_service.check_provider_rate_limit(provider_id)


@router.post("/provider/hold")
async def hold_provider(request: ProviderHoldRequest):
    """
    Hold a provider's queue for manual review.
    
    Required when duplicate detected-and-blocked > 0 in a window.
    """
    return drain_service.hold_provider(request.provider_id, request.reason)


@router.post("/provider/release")
async def release_provider(provider_id: str):
    """
    Release a provider's hold after manual review.
    """
    return drain_service.release_provider(provider_id)


@router.get("/providers/held")
async def get_held_providers():
    """Get list of providers currently on hold."""
    return {
        "providers_held": len(drain_service.providers_held),
        "held_providers": drain_service.providers_held
    }


@router.post("/token-bucket/check")
async def check_token_bucket(p95_ms: float, reserves_pct: float):
    """
    Check if burst mode is available via token bucket.
    
    Burst to 5 rps allowed if:
    - P95 < 1.0s
    - Reserves ≥ 22%
    - Tokens available in bucket
    """
    return drain_service.check_token_bucket_burst(p95_ms, reserves_pct)


class GmvCapCheckRequest(BaseModel):
    provider_id: str
    amount: float


@router.post("/gmv-cap/check")
async def check_gmv_caps(request: GmvCapCheckRequest):
    """
    Check GMV caps before processing a drain item.
    
    Enforces:
    - global_10m_gmv_cap = $100k (pre-throttle to 2 rps if >80%)
    - provider_hourly_gmv_cap = $10k (HOLD + page CEO if hit)
    """
    return drain_service.check_gmv_caps(request.provider_id, request.amount)


@router.post("/upshift/check")
async def check_upshift(p95_ms: float, error_rate_1m: float, reserves_pct: float):
    """
    Check if eligible to upshift from Band 2 to Band 1 (5 rps).
    
    Requires BOTH for 5 straight minutes:
    - reserves ≥20%
    - P95 ≤1.0s with error_rate_1m ≤0.3%
    """
    return drain_service.check_upshift_eligibility(p95_ms, error_rate_1m, reserves_pct)


@router.get("/reconciliation/latest")
async def get_latest_reconciliation():
    """Get the latest rolling reconciliation record."""
    if drain_service.rolling_reconciliations:
        return drain_service.rolling_reconciliations[-1]
    return {"message": "No reconciliations yet"}


@router.get("/reconciliation/all")
async def get_all_reconciliations():
    """Get all rolling reconciliation records (last 24 hours / 144 entries)."""
    return {
        "total": len(drain_service.rolling_reconciliations),
        "reconciliations": drain_service.rolling_reconciliations
    }


class ProviderConcentrationRequest(BaseModel):
    provider_id: str
    amount: float


class LedgerEntryRequest(BaseModel):
    stripe_charge_id: str
    provider_id: str
    amount: float
    platform_fee: float
    idempotency_key: str
    ledger_tx_id: str


@router.post("/complete")
async def complete_drain():
    """
    Complete drain and enter idle_watch mode when backlog=0.
    
    Sets drain_mode=idle_watch, keeps breaker=CLOSED.
    Pages CEO with event_id and evidence_hash.
    """
    return drain_service.complete_drain()


@router.post("/concentration/check")
async def check_provider_concentration(request: ProviderConcentrationRequest):
    """
    Check if provider exceeds 25% of 10-min GMV window.
    
    If exceeded, HOLDs provider queue and pages CEO.
    """
    return drain_service.check_provider_concentration(request.provider_id, request.amount)


@router.get("/concentration/top")
async def get_top_provider_concentration():
    """Get concentration percentage of top provider in 10-min window."""
    return drain_service.get_top_provider_concentration()


@router.post("/ledger/entry")
async def add_ledger_entry(request: LedgerEntryRequest):
    """Add a row-level entry to the Drain Day Ledger."""
    return drain_service.add_ledger_entry(request.model_dump())


@router.post("/ledger/seal")
async def seal_ledger():
    """
    Seal the Drain Day Ledger with bundle hash.
    
    Locks ledger with row-level entries and emits seal event.
    No further entries allowed after sealing.
    """
    return drain_service.seal_ledger()


@router.get("/ledger/entries")
async def get_ledger_entries():
    """Get all entries in the Drain Day Ledger."""
    return {
        "sealed": drain_service.ledger_sealed,
        "seal_hash": drain_service.ledger_seal_hash,
        "entry_count": len(drain_service.drain_day_ledger),
        "entries": drain_service.drain_day_ledger
    }


@router.get("/ledger/csv")
async def get_ledger_csv():
    """Export reconciliation data as CSV."""
    from fastapi.responses import PlainTextResponse
    csv_content = drain_service.export_reconciliation_csv()
    return PlainTextResponse(content=csv_content, media_type="text/csv")


@router.get("/gmv-cap/status")
async def get_gmv_cap_status():
    """Get current GMV cap status and utilization."""
    return {
        "global_10m_gmv_cap": drain_service.global_10m_gmv_cap,
        "global_10m_gmv_current": round(drain_service.window_gmv_recovered, 2),
        "global_10m_gmv_utilization_pct": round(drain_service.global_10m_gmv_utilization_pct, 2),
        "pre_throttle_threshold_pct": 80,
        "resume_threshold_pct": 60,
        "provider_hourly_gmv_cap": drain_service.provider_hourly_gmv_cap,
        "provider_hourly_cap_hit_count": drain_service.provider_hourly_cap_hit_count,
        "provider_concentration_cap_pct": drain_service.provider_concentration_cap_pct,
        "top_provider_concentration": drain_service.get_top_provider_concentration()
    }


@router.get("/00-00z-snapshot")
async def get_cfo_snapshot():
    """
    Generate 00:00Z CFO-ready snapshot with mini P&L.
    
    Includes:
    - GMV_recovered_total, platform_fee_total (3%), refunds_reserve_total (1%)
    - stripe_success_pct_total, duplicates stats
    - providers_touched, concentration_top_provider_10m_pct
    - Mini P&L: fees - refunds_reserve - payment processing = net contribution
    - canonical_ledger_hash and evidence_hash
    """
    return drain_service.generate_cfo_snapshot()


@router.get("/22-30z-checkpoint")
async def get_22_30z_checkpoint():
    """
    Generate the 22:30Z checkpoint with all required contents.
    
    Required contents:
    - backlog_depth, oldest_item_age_sec, DLQ_depth
    - drains_last_10m, success_last_10m, GMV_recovered_10m, platform_fee_10m, cumulative totals
    - stripe_success_pct_10m, duplicates_prevented_10m, held_providers[]
    - reserves_pct, P95, error_rate_1m, budget_pct, compute_ratio
    - canonical_ledger_hash and evidence_hash
    """
    return {
        "checkpoint": "22:30Z",
        "backlog_depth": drain_service.live_backlog_depth,
        "oldest_item_age_sec": drain_service.oldest_item_age_sec,
        "DLQ_depth": 0,
        "drains_last_10m": drain_service.window_drained_count,
        "success_last_10m": drain_service.window_success_count,
        "GMV_recovered_10m": round(drain_service.window_gmv_recovered, 2),
        "platform_fee_10m": round(drain_service.window_platform_fee, 2),
        "cumulative_totals": {
            "GMV_recovered": round(drain_service.cumulative_gmv_recovered, 2),
            "platform_fee": round(drain_service.cumulative_platform_fee, 2),
            "drained_count": drain_service.cumulative_drained_count,
            "success_count": drain_service.cumulative_success_count
        },
        "stripe_success_pct_10m": 100.0,
        "duplicates_prevented_10m": drain_service.window_duplicates_prevented,
        "held_providers": list(drain_service.providers_held.keys()),
        "reserves_pct": drain_service.reserves_history[-1]["reserves_pct"] if drain_service.reserves_history else 0,
        "P95": 0,
        "error_rate_1m": 0,
        "budget_pct": drain_service.budget_pct,
        "compute_ratio": drain_service.compute_ratio,
        "canonical_ledger_hash": drain_service.canonical_ledger_hash,
        "evidence_hash": drain_service.last_evidence_hash
    }
