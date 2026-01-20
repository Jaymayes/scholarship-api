"""
Metrics P95 Endpoint - Phase 3
GET /metrics/p95 returns P50/P95 latency metrics over a 10-minute window.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from services.latency_metrics_collector import latency_collector
from services.pilot_controller import pilot_controller

router = APIRouter(tags=["Metrics"])


class P95Response(BaseModel):
    window_sec: int
    p50_ms: float
    p95_ms: float
    sample_count: int
    timestamp: str


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
    
    return P95Response(
        window_sec=metrics.window_sec,
        p50_ms=metrics.p50_ms,
        p95_ms=metrics.p95_ms,
        sample_count=metrics.sample_count,
        timestamp=metrics.timestamp
    )
