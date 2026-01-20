# Metrics Endpoints Validation Report

**Date:** 2026-01-20  
**Phase:** 3  
**Status:** IMPLEMENTED

## Endpoint Details

### GET /metrics/p95

**Purpose:** Returns P50/P95 latency metrics over a 10-minute sliding window.

**Response Schema:**
```json
{
  "window_sec": 600,
  "p50_ms": <float>,
  "p95_ms": <float>,
  "sample_count": <int>,
  "timestamp": "<ISO8601>"
}
```

**Implementation Files:**
- `routers/metrics_p95.py` - FastAPI router with GET /metrics/p95 endpoint
- `services/latency_metrics_collector.py` - Thread-safe latency collector with 10-minute sliding window

**Features:**
1. Thread-safe latency sample collection
2. 10-minute sliding window with automatic pruning
3. Accurate P50/P95 percentile calculation using linear interpolation
4. Falls back to synthetic probe metrics from pilot_controller when no samples exist
5. ISO8601 timestamp in UTC

**Validation:**
- Endpoint registered in main.py
- Response model validated via Pydantic
- Returns valid JSON matching the required schema

## Evidence

Endpoint successfully added and returns valid JSON response with:
- `window_sec`: 600 (10 minutes)
- `p50_ms`: 50th percentile latency
- `p95_ms`: 95th percentile latency  
- `sample_count`: Number of samples in window
- `timestamp`: ISO8601 formatted timestamp
