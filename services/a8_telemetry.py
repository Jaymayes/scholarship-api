"""
A8 Telemetry Emitter - SEV-2 CIR-20260119-001
Emits metrics to A8 every minute per CEO directive
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
import httpx

from database.session_manager import get_pool_status

logger = logging.getLogger("scholarship_api.a8_telemetry")

class A8TelemetryEmitter:
    
    def __init__(self):
        self.a8_url = os.environ.get("EVENT_BUS_URL", "")
        self.a8_token = os.environ.get("EVENT_BUS_TOKEN", "")
        self.incident_id = "CIR-20260119-001"
        self.enabled = bool(self.a8_url and self.a8_token)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._error_count = 0
        self._last_emit: Optional[str] = None
        
        if self.enabled:
            logger.info(f"A8 Telemetry Emitter initialized for {self.incident_id}")
        else:
            logger.warning("A8 Telemetry disabled - missing EVENT_BUS_URL or EVENT_BUS_TOKEN")
    
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
        
        payload = {
            "event_type": "sev2_telemetry",
            "incident_id": self.incident_id,
            "source": "A2_CORE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.a8_url}/api/v1/events",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.a8_token}",
                        "Content-Type": "application/json",
                        "X-Incident-ID": self.incident_id
                    }
                )
                
                if response.status_code in [200, 201, 202]:
                    self._error_count = 0
                    self._last_emit = datetime.now(timezone.utc).isoformat()
                    logger.debug(f"A8 telemetry emitted: {response.status_code}")
                    return True
                else:
                    self._error_count += 1
                    logger.warning(f"A8 emission failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            self._error_count += 1
            logger.error(f"A8 emission error: {e}")
            return False
    
    async def emit_loop(self, interval_seconds: int = 60):
        self._running = True
        logger.info(f"A8 telemetry loop started: {interval_seconds}s interval")
        
        while self._running:
            try:
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
    
    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "error_count": self._error_count,
            "last_emit": self._last_emit,
            "incident_id": self.incident_id
        }

a8_telemetry = A8TelemetryEmitter()
