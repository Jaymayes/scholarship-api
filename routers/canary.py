"""
SEV-2 Canary Endpoints - CIR-20260119-001
Internal endpoints for canary sequence control
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from services.canary_controller import canary_controller, CanaryMetrics
from services.a8_telemetry import a8_telemetry

router = APIRouter(prefix="/api/internal/canary", tags=["canary-sev2"])

class PreCanaryGatesRequest(BaseModel):
    a1_db_connected: bool = False
    a1_auth_5xx: int = 999
    a1_pool_utilization: float = 100
    a1_p95_ms: float = 999
    a3_concurrency: int = 999
    a3_queues_paused: bool = False
    a3_breaker: str = "open"
    a3_db_url_clean: bool = False
    a5_200_ok: bool = False
    a5_markers: List[str] = []
    a7_200_ok: bool = False
    a7_markers: List[str] = []
    a8_cir_active: bool = True
    confirmations_3of3: int = 0

class MetricsRequest(BaseModel):
    a1_db_connected: bool = True
    a1_pool_in_use: int = 0
    a1_pool_idle: int = 10
    a1_pool_total: int = 10
    a1_pool_utilization_pct: float = 0
    a1_auth_5xx: int = 0
    a1_p95_ms: float = 50
    a3_breaker_state: str = "half_open"
    a3_req_rate: float = 0
    a3_error_rate: float = 0
    a3_backoff_state: str = "none"
    a3_queue_depth: int = 0
    a3_dlq_count: int = 0
    a5_http_200_markers: List[str] = []
    a5_p95_ms: float = 50
    a7_http_200_markers: List[str] = []
    a7_p95_ms: float = 50
    a6_p95_ms: float = 50
    a6_5xx_rate: float = 0
    a8_p95_ms: float = 50
    a8_5xx_rate: float = 0
    cost_compute_units_burned: int = 0
    cost_retry_suppressed_count: int = 0

class AttestationRequest(BaseModel):
    a8_attestation_id: str

@router.get("/state")
async def get_canary_state():
    """Get current canary state"""
    return canary_controller.get_state()

@router.post("/gates/check")
async def check_pre_canary_gates(gates: PreCanaryGatesRequest):
    """Check pre-canary gates status"""
    return canary_controller.check_pre_canary_gates(gates.model_dump())

@router.post("/step1/start")
async def start_canary_step1():
    """Start canary Step 1: A3 concurrency=1, rate_limit=5/min"""
    result = canary_controller.start_step_1()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/step2/start")
async def start_canary_step2():
    """Start canary Step 2: A3 concurrency=2-3, rate_limit=20/min, start 60-min green clock"""
    result = canary_controller.start_step_2()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/metrics")
async def submit_metrics(metrics: MetricsRequest):
    """Submit per-minute metrics from ecosystem apps"""
    cm = CanaryMetrics(
        a1_db_connected=metrics.a1_db_connected,
        a1_pool_in_use=metrics.a1_pool_in_use,
        a1_pool_idle=metrics.a1_pool_idle,
        a1_pool_total=metrics.a1_pool_total,
        a1_pool_utilization_pct=metrics.a1_pool_utilization_pct,
        a1_auth_5xx=metrics.a1_auth_5xx,
        a1_p95_ms=metrics.a1_p95_ms,
        a3_breaker_state=metrics.a3_breaker_state,
        a3_req_rate=metrics.a3_req_rate,
        a3_error_rate=metrics.a3_error_rate,
        a3_backoff_state=metrics.a3_backoff_state,
        a3_queue_depth=metrics.a3_queue_depth,
        a3_dlq_count=metrics.a3_dlq_count,
        a5_http_200_markers=metrics.a5_http_200_markers,
        a5_p95_ms=metrics.a5_p95_ms,
        a7_http_200_markers=metrics.a7_http_200_markers,
        a7_p95_ms=metrics.a7_p95_ms,
        a6_p95_ms=metrics.a6_p95_ms,
        a6_5xx_rate=metrics.a6_5xx_rate,
        a8_p95_ms=metrics.a8_p95_ms,
        a8_5xx_rate=metrics.a8_5xx_rate,
        cost_compute_units_burned=metrics.cost_compute_units_burned,
        cost_retry_suppressed_count=metrics.cost_retry_suppressed_count
    )
    return canary_controller.process_metrics(cm)

@router.post("/attestation")
async def generate_attestation(req: AttestationRequest):
    """Generate T+60 attestation for CEO review"""
    result = canary_controller.generate_attestation(req.a8_attestation_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/telemetry/status")
async def get_telemetry_status():
    """Get A8 telemetry emitter status"""
    return a8_telemetry.get_status()

@router.post("/telemetry/emit")
async def emit_telemetry_now():
    """Force immediate A8 telemetry emission"""
    metrics = a8_telemetry.collect_a2_metrics()
    success = await a8_telemetry.emit_to_a8(metrics)
    return {
        "emitted": success,
        "metrics": metrics
    }
