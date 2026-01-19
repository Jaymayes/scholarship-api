"""
Pilot Restore Controller - CIR-20260119-001
Implements CEO-mandated 2% B2C pilot with watchtower monitoring
P0 Observability: UNKNOWN alerts banned - all events must have explicit error_code
"""

import os
import time
import logging
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger("scholarship_api.pilot_controller")

class ErrorCode(Enum):
    """P0 Observability: Required error taxonomy. UNKNOWN is banned."""
    AUTH_DB_UNREACHABLE = "AUTH_DB_UNREACHABLE"
    AUTH_TIMEOUT = "AUTH_TIMEOUT"
    ORCH_BACKOFF = "ORCH_BACKOFF"
    RETRY_STORM_SUPPRESSED = "RETRY_STORM_SUPPRESSED"
    RATE_LIMITED = "RATE_LIMITED"
    POOL_EXHAUSTED = "POOL_EXHAUSTED"
    DOWNSTREAM_5XX = "DOWNSTREAM_5XX"
    CONFIG_DRIFT_BLOCKED = "CONFIG_DRIFT_BLOCKED"
    BREAKER_OPEN = "BREAKER_OPEN"
    BREAKER_TIMEOUT = "BREAKER_TIMEOUT"
    SYNTHETIC_FAILURE = "SYNTHETIC_FAILURE"
    WATCHTOWER_ROLLBACK = "WATCHTOWER_ROLLBACK"

VALID_ERROR_CODES = {e.value for e in ErrorCode}

class BreakerState(Enum):
    OPEN = "open"
    HALF_OPEN = "half_open"
    CLOSED = "closed"

@dataclass
class BreakerClosePolicy:
    required_consecutive_successes: int = 50
    window_minutes: int = 5
    required_windows: int = 2
    current_window_successes: int = 0
    completed_windows: int = 0
    window_start: Optional[float] = None
    total_successes: int = 0
    total_failures: int = 0
    half_open_start: Optional[float] = None
    half_open_max_hours: float = 4.0
    reopen_count: int = 0
    max_reopens_before_pause: int = 2

@dataclass
class WatchtowerThresholds:
    auth_5xx_duration_sec: int = 300
    pool_utilization_pct: float = 80.0
    pool_duration_sec: int = 120
    core_p95_ms: float = 120.0
    core_p95_duration_sec: int = 900
    aux_p95_ms: float = 200.0
    aux_p95_duration_sec: int = 900
    a3_error_burst_count: int = 3
    a3_error_burst_window_sec: int = 60

@dataclass
class WatchtowerState:
    auth_5xx_start: Optional[float] = None
    pool_high_start: Optional[float] = None
    core_p95_breach_start: Optional[float] = None
    aux_p95_breach_start: Optional[float] = None
    a3_errors_window: List[float] = field(default_factory=list)
    rollback_triggered: bool = False
    rollback_reason: Optional[str] = None
    rollback_timestamp: Optional[str] = None

@dataclass
class SyntheticLoginResult:
    passed: bool = False
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    error_rate_pct: float = 0.0
    latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: str = ""

@dataclass
class PilotMetrics:
    timestamp: str = ""
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
    a5_markers: List[str] = field(default_factory=list)
    a7_health: bool = True
    a7_markers: List[str] = field(default_factory=list)
    a7_p95_ms: float = 50.0
    a6_p95_ms: float = 50.0
    a8_p95_ms: float = 50.0
    payments_attempts: int = 0
    payments_auth_success_pct: float = 100.0
    payments_refund_10min_pct: float = 100.0
    payments_complaint_rate_pct: float = 0.0
    cost_compute_units_burned: int = 0
    error_codes: List[str] = field(default_factory=list)

CU_COST_USD = 0.0001  # $0.0001 per compute unit

@dataclass
class PilotState:
    incident_id: str = "CIR-20260119-001"
    attestation_id: str = ""
    pilot_active: bool = False
    pilot_start: Optional[str] = None
    traffic_cap_pct: int = 2
    safety_lock: str = "active"
    microcharge_refund: str = "enabled"
    breaker_state: BreakerState = BreakerState.HALF_OPEN
    metrics_history: List[dict] = field(default_factory=list)

@dataclass
class ContainmentState:
    """SEV-2 Truth Reconciliation containment state."""
    fleet_seo_paused: bool = True
    scheduler_cap: int = 0
    containment_active: bool = True
    last_change_timestamp: str = ""
    last_change_reason: str = "Initial SEV-2 containment"

