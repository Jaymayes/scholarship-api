"""
Pilot Restore Endpoints - CIR-20260119-001
2% B2C pilot with watchtower monitoring and auto-rollback
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from services.pilot_controller import pilot_controller, PilotMetrics, VALID_ERROR_CODES

router = APIRouter(prefix="/api/internal/pilot", tags=["pilot-sev2"])

class SyntheticLoginRequest(BaseModel):
    provider_login_url: Optional[str] = None
    iterations: int = 10

class EventValidationRequest(BaseModel):
    error_code: str

class PilotMetricsRequest(BaseModel):
    a1_auth_5xx: int = 0
    a1_pool_in_use: int = 0
    a1_pool_idle: int = 10
    a1_pool_total: int = 10
    a1_pool_utilization_pct: float = 0.0
    a1_p95_ms: float = 50.0
    a1_connection_errors: int = 0
    a3_breaker_state: str = "half_open"
    a3_success_count: int = 0
    a3_error_count: int = 0
    a3_retry_suppressed_count: int = 0
    a3_queue_depth: int = 0
    a3_dlq_count: int = 0
    a5_health: bool = True
    a5_markers: List[str] = []
    a7_health: bool = True
    a7_markers: List[str] = []
    a7_p95_ms: float = 50.0
    a6_p95_ms: float = 50.0
    a8_p95_ms: float = 50.0
    payments_attempts: int = 0
    payments_auth_success_pct: float = 100.0
    payments_refund_10min_pct: float = 100.0
    payments_complaint_rate_pct: float = 0.0
    cost_compute_units_burned: int = 0
    error_codes: List[str] = []

class BreakerResultRequest(BaseModel):
    success: bool

@router.get("/state")
async def get_pilot_state():
    return pilot_controller.get_state()

@router.post("/synthetic-login")
async def run_synthetic_login(req: SyntheticLoginRequest):
    result = await pilot_controller.run_synthetic_login_test(
        provider_login_url=req.provider_login_url,
        iterations=req.iterations
    )
    
    if not result.passed:
        return {
            "status": "FAILED",
            "sev1_declared": True,
            "result": {
                "passed": result.passed,
                "p50_ms": result.p50_ms,
                "p95_ms": result.p95_ms,
                "p99_ms": result.p99_ms,
                "error_rate_pct": result.error_rate_pct,
                "errors": result.errors,
                "timestamp": result.timestamp
            },
            "action": "TRAFFIC_CAP_B2C_PILOT set to 0"
        }
    
    return {
        "status": "PASSED",
        "result": {
            "passed": result.passed,
            "p50_ms": result.p50_ms,
            "p95_ms": result.p95_ms,
            "p99_ms": result.p99_ms,
            "error_rate_pct": result.error_rate_pct,
            "timestamp": result.timestamp
        },
        "ready_for_activation": True
    }

@router.post("/activate")
async def activate_pilot():
    result = pilot_controller.activate_pilot()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/deactivate")
async def deactivate_pilot(reason: str = "Manual deactivation"):
    return pilot_controller.deactivate_pilot(reason)

@router.post("/metrics")
async def submit_pilot_metrics(metrics: PilotMetricsRequest):
    pm = PilotMetrics(
        a1_auth_5xx=metrics.a1_auth_5xx,
        a1_pool_in_use=metrics.a1_pool_in_use,
        a1_pool_idle=metrics.a1_pool_idle,
        a1_pool_total=metrics.a1_pool_total,
        a1_pool_utilization_pct=metrics.a1_pool_utilization_pct,
        a1_p95_ms=metrics.a1_p95_ms,
        a1_connection_errors=metrics.a1_connection_errors,
        a3_breaker_state=metrics.a3_breaker_state,
        a3_success_count=metrics.a3_success_count,
        a3_error_count=metrics.a3_error_count,
        a3_retry_suppressed_count=metrics.a3_retry_suppressed_count,
        a3_queue_depth=metrics.a3_queue_depth,
        a3_dlq_count=metrics.a3_dlq_count,
        a5_health=metrics.a5_health,
        a5_markers=metrics.a5_markers,
        a7_health=metrics.a7_health,
        a7_markers=metrics.a7_markers,
        a7_p95_ms=metrics.a7_p95_ms,
        a6_p95_ms=metrics.a6_p95_ms,
        a8_p95_ms=metrics.a8_p95_ms,
        payments_attempts=metrics.payments_attempts,
        payments_auth_success_pct=metrics.payments_auth_success_pct,
        payments_refund_10min_pct=metrics.payments_refund_10min_pct,
        payments_complaint_rate_pct=metrics.payments_complaint_rate_pct,
        cost_compute_units_burned=metrics.cost_compute_units_burned,
        error_codes=metrics.error_codes
    )
    
    result = pilot_controller.process_metrics(pm)
    
    if result.get("status") == "rejected":
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "P0 Observability Violation",
                "reason": result.get("reason"),
                "invalid_codes": result.get("invalid_codes"),
                "unknown_events_rejected_total": result.get("unknown_events_rejected_total")
            }
        )
    
    if result.get("event") == "auto_pause_b2c":
        return {
            "watchtower": "AUTO_PAUSE_B2C",
            "reason": result.get("reason"),
            "timestamp": result.get("timestamp"),
            "traffic_cap_pct": 0,
            "rca_task_opened": result.get("rca_task_opened")
        }
    
    if result.get("status") == "pilot_deactivated":
        return {
            "watchtower": "ROLLBACK_TRIGGERED",
            "reason": result.get("reason"),
            "timestamp": result.get("timestamp"),
            "action": "B2C capture paused, refunds enabled"
        }
    
    return result

@router.post("/breaker/result")
async def record_breaker_result(req: BreakerResultRequest):
    result = pilot_controller.record_breaker_result(req.success)
    
    if result.get("event") == "breaker_closed":
        return {
            "event": "breaker_closed",
            "message": "Breaker closed: 50 consecutive successes across two 5-min windows",
            "timestamp": result.get("timestamp"),
            "total_successes": result.get("total_successes")
        }
    
    return result

@router.get("/report/t1h")
async def get_t1h_report():
    return pilot_controller.generate_t1h_report()

@router.get("/report/t6h")
async def get_t6h_report():
    return pilot_controller.generate_t6h_report()

@router.get("/report/t12h")
async def get_t12h_report():
    return pilot_controller.generate_t12h_report()

@router.get("/report/t24h")
async def get_t24h_report():
    """T+24h Watchtower report with GO/NO-GO for Gate-1 (5%)."""
    return pilot_controller.generate_t24h_report()

@router.get("/observability/taxonomy")
async def get_error_taxonomy():
    """P0 Observability: Return valid error_code taxonomy. UNKNOWN is banned."""
    return {
        "valid_error_codes": list(VALID_ERROR_CODES),
        "unknown_banned": True,
        "slo": "100% events mapped; 0 UNKNOWN in dashboards",
        "unknown_events_rejected": pilot_controller.unknown_events_rejected
    }

@router.post("/observability/validate")
async def validate_error_code(req: EventValidationRequest):
    """P0 Observability: Validate an error_code before submission."""
    result = pilot_controller.validate_event(req.error_code)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result)
    return result

@router.post("/breaker/reopen")
async def record_breaker_reopen():
    """Track breaker reopen for time-bound gate."""
    pilot_controller.record_breaker_reopen()
    return {
        "reopen_count": pilot_controller.breaker_policy.reopen_count,
        "max_reopens_before_pause": pilot_controller.breaker_policy.max_reopens_before_pause,
        "will_auto_pause": pilot_controller.breaker_policy.reopen_count >= pilot_controller.breaker_policy.max_reopens_before_pause
    }

@router.get("/time-gate/status")
async def get_time_gate_status():
    """Check breaker time-bound gate status."""
    import time
    half_open_start = pilot_controller.breaker_policy.half_open_start
    return {
        "half_open_elapsed_hours": round((time.time() - half_open_start) / 3600, 2) if half_open_start else 0,
        "half_open_max_hours": pilot_controller.breaker_policy.half_open_max_hours,
        "reopen_count": pilot_controller.breaker_policy.reopen_count,
        "max_reopens_before_pause": pilot_controller.breaker_policy.max_reopens_before_pause,
        "rca_task_opened": pilot_controller.rca_task_opened,
        "will_auto_pause_on_timeout": half_open_start is not None and (time.time() - half_open_start) / 3600 >= pilot_controller.breaker_policy.half_open_max_hours
    }

@router.get("/watchtower/status")
async def get_watchtower_status():
    state = pilot_controller.get_state()
    return {
        "watchtower_active": state["pilot_active"],
        "thresholds": {
            "auth_5xx_duration_sec": 300,
            "pool_utilization_pct": 80.0,
            "pool_duration_sec": 120,
            "core_p95_ms": 120.0,
            "core_p95_duration_sec": 900,
            "aux_p95_ms": 200.0,
            "aux_p95_duration_sec": 900,
            "a3_error_burst_count": 3,
            "a3_error_burst_window_sec": 60
        },
        "current_state": state["watchtower"],
        "breaker_policy": state["breaker_policy"],
        "time_bound_gate": {
            "half_open_max_hours": pilot_controller.breaker_policy.half_open_max_hours,
            "max_reopens_before_pause": pilot_controller.breaker_policy.max_reopens_before_pause,
            "reopen_count": pilot_controller.breaker_policy.reopen_count,
            "rca_task_opened": pilot_controller.rca_task_opened
        },
        "p0_observability": {
            "unknown_events_rejected": pilot_controller.unknown_events_rejected
        }
    }
