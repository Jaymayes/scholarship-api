"""
A3→A6 Circuit Breaker - CEO Directive (2026-01-15)

Protects A3 (Auto Page Maker + scholarship flows) from A6 provider failures.
Student flows NEVER blocked; provider payloads queued for retry.

States:
- CLOSED: Normal calls to A6
- OPEN: 3 consecutive failures in 60s → block for 5 minutes, queue payloads
- HALF_OPEN: 1 probe per 30s; 2 consecutive successes → close; failure → open
"""

import asyncio
import time
import json
import random
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import os

logger = logging.getLogger(__name__)

FEATURE_FLAG_ENABLED = os.environ.get("A3_A6_CIRCUIT_BREAKER_ENABLED", "false").lower() == "true"


class BreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class BacklogEntry:
    id: str
    idempotency_key: str
    payload_json: str
    first_seen_at: datetime
    next_retry_at: datetime
    attempts: int = 0
    status: str = "pending"


@dataclass
class BreakerMetrics:
    breaker_state: str = "CLOSED"
    failures_last_5m: int = 0
    open_count_1h: int = 0
    provider_backlog_depth: int = 0
    dlq_depth: int = 0
    a3_call_p95_ms_to_a6: float = 0.0
    a3_call_error_rate_to_a6: float = 0.0
    last_updated: str = ""