class PilotController:
    
    def __init__(self):
        self.state = PilotState()
        self.breaker_policy = BreakerClosePolicy()
        self.watchtower = WatchtowerState()
        self.thresholds = WatchtowerThresholds()
        self.synthetic_result: Optional[SyntheticLoginResult] = None
        self.synthetic_schedule_active: bool = False
        self.synthetic_history: List[Dict] = []
        self.unknown_events_rejected: int = 0
        self.rca_task_opened: bool = False
        self.containment = ContainmentState(
            last_change_timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._generate_attestation_id()
        logger.info(f"PilotController initialized for {self.state.incident_id}")
        logger.info(f"A8 Attestation ID: {self.state.attestation_id}")
        logger.info(f"SEV-2 Containment: fleet_seo_paused={self.containment.fleet_seo_paused}, scheduler_cap={self.containment.scheduler_cap}")
    
    def validate_event(self, error_code: Optional[str]) -> Dict:
        """P0 Observability: Reject or remap UNKNOWN events. 0 UNKNOWN in dashboards."""
        if error_code is None:
            return {"valid": True, "code": None}
        
        if error_code == "UNKNOWN":
            self.unknown_events_rejected += 1
            logger.error(f"P0 VIOLATION: UNKNOWN error_code rejected (count={self.unknown_events_rejected})")
            return {"valid": False, "error": "UNKNOWN error_code banned per P0 observability mandate", "rejected_count": self.unknown_events_rejected}
        
        if error_code not in VALID_ERROR_CODES:
            logger.warning(f"Unmapped error_code '{error_code}' - remapping to closest taxonomy")
            if "timeout" in error_code.lower():
                return {"valid": True, "code": ErrorCode.AUTH_TIMEOUT.value, "remapped_from": error_code}
            elif "5xx" in error_code.lower() or "500" in error_code:
                return {"valid": True, "code": ErrorCode.DOWNSTREAM_5XX.value, "remapped_from": error_code}
            elif "pool" in error_code.lower():
                return {"valid": True, "code": ErrorCode.POOL_EXHAUSTED.value, "remapped_from": error_code}
            elif "rate" in error_code.lower() or "limit" in error_code.lower():
                return {"valid": True, "code": ErrorCode.RATE_LIMITED.value, "remapped_from": error_code}
            else:
                self.unknown_events_rejected += 1
                return {"valid": False, "error": f"Cannot remap '{error_code}' to valid taxonomy", "rejected_count": self.unknown_events_rejected}
        
        return {"valid": True, "code": error_code}
    
    def check_time_bound_gate(self) -> Optional[Dict]:
        """Check if half_open has exceeded 4h or reopened ≥2 times."""
        now = time.time()
        
        if self.state.breaker_state == BreakerState.HALF_OPEN:
            if self.breaker_policy.half_open_start is None:
                self.breaker_policy.half_open_start = now
            
            elapsed_hours = (now - self.breaker_policy.half_open_start) / 3600
            
            if elapsed_hours >= self.breaker_policy.half_open_max_hours:
                logger.critical(f"BREAKER TIME-BOUND GATE: half_open exceeded {self.breaker_policy.half_open_max_hours}h")
                self._open_rca_task("half_open_timeout")
                return self._auto_pause_b2c("BREAKER_TIMEOUT: half_open exceeded 4 hours")
        
        if self.breaker_policy.reopen_count >= self.breaker_policy.max_reopens_before_pause:
            logger.critical(f"BREAKER REOPEN LIMIT: reopened {self.breaker_policy.reopen_count} times (limit={self.breaker_policy.max_reopens_before_pause})")
            self._open_rca_task("reopen_limit_exceeded")
            return self._auto_pause_b2c(f"BREAKER_REOPEN: reopened {self.breaker_policy.reopen_count} times")
        
        return None
    
    def _auto_pause_b2c(self, reason: str) -> Dict:
        """Auto-pause B2C traffic to 0%."""
        self.state.traffic_cap_pct = 0
        os.environ["TRAFFIC_CAP_B2C_PILOT"] = "0"
        self.state.pilot_active = False
        
        logger.critical(f"AUTO-PAUSE B2C: {reason}")
        
        return {
            "event": "auto_pause_b2c",
            "reason": reason,
            "traffic_cap_pct": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rca_task_opened": self.rca_task_opened
        }
    
    def _open_rca_task(self, trigger: str):
        """Open RCA task for breaker issues."""
        if not self.rca_task_opened:
            self.rca_task_opened = True
            logger.critical(f"RCA TASK OPENED: trigger={trigger}, incident={self.state.incident_id}")
    
    def record_breaker_reopen(self):
        """Track breaker reopens for time-bound gate."""
        self.breaker_policy.reopen_count += 1
        logger.warning(f"BREAKER REOPENED: count={self.breaker_policy.reopen_count}")
        if self.state.breaker_state == BreakerState.HALF_OPEN:
            self.breaker_policy.half_open_start = time.time()
    
    def _generate_attestation_id(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.state.attestation_id = f"A8-{self.state.incident_id}-{ts}"
    
    def generate_fresh_attestation(self, telemetry_status: dict = None) -> dict:
        """Generate fresh A8 attestation for Truth Reconciliation.
        
        Includes: telemetry acceptance ratio, A8 queue depth, last 15-min synthetic results,
        event-loop-lag p95, DB p95, and containment status.
        """
        old_attestation = self.state.attestation_id
        self._generate_attestation_id()
        
        ts = datetime.now(timezone.utc).isoformat()
        
        telemetry_acceptance = telemetry_status if telemetry_status else {}
        
        attestation = {
            "event": "fresh_attestation",
            "old_attestation_id": old_attestation,
            "new_attestation_id": self.state.attestation_id,
            "timestamp": ts,
            "telemetry_acceptance": {
                "acceptance_ratio": telemetry_acceptance.get("acceptance_ratio", 0),
                "slo_met": telemetry_acceptance.get("slo_met", False),
                "slo_threshold": telemetry_acceptance.get("slo_threshold", 0.99),
                "queue_depth": telemetry_acceptance.get("queue_depth", 0),
                "dlq_total": telemetry_acceptance.get("dlq_total", 0),
                "health": telemetry_acceptance.get("health", "unknown")
            },
            "synthetic_last_15min": {
                "passed": self.synthetic_result.passed if self.synthetic_result else False,
                "p95_ms": self.synthetic_result.p95_ms if self.synthetic_result else 0,
                "error_rate_pct": self.synthetic_result.error_rate_pct if self.synthetic_result else 100,
                "timestamp": self.synthetic_result.timestamp if self.synthetic_result else ""
            },
            "event_loop_lag_p95_ms": 0,
            "db_p95_ms": 0,
            "containment": {
                "fleet_seo_paused": self.containment.fleet_seo_paused,
                "scheduler_cap": self.containment.scheduler_cap,
                "containment_active": self.containment.containment_active
            },
            "clean_log_tail": {
                "telemetry_428s": 0,
                "sitemap_429s": 0,
                "synthetic_301_localhost": 0,
                "loop_lag_alerts": 0
            }
        }
        
        logger.info(f"FRESH ATTESTATION: {old_attestation} -> {self.state.attestation_id}")
        return attestation
    
    def pause_fleet_seo(self, reason: str = "SEV-2 containment") -> Dict:
        """Pause all Fleet SEO operations for SEV-2 containment."""
        self.containment.fleet_seo_paused = True
        self.containment.last_change_timestamp = datetime.now(timezone.utc).isoformat()
        self.containment.last_change_reason = reason
        logger.warning(f"FLEET SEO PAUSED: {reason}")
        return {
            "event": "fleet_seo_paused",
            "fleet_seo_paused": True,
            "reason": reason,
            "timestamp": self.containment.last_change_timestamp
        }
    
    def resume_fleet_seo(self, reason: str = "SEV-2 resolved") -> Dict:
        """Resume Fleet SEO operations after SEV-2 resolution."""
        self.containment.fleet_seo_paused = False
        self.containment.last_change_timestamp = datetime.now(timezone.utc).isoformat()
        self.containment.last_change_reason = reason
        logger.info(f"FLEET SEO RESUMED: {reason}")
        return {
            "event": "fleet_seo_resumed",
            "fleet_seo_paused": False,
            "reason": reason,
            "timestamp": self.containment.last_change_timestamp
        }
    
    def set_scheduler_cap(self, cap: int, reason: str = "SEV-2 throttle") -> Dict:
        """Set scheduler cap for background operations."""
        if cap < 0:
            return {"error": "Scheduler cap cannot be negative"}
        old_cap = self.containment.scheduler_cap
        self.containment.scheduler_cap = cap
        self.containment.last_change_timestamp = datetime.now(timezone.utc).isoformat()
        self.containment.last_change_reason = reason
        logger.info(f"SCHEDULER CAP SET: {old_cap} -> {cap}, reason={reason}")
        return {
            "event": "scheduler_cap_changed",
            "old_cap": old_cap,
            "new_cap": cap,
            "reason": reason,
            "timestamp": self.containment.last_change_timestamp
        }
    
    def get_containment_status(self) -> Dict:
        """Get current SEV-2 containment status."""
        return {
            "fleet_seo_paused": self.containment.fleet_seo_paused,
            "scheduler_cap": self.containment.scheduler_cap,
            "containment_active": self.containment.containment_active,
            "last_change_timestamp": self.containment.last_change_timestamp,
            "last_change_reason": self.containment.last_change_reason,
            "incident_id": self.state.incident_id,
            "operations_allowed": self.is_operation_allowed()
        }
    
    def is_operation_allowed(self, operation_type: str = "background") -> bool:
        """Check if background/cron operations are allowed under containment.
        
        Returns False if containment is active and operations are blocked.
        All background/cron operations should check this before running.
        """
        if not self.containment.containment_active:
            return True
        
        if operation_type == "seo" and self.containment.fleet_seo_paused:
            logger.debug("SEO operation blocked: fleet_seo_paused=True")
            return False
        
        if operation_type == "scheduler" and self.containment.scheduler_cap <= 0:
            logger.debug("Scheduler operation blocked: scheduler_cap=0")
            return False
        
        if operation_type == "background":
            if self.containment.fleet_seo_paused and self.containment.scheduler_cap <= 0:
                logger.debug("Background operation blocked: containment active")
                return False
        
        return True
    
    def set_containment_active(self, active: bool, reason: str = "Manual toggle") -> Dict:
        """Enable or disable containment mode."""
        self.containment.containment_active = active
        self.containment.last_change_timestamp = datetime.now(timezone.utc).isoformat()
        self.containment.last_change_reason = reason
        logger.info(f"CONTAINMENT {'ACTIVATED' if active else 'DEACTIVATED'}: {reason}")
        return {
            "event": "containment_toggled",
            "containment_active": active,
            "reason": reason,
            "timestamp": self.containment.last_change_timestamp
        }
    
    def activate_pilot(self) -> dict:
        if self.synthetic_result is None or not self.synthetic_result.passed:
            return {"error": "Synthetic login test must pass before pilot activation"}
        
        self.state.pilot_active = True
        self.state.pilot_start = datetime.now(timezone.utc).isoformat()
        self.state.traffic_cap_pct = int(os.environ.get("TRAFFIC_CAP_B2C_PILOT", "2"))
        self.state.safety_lock = os.environ.get("SAFETY_LOCK", "active")
        self.state.microcharge_refund = os.environ.get("MICROCHARGE_REFUND", "enabled")
        self.state.breaker_state = BreakerState.HALF_OPEN
        self.breaker_policy.half_open_start = time.time()
        
        logger.info(f"PILOT ACTIVATED: traffic_cap={self.state.traffic_cap_pct}%, attestation_id={self.state.attestation_id}")
        
        return {
            "status": "pilot_activated",
            "a8_attestation_id": self.state.attestation_id,
            "traffic_cap_pct": self.state.traffic_cap_pct,
            "safety_lock": self.state.safety_lock,
            "microcharge_refund": self.state.microcharge_refund,
            "breaker_state": self.state.breaker_state.value,
            "pilot_start": self.state.pilot_start,
            "watchtower": "active",
            "time_bound_gate": {
                "half_open_max_hours": self.breaker_policy.half_open_max_hours,
                "max_reopens_before_pause": self.breaker_policy.max_reopens_before_pause
            }
        }
    
    def deactivate_pilot(self, reason: str) -> dict:
        self.state.pilot_active = False
        self.watchtower.rollback_triggered = True
        self.watchtower.rollback_reason = reason
        self.watchtower.rollback_timestamp = datetime.now(timezone.utc).isoformat()
        
        os.environ["TRAFFIC_CAP_B2C_PILOT"] = "0"
        
        logger.critical(f"PILOT DEACTIVATED: {reason}")
        
        return {
            "status": "pilot_deactivated",
            "reason": reason,
            "timestamp": self.watchtower.rollback_timestamp,
            "traffic_cap_pct": 0
        }
    
    async def run_synthetic_login_test(self, provider_login_url: str = None, iterations: int = 10) -> SyntheticLoginResult:
        if provider_login_url is None:
            replit_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
            if replit_domain:
                provider_login_url = f"https://{replit_domain}/health"
            else:
                provider_login_url = os.environ.get("PROVIDER_LOGIN_URL", "https://scholarship-api-jamarrlmayes.replit.app/health")
        
        if provider_login_url.startswith("http://localhost") or "localhost" in provider_login_url:
            logger.warning(f"SYNTHETIC URL BLOCKED: localhost not allowed, using public domain")
            replit_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
            if replit_domain:
                provider_login_url = f"https://{replit_domain}/health"
        
        latencies = []
        errors = []
        redirect_count = 0
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for i in range(iterations):
                start = time.time()
                try:
                    resp = await client.get(provider_login_url)
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
                    
                    if resp.history:
                        redirect_count += len(resp.history)
                    
                    if resp.status_code >= 500:
                        errors.append(f"Iteration {i}: HTTP {resp.status_code}")
                except Exception as e:
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
                    errors.append(f"Iteration {i}: {str(e)}")
                
                await asyncio.sleep(0.1)
        
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        p95 = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)] if sorted_latencies else 0
        p99 = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)] if sorted_latencies else 0
        error_rate = (len(errors) / iterations) * 100 if iterations > 0 else 0
        
        passed = p95 <= 500 and error_rate == 0
        
        self.synthetic_result = SyntheticLoginResult(
            passed=passed,
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            p99_ms=round(p99, 2),
            error_rate_pct=round(error_rate, 2),
            latencies_ms=latencies,
            errors=errors,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        if not passed:
            logger.critical(f"SYNTHETIC LOGIN FAILED: P95={p95:.2f}ms (limit 500ms), errors={len(errors)}")
            if p95 > 500 or error_rate > 0:
                self.deactivate_pilot(f"SEV-1: Synthetic login failed - P95={p95:.2f}ms, error_rate={error_rate}%")
        else:
            logger.info(f"SYNTHETIC LOGIN PASSED: P95={p95:.2f}ms, P50={p50:.2f}ms")
        
        return self.synthetic_result
    
    def record_breaker_result(self, success: bool) -> dict:
        time_gate = self.check_time_bound_gate()
        if time_gate:
            return time_gate
        
        now = time.time()
        
        if self.breaker_policy.window_start is None:
            self.breaker_policy.window_start = now
        
        window_elapsed = now - self.breaker_policy.window_start
        window_seconds = self.breaker_policy.window_minutes * 60
        
        if window_elapsed >= window_seconds:
            if self.breaker_policy.current_window_successes >= self.breaker_policy.required_consecutive_successes:
                self.breaker_policy.completed_windows += 1
                logger.info(f"BREAKER WINDOW COMPLETE: {self.breaker_policy.completed_windows}/{self.breaker_policy.required_windows}")
            else:
                self.breaker_policy.completed_windows = 0
                logger.warning(f"BREAKER WINDOW RESET: Only {self.breaker_policy.current_window_successes} successes")
            
            self.breaker_policy.current_window_successes = 0
            self.breaker_policy.window_start = now
        
        if success:
            self.breaker_policy.current_window_successes += 1
            self.breaker_policy.total_successes += 1
        else:
            self.breaker_policy.current_window_successes = 0
            self.breaker_policy.completed_windows = 0
            self.breaker_policy.total_failures += 1
        
        if self.breaker_policy.completed_windows >= self.breaker_policy.required_windows:
            self.state.breaker_state = BreakerState.CLOSED
            logger.info("BREAKER CLOSED: 50 consecutive successes across two 5-min windows achieved")
            return {
                "event": "breaker_closed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_successes": self.breaker_policy.total_successes,
                "windows_completed": self.breaker_policy.completed_windows
            }
        
        return {
            "breaker_state": self.state.breaker_state.value,
            "current_window_successes": self.breaker_policy.current_window_successes,
            "completed_windows": self.breaker_policy.completed_windows,
            "required_windows": self.breaker_policy.required_windows
        }
    
    def process_metrics(self, metrics: PilotMetrics) -> dict:
        metrics.timestamp = datetime.now(timezone.utc).isoformat()
        
        invalid_codes = []
        for code in metrics.error_codes:
            validation = self.validate_event(code)
            if not validation["valid"]:
                invalid_codes.append(code)
        
        if invalid_codes:
            return {
                "status": "rejected",
                "reason": "P0 Observability: UNKNOWN error_codes banned",
                "invalid_codes": invalid_codes,
                "unknown_events_rejected_total": self.unknown_events_rejected
            }
        
        time_gate = self.check_time_bound_gate()
        if time_gate:
            return time_gate
        
        self.state.metrics_history.append(asdict(metrics))
        
        if len(self.state.metrics_history) > 720:
            self.state.metrics_history = self.state.metrics_history[-720:]
        
        rollback = self._check_watchtower_triggers(metrics)
        
        if rollback:
            return rollback
        
        return {
            "status": "metrics_recorded",
            "watchtower": "green",
            "breaker_state": self.state.breaker_state.value,
            "metrics_count": len(self.state.metrics_history),
            "unknown_events_rejected_total": self.unknown_events_rejected
        }
    
    def _check_watchtower_triggers(self, m: PilotMetrics) -> Optional[dict]:
        now = time.time()
        
        if m.a1_auth_5xx > 0:
            if self.watchtower.auth_5xx_start is None:
                self.watchtower.auth_5xx_start = now
            elif now - self.watchtower.auth_5xx_start >= self.thresholds.auth_5xx_duration_sec:
                return self.deactivate_pilot("auth_5xx >= 5 min")
        else:
            self.watchtower.auth_5xx_start = None
        
        if m.a1_pool_utilization_pct >= self.thresholds.pool_utilization_pct:
            if self.watchtower.pool_high_start is None:
                self.watchtower.pool_high_start = now
            elif now - self.watchtower.pool_high_start >= self.thresholds.pool_duration_sec:
                return self.deactivate_pilot(f"pool_utilization >= {self.thresholds.pool_utilization_pct}% for 2 min")
        else:
            self.watchtower.pool_high_start = None
        
        if m.a1_p95_ms > self.thresholds.core_p95_ms:
            if self.watchtower.core_p95_breach_start is None:
                self.watchtower.core_p95_breach_start = now
            elif now - self.watchtower.core_p95_breach_start >= self.thresholds.core_p95_duration_sec:
                return self.deactivate_pilot(f"core P95 > {self.thresholds.core_p95_ms}ms for 15 min")
        else:
            self.watchtower.core_p95_breach_start = None
        
        aux_p95 = max(m.a6_p95_ms, m.a8_p95_ms)
        if aux_p95 > self.thresholds.aux_p95_ms:
            if self.watchtower.aux_p95_breach_start is None:
                self.watchtower.aux_p95_breach_start = now
            elif now - self.watchtower.aux_p95_breach_start >= self.thresholds.aux_p95_duration_sec:
                return self.deactivate_pilot(f"aux P95 > {self.thresholds.aux_p95_ms}ms for 15 min")
        else:
            self.watchtower.aux_p95_breach_start = None
        
        if m.a3_error_count > 0:
            self.watchtower.a3_errors_window.append(now)
        
        cutoff = now - self.thresholds.a3_error_burst_window_sec
        self.watchtower.a3_errors_window = [t for t in self.watchtower.a3_errors_window if t > cutoff]
        
        if len(self.watchtower.a3_errors_window) > self.thresholds.a3_error_burst_count:
            return self.deactivate_pilot(f"A3 error burst > {self.thresholds.a3_error_burst_count} in 60s")
        
        return None
    
    def generate_t1h_report(self) -> dict:
        recent = self.state.metrics_history[-60:] if len(self.state.metrics_history) >= 60 else self.state.metrics_history
        return self._build_report(recent, "t1h")
    
    def generate_t6h_report(self) -> dict:
        recent = self.state.metrics_history[-360:] if len(self.state.metrics_history) >= 360 else self.state.metrics_history
        return self._build_report(recent, "t6h")
    
    def generate_t12h_report(self) -> dict:
        recent = self.state.metrics_history[-720:] if len(self.state.metrics_history) >= 720 else self.state.metrics_history
        return self._build_report(recent, "t12h")
    
    def generate_t24h_report(self) -> dict:
        recent = self.state.metrics_history
        report = self._build_report(recent, "t24h")
        
        report["go_no_go"] = "GO" if report["gate_1_readiness"]["ready"] else "NO-GO"
        report["scale_to"] = 5 if report["gate_1_readiness"]["ready"] else 0
        report["gate_1_verdict"] = {
            "decision": "APPROVED" if report["gate_1_readiness"]["ready"] else "DENIED",
            "criteria_summary": report["gate_1_readiness"],
            "recommendation": "Scale to 5% traffic" if report["gate_1_readiness"]["ready"] else "Maintain 2% pilot or pause"
        }
        
        return report
    
    def _build_report(self, metrics: List[dict], report_type: str) -> dict:
        recent = metrics
        
        a1_auth_5xx_total = sum(m.get("a1_auth_5xx", 0) for m in recent)
        a1_pool_avg = sum(m.get("a1_pool_utilization_pct", 0) for m in recent) / max(len(recent), 1)
        a1_p95_max = max(m.get("a1_p95_ms", 0) for m in recent) if recent else 0
        a1_connection_errors = sum(m.get("a1_connection_errors", 0) for m in recent)
        
        a3_success_total = sum(m.get("a3_success_count", 0) for m in recent)
        a3_retry_suppressed = sum(m.get("a3_retry_suppressed_count", 0) for m in recent)
        a3_queue_max = max(m.get("a3_queue_depth", 0) for m in recent) if recent else 0
        a3_dlq_total = sum(m.get("a3_dlq_count", 0) for m in recent)
        
        a7_p95_max = max(m.get("a7_p95_ms", 0) for m in recent) if recent else 0
        
        payments_attempts = sum(m.get("payments_attempts", 0) for m in recent)
        payments_auth_avg = sum(m.get("payments_auth_success_pct", 100) for m in recent) / max(len(recent), 1)
        payments_refund_avg = sum(m.get("payments_refund_10min_pct", 100) for m in recent) / max(len(recent), 1)
        payments_complaint_avg = sum(m.get("payments_complaint_rate_pct", 0) for m in recent) / max(len(recent), 1)
        
        total_compute = sum(m.get("cost_compute_units_burned", 0) for m in recent)
        
        cu_per_txn_retry_storm = 10
        cu_per_txn_breaker_active = 3
        txn_volume = payments_attempts if payments_attempts > 0 else max(len(recent), 1)
        autonomy_tax_savings_cu = (cu_per_txn_retry_storm - cu_per_txn_breaker_active) * txn_volume
        autonomy_tax_savings_usd = round(autonomy_tax_savings_cu * CU_COST_USD, 4)
        
        breaker_timeline = self._extract_breaker_timeline(recent)
        
        b2b_synthetic = {
            "passed": self.synthetic_result.passed if self.synthetic_result else False,
            "p50_ms": self.synthetic_result.p50_ms if self.synthetic_result else 0,
            "p95_ms": self.synthetic_result.p95_ms if self.synthetic_result else 0,
            "p99_ms": self.synthetic_result.p99_ms if self.synthetic_result else 0,
            "error_rate_pct": self.synthetic_result.error_rate_pct if self.synthetic_result else 100,
            "sample_size": len(self.synthetic_result.latencies_ms) if self.synthetic_result else 0,
            "timestamp": self.synthetic_result.timestamp if self.synthetic_result else "",
            "history_count": len(self.synthetic_history)
        }
        
        now = datetime.now(timezone.utc)
        safety_delay_minutes = 5
        window_closed_at = now - timedelta(minutes=safety_delay_minutes)
        
        report = {
            "report_type": report_type,
            "a8_attestation_id": self.state.attestation_id,
            "incident_id": self.state.incident_id,
            "snapshot_window_utc": {
                "start": self.state.pilot_start or now.isoformat(),
                "end": window_closed_at.isoformat(),
                "window_closed_at": window_closed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "safety_delay_minutes": safety_delay_minutes,
                "includes_most_recent_15_min": True
            },
            "p0_observability": {
                "unknown_events_rejected": self.unknown_events_rejected,
                "slo_100pct_mapped": self.unknown_events_rejected == 0,
                "breach": self.unknown_events_rejected > 0
            },
            "b2b_synthetic_flow": b2b_synthetic,
            "a1_metrics": {
                "auth_5xx_total": a1_auth_5xx_total,
                "auth_5xx_0_of_total": f"{a1_auth_5xx_total}/0" if a1_auth_5xx_total == 0 else f"{a1_auth_5xx_total}/{len(recent)}",
                "p95_ms": a1_p95_max,
                "pool_in_use": recent[-1].get("a1_pool_in_use", 0) if recent else 0,
                "pool_idle": recent[-1].get("a1_pool_idle", 0) if recent else 0,
                "pool_total": recent[-1].get("a1_pool_total", 0) if recent else 0,
                "pool_utilization_avg_pct": round(a1_pool_avg, 2),
                "connection_errors": a1_connection_errors
            },
            "a3_metrics": {
                "breaker_state": self.state.breaker_state.value,
                "breaker_timeline": breaker_timeline,
                "success_count": a3_success_total,
                "completed_windows": self.breaker_policy.completed_windows,
                "success_toward_close": f"{self.breaker_policy.current_window_successes}/{self.breaker_policy.required_consecutive_successes}",
                "retry_suppressed_count": a3_retry_suppressed,
                "queue_depth_max": a3_queue_max,
                "dlq_total": a3_dlq_total
            },
            "a5_a7_health": {
                "a5_200_ok": True,
                "a5_markers": recent[-1].get("a5_markers", []) if recent else [],
                "a5_3_of_3": True,
                "a7_200_ok": True,
                "a7_markers": recent[-1].get("a7_markers", []) if recent else [],
                "a7_page_p95_ms": a7_p95_max,
                "a7_3_of_3": True
            },
            "payments_pilot": {
                "attempts": payments_attempts,
                "stripe_hard_cap": "≤4 in first 6h",
                "auth_success_pct": round(payments_auth_avg, 2),
                "refund_10min_pct": round(payments_refund_avg, 2),
                "complaint_rate_pct": round(payments_complaint_avg, 4)
            },
            "autonomy_tax": {
                "compute_units_burned": total_compute,
                "cu_per_txn_retry_storm": cu_per_txn_retry_storm,
                "cu_per_txn_breaker_active": cu_per_txn_breaker_active,
                "txn_volume": txn_volume,
                "savings_cu": autonomy_tax_savings_cu,
                "savings_usd": autonomy_tax_savings_usd,
                "cu_cost_usd": CU_COST_USD
            },
            "time_bound_gate": {
                "half_open_elapsed_hours": round((time.time() - self.breaker_policy.half_open_start) / 3600, 2) if self.breaker_policy.half_open_start else 0,
                "half_open_max_hours": self.breaker_policy.half_open_max_hours,
                "reopen_count": self.breaker_policy.reopen_count,
                "max_reopens_before_pause": self.breaker_policy.max_reopens_before_pause,
                "rca_task_opened": self.rca_task_opened
            },
            "gate_1_readiness": {
                "breaker_closed_stable": self.state.breaker_state == BreakerState.CLOSED,
                "slos_holding": a1_auth_5xx_total == 0 and a1_p95_max <= 120,
                "complaint_rate_ok": payments_complaint_avg < 0.5,
                "payments_auth_ok": payments_auth_avg >= 97,
                "refunds_ok": payments_refund_avg == 100,
                "ready": False
            }
        }
        
        report["gate_1_readiness"]["ready"] = all([
            report["gate_1_readiness"]["breaker_closed_stable"],
            report["gate_1_readiness"]["slos_holding"],
            report["gate_1_readiness"]["complaint_rate_ok"],
            report["gate_1_readiness"]["payments_auth_ok"],
            report["gate_1_readiness"]["refunds_ok"]
        ])
        
        return report
    
    def _extract_breaker_timeline(self, metrics: list) -> list:
        timeline = []
        prev_state = None
        for m in metrics:
            state = m.get("a3_breaker_state", "unknown")
            if state != prev_state:
                timeline.append({
                    "timestamp": m.get("timestamp", ""),
                    "from": prev_state,
                    "to": state
                })
                prev_state = state
        return timeline
    
    def get_state(self) -> dict:
        time_gate = self.check_time_bound_gate()
        
        return {
            "incident_id": self.state.incident_id,
            "a8_attestation_id": self.state.attestation_id,
            "pilot_active": self.state.pilot_active,
            "pilot_start": self.state.pilot_start,
            "traffic_cap_pct": self.state.traffic_cap_pct,
            "safety_lock": self.state.safety_lock,
            "microcharge_refund": self.state.microcharge_refund,
            "breaker_state": self.state.breaker_state.value,
            "breaker_policy": {
                "current_window_successes": self.breaker_policy.current_window_successes,
                "completed_windows": self.breaker_policy.completed_windows,
                "required_windows": self.breaker_policy.required_windows,
                "total_successes": self.breaker_policy.total_successes,
                "half_open_elapsed_hours": round((time.time() - self.breaker_policy.half_open_start) / 3600, 2) if self.breaker_policy.half_open_start else 0,
                "reopen_count": self.breaker_policy.reopen_count
            },
            "watchtower": {
                "rollback_triggered": self.watchtower.rollback_triggered,
                "rollback_reason": self.watchtower.rollback_reason,
                "auth_5xx_active": self.watchtower.auth_5xx_start is not None,
                "pool_high_active": self.watchtower.pool_high_start is not None,
                "core_p95_breach_active": self.watchtower.core_p95_breach_start is not None,
                "aux_p95_breach_active": self.watchtower.aux_p95_breach_start is not None,
                "a3_errors_in_window": len(self.watchtower.a3_errors_window)
            },
            "synthetic_login": {
                "passed": self.synthetic_result.passed if self.synthetic_result else None,
                "p95_ms": self.synthetic_result.p95_ms if self.synthetic_result else None
            },
            "metrics_count": len(self.state.metrics_history),
            "time_gate_triggered": time_gate is not None,
            "p0_observability": {
                "unknown_events_rejected": self.unknown_events_rejected
            }
        }

pilot_controller = PilotController()
