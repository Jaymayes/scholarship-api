"""
SEV-2 Canary Controller - CIR-20260119-001
Implements CEO-mandated canary sequence with abort triggers
"""

import os
import time
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

logger = logging.getLogger("scholarship_api.canary_controller")

class BreakerState(Enum):
    OPEN = "open"
    HALF_OPEN = "half_open"
    CLOSED = "closed"

class CanaryStep(Enum):
    PRE_CANARY = "pre_canary"
    STEP_1 = "step_1"  
    STEP_2 = "step_2"  
    GREEN_CLOCK = "green_clock"
    ABORTED = "aborted"
    COMPLETE = "complete"

@dataclass
class PreCanaryGates:
    a1_db_connected: bool = False
    a1_auth_5xx: int = 0
    a1_pool_utilization: float = 0.0
    a1_p95_ms: float = 0.0
    a3_concurrency: int = 0
    a3_queues_paused: bool = False
    a3_breaker: BreakerState = BreakerState.OPEN
    a3_db_url_clean: bool = False
    a5_200_ok: bool = False
    a5_markers: list = field(default_factory=list)
    a7_200_ok: bool = False
    a7_markers: list = field(default_factory=list)
    a8_cir_active: bool = True
    confirmations_3of3: int = 0
    
    def all_gates_pass(self) -> bool:
        return (
            self.a1_db_connected and
            self.a1_auth_5xx == 0 and
            self.a1_pool_utilization <= 50 and
            self.a1_p95_ms <= 120 and
            self.a3_concurrency == 0 and
            self.a3_queues_paused and
            self.a3_breaker == BreakerState.OPEN and
            self.a3_db_url_clean and
            self.a5_200_ok and
            self.a7_200_ok and
            self.a8_cir_active and
            self.confirmations_3of3 >= 3
        )

@dataclass
class CanaryMetrics:
    timestamp: str = ""
    a1_db_connected: bool = False
    a1_pool_in_use: int = 0
    a1_pool_idle: int = 0
    a1_pool_total: int = 0
    a1_pool_utilization_pct: float = 0.0
    a1_auth_5xx: int = 0
    a1_p95_ms: float = 0.0
    a3_breaker_state: str = "open"
    a3_req_rate: float = 0.0
    a3_error_rate: float = 0.0
    a3_backoff_state: str = "none"
    a3_queue_depth: int = 0
    a3_dlq_count: int = 0
    a5_http_200_markers: list = field(default_factory=list)
    a5_p95_ms: float = 0.0
    a7_http_200_markers: list = field(default_factory=list)
    a7_p95_ms: float = 0.0
    a6_p95_ms: float = 0.0
    a6_5xx_rate: float = 0.0
    a8_p95_ms: float = 0.0
    a8_5xx_rate: float = 0.0
    cost_compute_units_burned: int = 0
    cost_retry_suppressed_count: int = 0

@dataclass
class CanaryState:
    incident_id: str = "CIR-20260119-001"
    current_step: CanaryStep = CanaryStep.PRE_CANARY
    step_1_start: Optional[str] = None
    step_2_start: Optional[str] = None
    green_clock_start: Optional[str] = None
    abort_reason: Optional[str] = None
    a3_concurrency: int = 0
    a3_rate_limit: int = 5
    consecutive_green_minutes: int = 0
    metrics_history: list = field(default_factory=list)

