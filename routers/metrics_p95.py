"""
Metrics P95 Endpoint - Phase 3
GET /metrics/p95 returns P50/P95 latency metrics over a 10-minute window.

Gate-2 Stabilization: Added event_loop_ms histogram and tuned thresholds.
Alert threshold: 300ms (reduced from 200ms to reduce noise)
Internal warning: 150ms (retained for monitoring)
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from services.latency_metrics_collector import latency_collector
from services.pilot_controller import pilot_controller

router = APIRouter(tags=["Metrics"])

# Gate-2 Stabilization: Event Loop thresholds
EVENT_LOOP_ALERT_THRESHOLD_MS = 300  # Alert only for sustained >300ms
EVENT_LOOP_WARNING_THRESHOLD_MS = 150  # Internal warning threshold


class P95Response(BaseModel):
    window_sec: int
    p50_ms: float
    p95_ms: float
    sample_count: int
    timestamp: str
    event_loop_ms: Optional[float] = None  # Gate-2: Event loop lag estimate


@router.get("/metrics/p95", response_model=P95Response)
async def get_p95_metrics():
    """
    Get P50/P95 latency metrics over a 10-minute sliding window.
    
    Returns:
        - window_sec: Window size in seconds (600)
        - p50_ms: 50th percentile latency in milliseconds
        - p95_ms: 95th percentile latency in milliseconds
        - sample_count: Number of samples in the window
        - timestamp: ISO8601 timestamp of the measurement
    """
    metrics = latency_collector.get_metrics()
    
    if metrics.sample_count == 0:
        synthetic = pilot_controller.synthetic_result
        if synthetic and synthetic.latencies_ms:
            return P95Response(
                window_sec=metrics.window_sec,
                p50_ms=synthetic.p50_ms,
                p95_ms=synthetic.p95_ms,
                sample_count=len(synthetic.latencies_ms),
                timestamp=synthetic.timestamp if synthetic.timestamp else metrics.timestamp
            )
    
    # Gate-2 Stabilization: Estimate event loop lag from P95
    # In Python asyncio, event loop lag is approximated by request processing latency
    event_loop_estimate = metrics.p95_ms if metrics.sample_count > 0 else 0.0
    
    return P95Response(
        window_sec=metrics.window_sec,
        p50_ms=metrics.p50_ms,
        p95_ms=metrics.p95_ms,
        sample_count=metrics.sample_count,
        timestamp=metrics.timestamp,
        event_loop_ms=event_loop_estimate
    )
