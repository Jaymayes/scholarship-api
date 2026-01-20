"""
Latency Metrics Collector - Phase 3
Tracks request latencies over a 10-minute sliding window for P50/P95 calculations.
"""

import time
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
import logging

logger = logging.getLogger("scholarship_api.latency_metrics")

WINDOW_SECONDS = 600  # 10 minutes


@dataclass
class LatencyMetrics:
    window_sec: int
    p50_ms: float
    p95_ms: float
    sample_count: int
    timestamp: str


class LatencyMetricsCollector:
    """Thread-safe latency collector with 10-minute sliding window."""

    def __init__(self, window_seconds: int = WINDOW_SECONDS):
        self.window_seconds = window_seconds
        self._samples: deque = deque()
        self._lock = threading.Lock()
        logger.info(f"LatencyMetricsCollector initialized with {window_seconds}s window")

    def record(self, latency_ms: float) -> None:
        """Record a latency sample with current timestamp."""
        now = time.time()
        with self._lock:
            self._samples.append((now, latency_ms))
            self._prune_old_samples(now)

    def _prune_old_samples(self, now: float) -> None:
        """Remove samples outside the window."""
        cutoff = now - self.window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _calculate_percentile(self, latencies: List[float], percentile: float) -> float:
        """Calculate percentile from sorted list."""
        if not latencies:
            return 0.0
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        index = (percentile / 100.0) * (n - 1)
        lower = int(index)
        upper = min(lower + 1, n - 1)
        fraction = index - lower
        return sorted_latencies[lower] * (1 - fraction) + sorted_latencies[upper] * fraction

    def get_metrics(self) -> LatencyMetrics:
        """Get current P50/P95 metrics for the window."""
        now = time.time()
        with self._lock:
            self._prune_old_samples(now)
            latencies = [sample[1] for sample in self._samples]

        p50 = self._calculate_percentile(latencies, 50.0)
        p95 = self._calculate_percentile(latencies, 95.0)

        return LatencyMetrics(
            window_sec=self.window_seconds,
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            sample_count=len(latencies),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def get_raw_latencies(self) -> List[float]:
        """Get raw latency samples (for debugging)."""
        now = time.time()
        with self._lock:
            self._prune_old_samples(now)
            return [sample[1] for sample in self._samples]


# Global singleton instance
latency_collector = LatencyMetricsCollector()
