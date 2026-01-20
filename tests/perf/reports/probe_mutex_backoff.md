# Probe De-duplication Mechanism

**Phase 3 Additional Repair - CIR-20260119-001**  
**Date:** 2026-01-20  
**Status:** ✅ IMPLEMENTED

## Overview

Probe de-duplication ensures only one synthetic probe runs per target URL at a time. This prevents duplicate probes from overwhelming targets and provides fair resource sharing.

## Implementation Details

### Distributed Mutex Per Target

Each probe target URL is hashed to create a unique mutex key:

```python
def get_target_key(self, url: str) -> str:
    """Generate consistent key for target URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]
```

### Lock Acquisition Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Probe Start │────▶│ Try Acquire  │────▶│ Lock Free?  │
└─────────────┘     │    Lock      │     └──────┬──────┘
                    └──────────────┘            │
                           ▲                    │
                           │              ┌─────┴─────┐
                           │              │   YES     │ NO
                           │              ▼           ▼
                    ┌──────┴───────┐  ┌──────────┐  ┌─────────────┐
                    │ Retry After  │◀─│  Probe   │  │  Backoff    │
                    │   Backoff    │  │ Execute  │  │  ±20% Jitter│
                    └──────────────┘  └──────────┘  └─────────────┘
```

### Random Jitter ±20%

Each backoff interval has ±20% jitter applied to prevent thundering herd:

```python
def apply_jitter(self, base_interval: float) -> float:
    """Apply ±20% random jitter to interval."""
    jitter_range = base_interval * self.jitter_pct  # 0.20
    return base_interval + random.uniform(-jitter_range, jitter_range)
```

**Examples:**
- 2s base → 1.6s to 2.4s actual
- 5s base → 4.0s to 6.0s actual
- 10s base → 8.0s to 12.0s actual

### Backoff Sequence: 2s, 5s, 10s

When a lock is held, the backoff sequence escalates:

| Attempt | Base Backoff | With Jitter (±20%) |
|---------|-------------|-------------------|
| 1 | 2s | 1.6s - 2.4s |
| 2 | 5s | 4.0s - 6.0s |
| 3+ | 10s | 8.0s - 12.0s |

```python
backoff_sequence: List[float] = field(default_factory=lambda: [2.0, 5.0, 10.0])
```

### Lock Timeout

Locks automatically expire after 60 seconds to prevent deadlocks:

```python
lock_timeout_sec: float = 60.0
```

## Data Structure

```python
@dataclass
class ProbeMutexState:
    active_probes: Dict[str, float]      # target_key -> lock_time
    backoff_attempts: Dict[str, int]     # target_key -> attempt_count
    backoff_sequence: List[float]        # [2.0, 5.0, 10.0]
    jitter_pct: float                    # 0.20 (±20%)
    lock_timeout_sec: float              # 60.0
```

## API Endpoints

### Get Probe Mutex Status
```
GET /api/internal/pilot/probe-mutex/status
```

Response:
```json
{
  "active_probes": 0,
  "active_probe_keys": [],
  "backoff_attempts": {},
  "config": {
    "backoff_sequence_sec": [2.0, 5.0, 10.0],
    "jitter_pct": 0.2,
    "lock_timeout_sec": 60.0
  },
  "public_base_url": "https://..."
}
```

## Integration with Synthetic Probes

The mutex is integrated into `run_synthetic_login_test()`:

```python
# Try to acquire lock
lock_result = self.probe_mutex.try_acquire_lock(provider_login_url)
if not lock_result["acquired"]:
    backoff_sec = lock_result["backoff_sec"]
    await asyncio.sleep(backoff_sec)
    # Retry once after backoff
    lock_result = self.probe_mutex.try_acquire_lock(provider_login_url)
    if not lock_result["acquired"]:
        return SyntheticLoginResult(passed=False, ...)

try:
    # Execute probe iterations with jittered delays
    for i in range(iterations):
        jittered_delay = self.probe_mutex.apply_jitter(0.1)
        # ... probe execution ...
        await asyncio.sleep(jittered_delay)
finally:
    # Always release lock
    self.probe_mutex.release_lock(provider_login_url)
```

## Logging

All mutex operations are logged for debugging:

| Event | Log Level | Message Pattern |
|-------|-----------|-----------------|
| Lock Acquired | DEBUG | `PROBE MUTEX: Acquired lock for {key}` |
| Lock Held | INFO | `PROBE MUTEX: Lock held for {key}, backoff={sec}s` |
| Lock Released | DEBUG | `PROBE MUTEX: Released lock for {key}` |

## Verification Checklist

- [x] Distributed mutex keyed by URL hash (SHA256, 16 chars)
- [x] Random jitter ±20% applied to all backoff intervals
- [x] Backoff sequence: 2s, 5s, 10s (escalating)
- [x] Lock timeout: 60s (auto-release on stale locks)
- [x] Jitter applied between probe iterations (±20% of 0.1s)
- [x] API endpoint exposes mutex status
- [x] Lock always released in `finally` block

## Files Modified

- `services/pilot_controller.py`: Added `ProbeMutexState` dataclass, integrated into `run_synthetic_login_test()`
- `routers/pilot.py`: Added `/probe-mutex/status` endpoint

## Related Documentation

- `tests/perf/reports/synthetics_public_urls.md` - Public URL configuration