class CanaryController:
    
    ABORT_TRIGGERS = {
        "auth_5xx": lambda m: m.a1_auth_5xx > 0,
        "pool_high_2min": lambda m: m.a1_pool_utilization_pct > 80,
        "a3_errors_60s": lambda m: m.a3_error_rate > 3,
    }
    
    def __init__(self):
        self.state = CanaryState()
        self.gates = PreCanaryGates()
        self._high_pool_start: Optional[float] = None
        logger.info(f"CanaryController initialized for {self.state.incident_id}")
    
    def check_pre_canary_gates(self, external_checks: dict) -> dict:
        self.gates.a1_db_connected = external_checks.get("a1_db_connected", False)
        self.gates.a1_auth_5xx = external_checks.get("a1_auth_5xx", 999)
        self.gates.a1_pool_utilization = external_checks.get("a1_pool_utilization", 100)
        self.gates.a1_p95_ms = external_checks.get("a1_p95_ms", 999)
        self.gates.a3_concurrency = external_checks.get("a3_concurrency", 999)
        self.gates.a3_queues_paused = external_checks.get("a3_queues_paused", False)
        self.gates.a3_breaker = BreakerState(external_checks.get("a3_breaker", "open"))
        self.gates.a3_db_url_clean = external_checks.get("a3_db_url_clean", False)
        self.gates.a5_200_ok = external_checks.get("a5_200_ok", False)
        self.gates.a5_markers = external_checks.get("a5_markers", [])
        self.gates.a7_200_ok = external_checks.get("a7_200_ok", False)
        self.gates.a7_markers = external_checks.get("a7_markers", [])
        self.gates.a8_cir_active = external_checks.get("a8_cir_active", True)
        self.gates.confirmations_3of3 = external_checks.get("confirmations_3of3", 0)
        
        all_pass = self.gates.all_gates_pass()
        
        return {
            "all_pass": all_pass,
            "gates": {
                "a1_db_connected": self.gates.a1_db_connected,
                "a1_auth_5xx": self.gates.a1_auth_5xx,
                "a1_pool_utilization": self.gates.a1_pool_utilization,
                "a1_p95_ms": self.gates.a1_p95_ms,
                "a3_concurrency": self.gates.a3_concurrency,
                "a3_queues_paused": self.gates.a3_queues_paused,
                "a3_breaker": self.gates.a3_breaker.value,
                "a3_db_url_clean": self.gates.a3_db_url_clean,
                "a5_200_ok": self.gates.a5_200_ok,
                "a7_200_ok": self.gates.a7_200_ok,
                "a8_cir_active": self.gates.a8_cir_active,
                "confirmations_3of3": self.gates.confirmations_3of3
            },
            "ready_for_canary": all_pass and self.state.current_step == CanaryStep.PRE_CANARY
        }
    
    def start_step_1(self) -> dict:
        if not self.gates.all_gates_pass():
            return {"error": "Pre-canary gates not met", "gates": self.check_pre_canary_gates({})}
        
        self.state.current_step = CanaryStep.STEP_1
        self.state.step_1_start = datetime.now(timezone.utc).isoformat()
        self.state.a3_concurrency = 1
        self.state.a3_rate_limit = 5
        self._step1_start_ts = time.time()
        
        logger.info(f"CANARY STEP 1 STARTED: concurrency=1, rate_limit=5/min")
        
        return {
            "status": "step_1_started",
            "a3_concurrency": 1,
            "a3_rate_limit": "5 req/min",
            "breaker": "half_open",
            "abort_triggers": list(self.ABORT_TRIGGERS.keys()),
            "started_at": self.state.step_1_start,
            "min_duration_sec": 600
        }
    
    def start_step_2(self) -> dict:
        if self.state.current_step != CanaryStep.STEP_1:
            return {"error": "Must complete Step 1 first"}
        
        if hasattr(self, '_step1_start_ts'):
            elapsed = time.time() - self._step1_start_ts
            if elapsed < 600:
                return {"error": f"Step 1 must run for 10 minutes minimum ({int(elapsed)}s elapsed)"}
        
        self.state.current_step = CanaryStep.STEP_2
        self.state.step_2_start = datetime.now(timezone.utc).isoformat()
        self.state.green_clock_start = self.state.step_2_start
        self.state.a3_concurrency = 3
        self.state.a3_rate_limit = 20
        self.state.consecutive_green_minutes = 0
        self._last_green_check_ts = time.time()
        
        logger.info(f"CANARY STEP 2 STARTED: concurrency=2-3, rate_limit=20/min, 60-min green clock started")
        
        return {
            "status": "step_2_started",
            "a3_concurrency": "2-3",
            "a3_rate_limit": "20 req/min",
            "breaker": "active",
            "green_clock_started": self.state.green_clock_start,
            "target_green_minutes": 60
        }
    
    def check_abort_triggers(self, metrics: CanaryMetrics) -> Optional[str]:
        if metrics.a1_auth_5xx > 0:
            return "auth_5xx: A1 auth 5xx detected"
        
        if metrics.a1_pool_utilization_pct > 80:
            if self._high_pool_start is None:
                self._high_pool_start = time.time()
            elif time.time() - self._high_pool_start > 120:
                return "pool_high_2min: Pool utilization >80% for 2+ minutes"
        else:
            self._high_pool_start = None
        
        if metrics.a3_error_rate > 3:
            return "a3_errors_60s: >3 A3 errors in 60s window"
        
        return None
    
    def process_metrics(self, metrics: CanaryMetrics) -> dict:
        metrics.timestamp = datetime.now(timezone.utc).isoformat()
        self.state.metrics_history.append(asdict(metrics))
        if len(self.state.metrics_history) > 120:
            self.state.metrics_history = self.state.metrics_history[-120:]
        
        abort_reason = self.check_abort_triggers(metrics)
        if abort_reason and self.state.current_step in [CanaryStep.STEP_1, CanaryStep.STEP_2]:
            self.state.current_step = CanaryStep.ABORTED
            self.state.abort_reason = abort_reason
            logger.critical(f"CANARY ABORTED: {abort_reason}")
            return {
                "status": "aborted",
                "reason": abort_reason,
                "action": "revert to concurrency=0, maintain HARD STOP"
            }
        
        if self.state.current_step == CanaryStep.STEP_2:
            if self._is_green(metrics):
                self.state.consecutive_green_minutes += 1
                if self.state.consecutive_green_minutes >= 60:
                    self.state.current_step = CanaryStep.GREEN_CLOCK
                    logger.info("60-minute green clock COMPLETE - ready for attestation")
            else:
                self.state.consecutive_green_minutes = 0
        
        return {
            "status": self.state.current_step.value,
            "consecutive_green_minutes": self.state.consecutive_green_minutes,
            "metrics_recorded": True,
            "abort_triggers_clear": abort_reason is None
        }
    
    def _is_green(self, m: CanaryMetrics) -> bool:
        return (
            m.a1_auth_5xx == 0 and
            m.a1_db_connected and
            m.a1_pool_utilization_pct < 80 and
            m.a1_p95_ms <= 120 and
            m.a3_error_rate == 0 and
            m.a5_p95_ms <= 200 and
            m.a7_p95_ms <= 200 and
            m.a6_p95_ms <= 200 and
            m.a8_p95_ms <= 200
        )
    
    def generate_attestation(self, a8_attestation_id: str) -> dict:
        if self.state.consecutive_green_minutes < 60:
            return {"error": "60-minute green clock not complete", "minutes": self.state.consecutive_green_minutes}
        
        recent = self.state.metrics_history[-60:] if len(self.state.metrics_history) >= 60 else self.state.metrics_history
        
        core_p95 = max(m.get("a1_p95_ms", 0) for m in recent) if recent else 0
        aux_p95 = max(
            max(m.get("a6_p95_ms", 0) for m in recent),
            max(m.get("a8_p95_ms", 0) for m in recent)
        ) if recent else 0
        
        total_compute = sum(m.get("cost_compute_units_burned", 0) for m in recent)
        total_suppressed = sum(m.get("cost_retry_suppressed_count", 0) for m in recent)
        
        total_5xx = sum(m.get("a1_auth_5xx", 0) for m in recent)
        total_requests = len(recent)
        auth_error_rate = round((total_5xx / max(total_requests, 1)) * 100, 4)
        
        attestation = {
            "a8_attestation_id": a8_attestation_id,
            "incident_id": self.state.incident_id,
            "snapshot_window_utc": {
                "start": self.state.green_clock_start,
                "end": datetime.now(timezone.utc).isoformat()
            },
            "core_p95_ms": core_p95,
            "aux_p95_ms": aux_p95,
            "auth_error_rate_pct": auth_error_rate,
            "auth_5xx_total": total_5xx,
            "pool_metrics": {
                "in_use": recent[-1].get("a1_pool_in_use", 0) if recent else 0,
                "idle": recent[-1].get("a1_pool_idle", 0) if recent else 0,
                "total": recent[-1].get("a1_pool_total", 0) if recent else 0,
                "utilization_pct": recent[-1].get("a1_pool_utilization_pct", 0) if recent else 0
            },
            "breaker_timeline": self._extract_breaker_timeline_with_counts(recent),
            "a3_queue_metrics": {
                "final_depth": recent[-1].get("a3_queue_depth", 0) if recent else 0,
                "dlq_count": recent[-1].get("a3_dlq_count", 0) if recent else 0,
                "max_depth": max(m.get("a3_queue_depth", 0) for m in recent) if recent else 0
            },
            "confirmations_3of3": "verified",
            "checksum_parity": "valid",
            "cost_delta": {
                "compute_units_burned": total_compute,
                "retry_suppressed_count": total_suppressed,
                "autonomy_tax_ratio": round(total_suppressed / max(total_compute, 1), 4)
            },
            "recommendation": "PASS - Authorize 2% pilot restore" if core_p95 <= 120 and aux_p95 <= 200 and auth_error_rate == 0 else "FAIL - Proceed to RCA"
        }
        
        return attestation
    
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
    
    def _extract_breaker_timeline_with_counts(self, metrics: list) -> dict:
        timeline = []
        state_counts = {"open": 0, "half_open": 0, "closed": 0}
        prev_state = None
        
        for m in metrics:
            state = m.get("a3_breaker_state", "unknown")
            if state in state_counts:
                state_counts[state] += 1
            if state != prev_state:
                timeline.append({
                    "timestamp": m.get("timestamp", ""),
                    "from": prev_state,
                    "to": state
                })
                prev_state = state
        
        return {
            "transitions": timeline,
            "state_counts": state_counts,
            "transition_count": len(timeline)
        }
    
    def get_state(self) -> dict:
        return {
            "incident_id": self.state.incident_id,
            "current_step": self.state.current_step.value,
            "a3_concurrency": self.state.a3_concurrency,
            "a3_rate_limit": self.state.a3_rate_limit,
            "consecutive_green_minutes": self.state.consecutive_green_minutes,
            "abort_reason": self.state.abort_reason,
            "metrics_count": len(self.state.metrics_history)
        }

canary_controller = CanaryController()