class A3A6CircuitBreaker:
    """
    Circuit breaker for A3→A6 calls with backlog queue.
    
    Spec:
    - 3 consecutive failures within 60s → OPEN for 5 minutes
    - HALF_OPEN: 1 probe per 30s; 2 consecutive successes → CLOSED
    - Backlog: exponential backoff with full jitter, base 30s, cap 15m, max 10 attempts
    """
    
    FAILURE_THRESHOLD = 3
    FAILURE_WINDOW_SECONDS = 60
    OPEN_DURATION_SECONDS = 300
    HALF_OPEN_PROBE_INTERVAL = 30
    RECOVERY_THRESHOLD = 2
    
    BACKLOG_BASE_DELAY = 30
    BACKLOG_MAX_DELAY = 900
    BACKLOG_MAX_ATTEMPTS = 10
    
    def __init__(self):
        self.state = BreakerState.CLOSED
        self.failure_times: list[float] = []
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_state_change = time.time()
        self.last_probe_time: Optional[float] = None
        self.open_count_1h = 0
        self.last_open_count_reset = time.time()
        
        self.backlog: list[BacklogEntry] = []
        self.dlq: list[BacklogEntry] = []
        
        self.call_latencies: list[float] = []
        self.call_results: list[bool] = []
        
        self._lock = asyncio.Lock()
        self._backlog_processor_running = False
    
    def _cleanup_old_failures(self):
        """Remove failures older than the window and reset consecutive count if needed."""
        cutoff = time.time() - self.FAILURE_WINDOW_SECONDS
        old_count = len(self.failure_times)
        self.failure_times = [t for t in self.failure_times if t > cutoff]
        
        if len(self.failure_times) == 0 and old_count > 0:
            self.consecutive_failures = 0
    
    def _reset_open_count_if_needed(self):
        """Reset hourly open count."""
        if time.time() - self.last_open_count_reset > 3600:
            self.open_count_1h = 0
            self.last_open_count_reset = time.time()
    
    def _calculate_backoff(self, attempts: int) -> float:
        """Exponential backoff with full jitter."""
        delay = min(
            self.BACKLOG_BASE_DELAY * (2 ** attempts),
            self.BACKLOG_MAX_DELAY
        )
        return random.uniform(0, delay)
    
    async def _should_allow_probe(self) -> bool:
        """Check if we can attempt a probe in HALF_OPEN state."""
        if self.last_probe_time is None:
            return True
        return time.time() - self.last_probe_time >= self.HALF_OPEN_PROBE_INTERVAL
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        logger.warning("A3→A6 Circuit Breaker: CLOSED → OPEN (3 consecutive failures)")
        self.state = BreakerState.OPEN
        self.last_state_change = time.time()
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.open_count_1h += 1
        self._emit_a8_event("circuit_opened", {"reason": "consecutive_failures"})
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        logger.info("A3→A6 Circuit Breaker: OPEN → HALF_OPEN (timeout expired)")
        self.state = BreakerState.HALF_OPEN
        self.last_state_change = time.time()
        self.consecutive_successes = 0
        self.last_probe_time = None
        self._emit_a8_event("circuit_half_open", {})
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        logger.info("A3→A6 Circuit Breaker: HALF_OPEN → CLOSED (recovery successful)")
        self.state = BreakerState.CLOSED
        self.last_state_change = time.time()
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self._emit_a8_event("circuit_closed", {"reason": "recovery_successful"})
    
    def _emit_a8_event(self, event_type: str, data: dict):
        """Emit telemetry event to A8."""
        logger.info(f"A8 Event: {event_type} - {data}")
    
    async def call(
        self,
        func: Callable,
        idempotency_key: str,
        payload: dict,
        *args,
        **kwargs
    ) -> dict:
        """
        Execute A6 call with circuit breaker protection.
        
        If circuit is OPEN, queue payload and return success for student flows.
        """
        if not FEATURE_FLAG_ENABLED:
            return await func(*args, **kwargs)
        
        async with self._lock:
            self._cleanup_old_failures()
            self._reset_open_count_if_needed()
            
            if self.state == BreakerState.OPEN:
                if time.time() - self.last_state_change >= self.OPEN_DURATION_SECONDS:
                    self._transition_to_half_open()
                else:
                    await self._enqueue_payload(idempotency_key, payload)
                    return {"status": "queued", "idempotency_key": idempotency_key}
            
            if self.state == BreakerState.HALF_OPEN:
                if not await self._should_allow_probe():
                    await self._enqueue_payload(idempotency_key, payload)
                    return {"status": "queued", "idempotency_key": idempotency_key}
                self.last_probe_time = time.time()
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            async with self._lock:
                self.call_latencies.append(latency)
                self.call_results.append(True)
                self._trim_metrics()
                
                self.consecutive_failures = 0
                self.consecutive_successes += 1
                self.failure_times.clear()
                
                if self.state == BreakerState.HALF_OPEN:
                    if self.consecutive_successes >= self.RECOVERY_THRESHOLD:
                        self._transition_to_closed()
            
            return result
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            
            async with self._lock:
                self.call_latencies.append(latency)
                self.call_results.append(False)
                self._trim_metrics()
                
                self.failure_times.append(time.time())
                self.consecutive_failures += 1
                self.consecutive_successes = 0
                
                if self.state == BreakerState.HALF_OPEN:
                    logger.warning("A3→A6 Circuit Breaker: HALF_OPEN → OPEN (probe failed)")
                    self.state = BreakerState.OPEN
                    self.last_state_change = time.time()
                    self.open_count_1h += 1
                    self._emit_a8_event("circuit_opened", {"reason": "probe_failed"})
                    
                elif len(self.failure_times) >= self.FAILURE_THRESHOLD:
                    self._transition_to_open()
                
                await self._enqueue_payload(idempotency_key, payload)
            
            logger.error(f"A3→A6 call failed: {e}")
            return {"status": "queued", "idempotency_key": idempotency_key, "error": str(e)}
    
    async def _enqueue_payload(self, idempotency_key: str, payload: dict):
        """Add payload to backlog queue."""
        for entry in self.backlog:
            if entry.idempotency_key == idempotency_key:
                logger.debug(f"Duplicate idempotency_key, skipping: {idempotency_key}")
                return
        
        now = datetime.utcnow()
        entry = BacklogEntry(
            id=f"bl_{int(time.time()*1000)}_{random.randint(1000, 9999)}",
            idempotency_key=idempotency_key,
            payload_json=json.dumps(payload),
            first_seen_at=now,
            next_retry_at=now + timedelta(seconds=self._calculate_backoff(0)),
            attempts=0,
            status="pending"
        )
        self.backlog.append(entry)
        logger.info(f"Enqueued payload: {idempotency_key}, backlog depth: {len(self.backlog)}")
        self._emit_a8_event("payload_enqueued", {"idempotency_key": idempotency_key})
    
    def _trim_metrics(self):
        """Keep only recent metrics for P95 calculation."""
        max_size = 1000
        if len(self.call_latencies) > max_size:
            self.call_latencies = self.call_latencies[-max_size:]
        if len(self.call_results) > max_size:
            self.call_results = self.call_results[-max_size:]
    
    def get_p95_latency(self) -> float:
        """Calculate P95 latency from recent calls."""
        if not self.call_latencies:
            return 0.0
        sorted_latencies = sorted(self.call_latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_error_rate(self) -> float:
        """Calculate error rate from recent calls."""
        if not self.call_results:
            return 0.0
        failures = sum(1 for r in self.call_results if not r)
        return failures / len(self.call_results)
    
    def get_metrics(self) -> BreakerMetrics:
        """Get current metrics for A8 telemetry."""
        cutoff = time.time() - 300
        failures_5m = len([t for t in self.failure_times if t > cutoff])
        
        return BreakerMetrics(
            breaker_state=self.state.value,
            failures_last_5m=failures_5m,
            open_count_1h=self.open_count_1h,
            provider_backlog_depth=len(self.backlog),
            dlq_depth=len(self.dlq),
            a3_call_p95_ms_to_a6=self.get_p95_latency(),
            a3_call_error_rate_to_a6=self.get_error_rate(),
            last_updated=datetime.utcnow().isoformat()
        )
    
    async def process_backlog(self, call_func: Callable) -> dict:
        """
        Process backlog entries. Call this periodically.
        
        Drain rate: ≥5 rps without impacting P95 >1.25s
        """
        if self._backlog_processor_running:
            return {"status": "already_running"}
        
        if self.state != BreakerState.CLOSED:
            return {"status": "circuit_not_closed", "state": self.state.value}
        
        self._backlog_processor_running = True
        processed = 0
        failed = 0
        
        try:
            now = datetime.utcnow()
            ready_entries = [
                e for e in self.backlog 
                if e.status == "pending" and e.next_retry_at <= now
            ]
            
            for entry in ready_entries[:5]:
                if self.get_p95_latency() > 1250:
                    logger.warning("Backlog processing paused: P95 > 1.25s")
                    break
                
                try:
                    payload = json.loads(entry.payload_json)
                    await call_func(payload)
                    
                    self.backlog.remove(entry)
                    processed += 1
                    logger.info(f"Backlog entry processed: {entry.idempotency_key}")
                    
                except Exception as e:
                    entry.attempts += 1
                    
                    if entry.attempts >= self.BACKLOG_MAX_ATTEMPTS:
                        entry.status = "dead_letter"
                        self.backlog.remove(entry)
                        self.dlq.append(entry)
                        logger.error(f"Entry moved to DLQ: {entry.idempotency_key}")
                        self._emit_a8_event("dlq_entry", {"idempotency_key": entry.idempotency_key})
                    else:
                        delay = self._calculate_backoff(entry.attempts)
                        entry.next_retry_at = now + timedelta(seconds=delay)
                        logger.warning(f"Retry scheduled for {entry.idempotency_key}: attempt {entry.attempts}, delay {delay:.1f}s")
                    
                    failed += 1
                
                await asyncio.sleep(0.2)
            
            return {"processed": processed, "failed": failed, "remaining": len(self.backlog)}
            
        finally:
            self._backlog_processor_running = False
    
    def get_status(self) -> dict:
        """Get circuit breaker status for health checks."""
        return {
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "backlog_depth": len(self.backlog),
            "dlq_depth": len(self.dlq),
            "open_count_1h": self.open_count_1h,
            "p95_ms": self.get_p95_latency(),
            "error_rate": self.get_error_rate(),
            "feature_enabled": FEATURE_FLAG_ENABLED,
            "state_uptime_seconds": round(time.time() - self.last_state_change, 2)
        }


a3_a6_breaker = A3A6CircuitBreaker()


def should_throttle() -> bool:
    """Check if throttle conditions are met per A8 Kill/Throttle rules."""
    metrics = a3_a6_breaker.get_metrics()
    return (
        10 <= metrics.provider_backlog_depth <= 30 or
        1250 <= metrics.a3_call_p95_ms_to_a6 < 1500
    )


def should_kill() -> bool:
    """Check if kill conditions are met per A8 Kill/Throttle rules."""
    metrics = a3_a6_breaker.get_metrics()
    return (
        metrics.provider_backlog_depth > 30 or
        metrics.a3_call_p95_ms_to_a6 >= 1500 or
        metrics.a3_call_error_rate_to_a6 >= 0.01
    )
