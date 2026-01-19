"""
Pilot Restore Controller - CIR-20260119-001
Implements CEO-mandated 2% B2C pilot with watchtower monitoring
"""

import os
import time
import logging
import asyncio
import httpx
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum

logger = logging.getLogger("scholarship_api.pilot_controller")

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
    a6_p95_ms: float = 50.0
    a8_p95_ms: float = 50.0
    payments_attempts: int = 0
    payments_auth_success_pct: float = 100.0
    payments_refund_10min_pct: float = 100.0
    payments_complaint_rate_pct: float = 0.0
    cost_compute_units_burned: int = 0

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

class PilotController:
    
    def __init__(self):
        self.state = PilotState()
        self.breaker_policy = BreakerClosePolicy()
        self.watchtower = WatchtowerState()
        self.thresholds = WatchtowerThresholds()
        self.synthetic_result: Optional[SyntheticLoginResult] = None
        self._generate_attestation_id()
        logger.info(f"PilotController initialized for {self.state.incident_id}")
        logger.info(f"A8 Attestation ID: {self.state.attestation_id}")
    
    def _generate_attestation_id(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.state.attestation_id = f"A8-{self.state.incident_id}-{ts}"
    
    def activate_pilot(self) -> dict:
        if self.synthetic_result is None or not self.synthetic_result.passed:
            return {"error": "Synthetic login test must pass before pilot activation"}
        
        self.state.pilot_active = True
        self.state.pilot_start = datetime.now(timezone.utc).isoformat()
        self.state.traffic_cap_pct = int(os.environ.get("TRAFFIC_CAP_B2C_PILOT", "2"))
        self.state.safety_lock = os.environ.get("SAFETY_LOCK", "active")
        self.state.microcharge_refund = os.environ.get("MICROCHARGE_REFUND", "enabled")
        self.state.breaker_state = BreakerState.HALF_OPEN
        
        logger.info(f"PILOT ACTIVATED: traffic_cap={self.state.traffic_cap_pct}%, attestation_id={self.state.attestation_id}")
        
        return {
            "status": "pilot_activated",
            "a8_attestation_id": self.state.attestation_id,
            "traffic_cap_pct": self.state.traffic_cap_pct,
            "safety_lock": self.state.safety_lock,
            "microcharge_refund": self.state.microcharge_refund,
            "breaker_state": self.state.breaker_state.value,
            "pilot_start": self.state.pilot_start,
            "watchtower": "active"
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
            provider_login_url = os.environ.get("PROVIDER_LOGIN_URL", "https://scholarship-api-jamarrlmayes.replit.app/health")
        
        latencies = []
        errors = []
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(iterations):
                start = time.time()
                try:
                    resp = await client.get(provider_login_url)
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
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
        self.state.metrics_history.append(asdict(metrics))
        
        if len(self.state.metrics_history) > 120:
            self.state.metrics_history = self.state.metrics_history[-120:]
        
        rollback = self._check_watchtower_triggers(metrics)
        
        if rollback:
            return rollback
        
        return {
            "status": "metrics_recorded",
            "watchtower": "green",
            "breaker_state": self.state.breaker_state.value,
            "metrics_count": len(self.state.metrics_history)
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
        
        a1_auth_5xx_total = sum(m.get("a1_auth_5xx", 0) for m in recent)
        a1_pool_avg = sum(m.get("a1_pool_utilization_pct", 0) for m in recent) / max(len(recent), 1)
        a1_p95_max = max(m.get("a1_p95_ms", 0) for m in recent) if recent else 0
        
        a3_success_total = sum(m.get("a3_success_count", 0) for m in recent)
        a3_retry_suppressed = sum(m.get("a3_retry_suppressed_count", 0) for m in recent)
        a3_queue_max = max(m.get("a3_queue_depth", 0) for m in recent) if recent else 0
        a3_dlq_total = sum(m.get("a3_dlq_count", 0) for m in recent)
        
        payments_attempts = sum(m.get("payments_attempts", 0) for m in recent)
        payments_auth_avg = sum(m.get("payments_auth_success_pct", 100) for m in recent) / max(len(recent), 1)
        payments_refund_avg = sum(m.get("payments_refund_10min_pct", 100) for m in recent) / max(len(recent), 1)
        payments_complaint_avg = sum(m.get("payments_complaint_rate_pct", 0) for m in recent) / max(len(recent), 1)
        
        total_compute = sum(m.get("cost_compute_units_burned", 0) for m in recent)
        
        cu_per_txn_retry_storm = 10
        cu_per_txn_breaker_active = 3
        txn_volume = payments_attempts if payments_attempts > 0 else len(recent)
        autonomy_tax_savings = (cu_per_txn_retry_storm - cu_per_txn_breaker_active) * txn_volume
        
        breaker_timeline = self._extract_breaker_timeline(recent)
        
        report = {
            "a8_attestation_id": self.state.attestation_id,
            "incident_id": self.state.incident_id,
            "snapshot_window_utc": {
                "start": self.state.pilot_start or datetime.now(timezone.utc).isoformat(),
                "end": datetime.now(timezone.utc).isoformat()
            },
            "synthetic_login_test": {
                "passed": self.synthetic_result.passed if self.synthetic_result else False,
                "p50_ms": self.synthetic_result.p50_ms if self.synthetic_result else 0,
                "p95_ms": self.synthetic_result.p95_ms if self.synthetic_result else 0,
                "p99_ms": self.synthetic_result.p99_ms if self.synthetic_result else 0,
                "error_rate_pct": self.synthetic_result.error_rate_pct if self.synthetic_result else 100,
                "timestamp": self.synthetic_result.timestamp if self.synthetic_result else ""
            },
            "a1_metrics": {
                "auth_5xx_total": a1_auth_5xx_total,
                "pool_in_use": recent[-1].get("a1_pool_in_use", 0) if recent else 0,
                "pool_idle": recent[-1].get("a1_pool_idle", 0) if recent else 0,
                "pool_total": recent[-1].get("a1_pool_total", 0) if recent else 0,
                "pool_utilization_avg_pct": round(a1_pool_avg, 2),
                "p95_max_ms": a1_p95_max
            },
            "a3_metrics": {
                "breaker_state": self.state.breaker_state.value,
                "breaker_timeline": breaker_timeline,
                "success_count": a3_success_total,
                "completed_windows": self.breaker_policy.completed_windows,
                "retry_suppressed_count": a3_retry_suppressed,
                "queue_depth_max": a3_queue_max,
                "dlq_total": a3_dlq_total
            },
            "a5_a7_health": {
                "a5_health": recent[-1].get("a5_health", True) if recent else True,
                "a5_markers": recent[-1].get("a5_markers", []) if recent else [],
                "a7_health": recent[-1].get("a7_health", True) if recent else True,
                "a7_markers": recent[-1].get("a7_markers", []) if recent else []
            },
            "payments_pilot": {
                "attempts": payments_attempts,
                "auth_success_pct": round(payments_auth_avg, 2),
                "refund_10min_pct": round(payments_refund_avg, 2),
                "complaint_rate_pct": round(payments_complaint_avg, 4)
            },
            "cost_analysis": {
                "compute_units_burned": total_compute,
                "cu_per_txn_retry_storm": cu_per_txn_retry_storm,
                "cu_per_txn_breaker_active": cu_per_txn_breaker_active,
                "txn_volume": txn_volume,
                "autonomy_tax_savings": autonomy_tax_savings
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
                "total_successes": self.breaker_policy.total_successes
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
            "metrics_count": len(self.state.metrics_history)
        }

pilot_controller = PilotController()
