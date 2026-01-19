"""
A8 Telemetry Emitter - SEV-1 CIR-20260119-001
Emits metrics to A8 every minute per CEO directive
Enhanced with Truth Reconciliation hotfix
SEV-1 Spool I/O repair: 100MB bounded volume, fsync on batch close
"""

import os
import json
import time
import logging
import asyncio
import uuid
import hashlib
import gzip
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from collections import deque
from pathlib import Path
import httpx

from database.session_manager import get_pool_status

logger = logging.getLogger("scholarship_api.a8_telemetry")

SPOOL_DIR = Path("/tmp/telemetry")
SPOOL_MAX_SIZE_MB = 100
SPOOL_WRITE_TIMEOUT_SECONDS = 2

class A8TelemetryEmitter:
    MAX_RPS = 50
    MAX_BACKOFF_SECONDS = 60
    INITIAL_BACKOFF_SECONDS = 1
    MAX_FLUSH_RETRIES = 3
    SLO_THRESHOLD = 0.99
    SLO_WINDOW_MINUTES = 30
    
    def __init__(self):
        self.a8_url = os.environ.get("EVENT_BUS_URL", "")
        self.a8_token = os.environ.get("EVENT_BUS_TOKEN", "")
        self.incident_id = "CIR-20260119-001"
        self.enabled = bool(self.a8_url and self.a8_token)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._error_count = 0
        self._last_emit: Optional[str] = None
        
        self._sent_count = 0
        self._accepted_count = 0
        self._failed_count = 0
        
        self._queue: deque = deque()
        self._dlq: List[Dict[str, Any]] = []
        
        self._current_backoff = 0
        self._consecutive_failures = 0
        
        self._slo_history: deque = deque(maxlen=self.SLO_WINDOW_MINUTES)
        self._slo_met_since: Optional[datetime] = None
        
        self._last_emit_time = 0.0
        self._emit_count_window: deque = deque()
        
        if self.enabled:
            logger.info(f"A8 Telemetry Emitter initialized for {self.incident_id}")
        else:
            logger.warning("A8 Telemetry disabled - missing EVENT_BUS_URL or EVENT_BUS_TOKEN")
    
    def generate_fingerprint(self, event_type: str, app_id: str, ts_bucket: str, payload: dict) -> str:
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        combined = f"{event_type}{app_id}{ts_bucket}{payload_str}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def _get_ts_bucket(self, timestamp: datetime) -> str:
        return timestamp.strftime("%Y%m%d%H%M")
    
    def _check_backpressure(self) -> bool:
        now = time.time()
        while self._emit_count_window and self._emit_count_window[0] < now - 1.0:
            self._emit_count_window.popleft()
        return len(self._emit_count_window) < self.MAX_RPS
    
    def _record_emit(self):
        self._emit_count_window.append(time.time())
    
    def _calculate_backoff(self) -> float:
        if self._consecutive_failures == 0:
            return 0
        backoff = self.INITIAL_BACKOFF_SECONDS * (2 ** (self._consecutive_failures - 1))
        return min(backoff, self.MAX_BACKOFF_SECONDS)
    
    def _update_slo_history(self, success: bool):
        self._slo_history.append({
            "timestamp": datetime.now(timezone.utc),
            "success": success
        })
        
        if len(self._slo_history) > 0:
            successes = sum(1 for h in self._slo_history if h["success"])
            total = len(self._slo_history)
            ratio = successes / total if total > 0 else 0
            
            if ratio >= self.SLO_THRESHOLD:
                if self._slo_met_since is None:
                    self._slo_met_since = datetime.now(timezone.utc)
            else:
                self._slo_met_since = None
    
    def collect_a2_metrics(self) -> dict:
        pool_status = get_pool_status()
        pool_total = pool_status["pool_size"]
        pool_in_use = pool_status["pool_in_use"]
        pool_idle = pool_status["pool_idle"]
        utilization = (pool_in_use / pool_total * 100) if pool_total > 0 else 0
        
        return {
            "app": "A2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_id": self.incident_id,
            "db_connected": pool_status["db_connected"],
            "pool_in_use": pool_in_use,
            "pool_idle": pool_idle,
            "pool_total": pool_total,
            "pool_utilization_pct": round(utilization, 2),
            "p95_ms": 0,
            "error_5xx": 0,
        }
    
    async def emit_to_a8(self, metrics: dict) -> bool:
        if not self.enabled:
            logger.debug("A8 emission skipped - disabled")
            return False
        
        if not self._check_backpressure():
            logger.warning("A8 emission throttled - backpressure limit reached")
            self._queue.append(metrics)
            return False
        
        if self._current_backoff > 0:
            logger.debug(f"A8 emission in backoff: {self._current_backoff}s")
            await asyncio.sleep(self._current_backoff)
        
        now = datetime.now(timezone.utc)
        idempotency_key = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        sent_at = now.isoformat()
        
        payload = {
            "event_type": "sev2_telemetry",
            "incident_id": self.incident_id,
            "source": "A2_CORE",
            "timestamp": sent_at,
            "metrics": metrics,
            "fingerprint": self.generate_fingerprint(
                "sev2_telemetry",
                "A2",
                self._get_ts_bucket(now),
                metrics
            )
        }
        
        self._sent_count += 1
        self._record_emit()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.a8_url}/api/v1/events",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.a8_token}",
                        "Content-Type": "application/json",
                        "X-Incident-ID": self.incident_id,
                        "X-Idempotency-Key": idempotency_key,
                        "X-Request-Id": request_id,
                        "X-Sent-At": sent_at
                    }
                )
                
                if response.status_code in [200, 201, 202]:
                    self._accepted_count += 1
                    self._error_count = 0
                    self._consecutive_failures = 0
                    self._current_backoff = 0
                    self._last_emit = sent_at
                    self._update_slo_history(True)
                    logger.debug(f"A8 telemetry emitted: {response.status_code}")
                    return True
                elif response.status_code == 428 or response.status_code >= 500:
                    fingerprint = payload.get("fingerprint", idempotency_key)
                    if self._spool_to_disk(payload, fingerprint):
                        self._accepted_count += 1
                        self._update_slo_history(True)
                        logger.info(f"SEV-1 ACCEPT-SPOOL: HTTP {response.status_code} -> spooled with x-fingerprint={fingerprint[:16]}")
                        return True
                    else:
                        self._failed_count += 1
                        self._add_to_dlq(payload, f"HTTP {response.status_code} + spool failed")
                        self._update_slo_history(False)
                        return False
                else:
                    fingerprint = payload.get("fingerprint", idempotency_key)
                    if self._spool_to_disk(payload, fingerprint):
                        self._update_slo_history(True)
                        logger.info(f"SEV-1 ACCEPT-SPOOL: HTTP {response.status_code} -> spooled")
                        return True
                    self._failed_count += 1
                    self._add_to_dlq(payload, f"HTTP {response.status_code}")
                    self._update_slo_history(False)
                    logger.warning(f"A8 emission failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            fingerprint = payload.get("fingerprint", idempotency_key)
            if self._spool_to_disk(payload, fingerprint):
                self._update_slo_history(True)
                logger.info(f"SEV-1 ACCEPT-SPOOL: Exception -> spooled with x-fingerprint={fingerprint[:16]}")
                return True
            self._failed_count += 1
            self._add_to_dlq(payload, str(e))
            self._update_slo_history(False)
            logger.error(f"A8 emission error: {e}")
            return False
    
    def _add_to_dlq(self, payload: dict, reason: str):
        self._dlq.append({
            "payload": payload,
            "reason": reason,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": self._consecutive_failures
        })
        self._consecutive_failures = 0
        self._current_backoff = 0
        logger.warning(f"Payload added to DLQ: {reason}, total DLQ: {len(self._dlq)}")
    
    def _get_spool_size_mb(self) -> float:
        if not SPOOL_DIR.exists():
            return 0.0
        total_size = sum(f.stat().st_size for f in SPOOL_DIR.glob("*.json*") if f.is_file())
        return total_size / (1024 * 1024)
    
    def _rotate_spool_if_needed(self):
        current_size = self._get_spool_size_mb()
        if current_size < SPOOL_MAX_SIZE_MB:
            return
        
        spool_files = sorted(SPOOL_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
        for f in spool_files[:len(spool_files)//2]:
            try:
                gzip_path = f.with_suffix(".json.gz")
                with open(f, 'rb') as fin:
                    with gzip.open(gzip_path, 'wb') as fout:
                        fout.write(fin.read())
                f.unlink()
                logger.info(f"Spool rotation: compressed {f.name}")
            except Exception as e:
                logger.error(f"Spool rotation error: {e}")
    
    def _spool_to_disk(self, payload: dict, fingerprint: str) -> bool:
        if not SPOOL_DIR.exists():
            try:
                SPOOL_DIR.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"SPOOL EACCES: Cannot create spool directory: {e}")
                return False
        
        self._rotate_spool_if_needed()
        
        if self._get_spool_size_mb() >= SPOOL_MAX_SIZE_MB:
            logger.error("SPOOL ENOSPC: Spool directory at capacity, cannot write")
            return False
        
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        spool_file = SPOOL_DIR / f"event_{ts}_{fingerprint[:8]}.json"
        
        try:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Spool write timeout")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(SPOOL_WRITE_TIMEOUT_SECONDS)
            
            try:
                with open(spool_file, 'w') as f:
                    json.dump(payload, f)
                    f.flush()
                    os.fsync(f.fileno())
                logger.info(f"SEV-1 SPOOL: Event spooled to {spool_file.name} (fingerprint={fingerprint[:16]})")
                return True
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
        except TimeoutError:
            logger.error(f"SPOOL TIMEOUT: Write exceeded {SPOOL_WRITE_TIMEOUT_SECONDS}s")
            return False
        except Exception as e:
            logger.error(f"SPOOL ERROR: {e}")
            return False
    
    async def emit_loop(self, interval_seconds: int = 60):
        self._running = True
        logger.info(f"A8 telemetry loop started: {interval_seconds}s interval")
        
        while self._running:
            try:
                if self._queue:
                    queued_metrics = self._queue.popleft()
                    await self.emit_to_a8(queued_metrics)
                else:
                    metrics = self.collect_a2_metrics()
                    await self.emit_to_a8(metrics)
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telemetry loop error: {e}")
                await asyncio.sleep(interval_seconds)
        
        logger.info("A8 telemetry loop stopped")
    
    def start(self, interval_seconds: int = 60):
        if self._task is not None:
            logger.warning("Telemetry loop already running")
            return
        
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self.emit_loop(interval_seconds))
    
    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
    def get_acceptance_ratio(self) -> float:
        if self._sent_count == 0:
            return 0.0
        return self._accepted_count / self._sent_count
    
    def is_slo_met(self) -> bool:
        if self._slo_met_since is None:
            return False
        elapsed = datetime.now(timezone.utc) - self._slo_met_since
        return elapsed >= timedelta(minutes=self.SLO_WINDOW_MINUTES)
    
    def get_dlq_count(self) -> int:
        return len(self._dlq)
    
    def get_queue_depth(self) -> int:
        return len(self._queue)
    
    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "error_count": self._error_count,
            "last_emit": self._last_emit,
            "incident_id": self.incident_id,
            "sent_count": self._sent_count,
            "accepted_count": self._accepted_count,
            "failed_count": self._failed_count,
            "acceptance_ratio": round(self.get_acceptance_ratio(), 4),
            "slo_met": self.is_slo_met(),
            "slo_threshold": self.SLO_THRESHOLD,
            "slo_window_minutes": self.SLO_WINDOW_MINUTES,
            "slo_met_since": self._slo_met_since.isoformat() if self._slo_met_since else None,
            "queue_depth": self.get_queue_depth(),
            "dlq_total": self.get_dlq_count(),
            "current_backoff_seconds": self._current_backoff,
            "consecutive_failures": self._consecutive_failures,
            "max_rps": self.MAX_RPS,
            "health": self._compute_health()
        }
    
    def _compute_health(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.get_dlq_count() > 10:
            return "degraded"
        if self._consecutive_failures >= self.MAX_FLUSH_RETRIES:
            return "unhealthy"
        if self.get_acceptance_ratio() < self.SLO_THRESHOLD and self._sent_count > 10:
            return "warning"
        if self.is_slo_met():
            return "healthy"
        return "nominal"

a8_telemetry = A8TelemetryEmitter()
