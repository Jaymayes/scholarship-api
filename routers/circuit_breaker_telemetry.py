"""
A8 Circuit Breaker Telemetry Endpoints - CEO Directive (2026-01-15)

Exposes A3→A6 circuit breaker metrics for A8 dashboards and kill/throttle rules.
Telemetry cadence: 1-minute polling recommended.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from services.a3_a6_circuit_breaker import a3_a6_breaker, should_throttle, should_kill
from utils.logger import get_logger

logger = get_logger("circuit_breaker_telemetry")
router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])


class BreakerTelemetry(BaseModel):
    breaker_state: str
    failures_last_5m: int
    open_count_1h: int
    provider_backlog_depth: int
    dlq_depth: int
    a3_call_p95_ms_to_a6: float
    a3_call_error_rate_to_a6: float
    last_updated: str
    throttle_recommended: bool
    kill_recommended: bool


class BreakerStatus(BaseModel):
    state: str
    consecutive_failures: int
    consecutive_successes: int
    backlog_depth: int
    dlq_depth: int
    open_count_1h: int
    p95_ms: float
    error_rate: float
    feature_enabled: bool
    state_uptime_seconds: float


class A8AlertPayload(BaseModel):
    alert_type: str
    severity: str
    breaker_state: str
    backlog_depth: int
    p95_ms: float
    error_rate: float
    timestamp: str
    incident_id: Optional[str] = None


@router.get("/a3-a6-breaker", response_model=BreakerTelemetry)
async def get_a3_a6_breaker_telemetry():
    """
    Get A3→A6 circuit breaker metrics for A8 dashboards.
    
    Recommended polling: 1-minute cadence for A8 dashboards.
    
    Returns:
        BreakerTelemetry with current state, failure counts, backlog depth, and recommendations.
    """
    metrics = a3_a6_breaker.get_metrics()
    
    return BreakerTelemetry(
        breaker_state=metrics.breaker_state,
        failures_last_5m=metrics.failures_last_5m,
        open_count_1h=metrics.open_count_1h,
        provider_backlog_depth=metrics.provider_backlog_depth,
        dlq_depth=metrics.dlq_depth,
        a3_call_p95_ms_to_a6=metrics.a3_call_p95_ms_to_a6,
        a3_call_error_rate_to_a6=metrics.a3_call_error_rate_to_a6,
        last_updated=metrics.last_updated,
        throttle_recommended=should_throttle(),
        kill_recommended=should_kill()
    )


@router.get("/a3-a6-breaker/status", response_model=BreakerStatus)
async def get_a3_a6_breaker_status():
    """
    Get detailed A3→A6 circuit breaker status for health checks.
    """
    status = a3_a6_breaker.get_status()
    return BreakerStatus(**status)


@router.post("/a3-a6-breaker/alert")
async def emit_a8_alert(payload: A8AlertPayload):
    """
    Emit A8 alert for circuit breaker events.
    
    Used by circuit breaker to notify A8 of state changes.
    """
    logger.warning(
        f"A8 Alert: {payload.alert_type} - severity={payload.severity}, "
        f"state={payload.breaker_state}, backlog={payload.backlog_depth}"
    )
    
    return {
        "status": "alert_received",
        "alert_type": payload.alert_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/a3-a6-breaker/guardrails")
async def get_guardrail_status():
    """
    Get current guardrail status for A8 Kill/Throttle rules.
    
    Guardrails (A8 Kill/Throttle approved):
    - THROTTLE if provider_backlog_depth 10-30 or P95 1.25-1.5s
    - KILL if >30 or P95 ≥1.5s or error ≥1.0%
    """
    metrics = a3_a6_breaker.get_metrics()
    
    throttle_reasons = []
    kill_reasons = []
    
    if 10 <= metrics.provider_backlog_depth <= 30:
        throttle_reasons.append(f"backlog_depth={metrics.provider_backlog_depth}")
    if 1250 <= metrics.a3_call_p95_ms_to_a6 < 1500:
        throttle_reasons.append(f"p95_ms={metrics.a3_call_p95_ms_to_a6}")
    
    if metrics.provider_backlog_depth > 30:
        kill_reasons.append(f"backlog_depth={metrics.provider_backlog_depth}")
    if metrics.a3_call_p95_ms_to_a6 >= 1500:
        kill_reasons.append(f"p95_ms={metrics.a3_call_p95_ms_to_a6}")
    if metrics.a3_call_error_rate_to_a6 >= 0.01:
        kill_reasons.append(f"error_rate={metrics.a3_call_error_rate_to_a6}")
    
    return {
        "throttle_active": len(throttle_reasons) > 0,
        "throttle_reasons": throttle_reasons,
        "kill_active": len(kill_reasons) > 0,
        "kill_reasons": kill_reasons,
        "current_metrics": {
            "backlog_depth": metrics.provider_backlog_depth,
            "p95_ms": metrics.a3_call_p95_ms_to_a6,
            "error_rate": metrics.a3_call_error_rate_to_a6
        },
        "timestamp": datetime.utcnow().isoformat()
    }
