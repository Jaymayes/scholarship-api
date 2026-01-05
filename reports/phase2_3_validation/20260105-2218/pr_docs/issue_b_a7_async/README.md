# Issue B: A7 Async Ingestion Refactor

## Status: NEW IMPLEMENTATION (Requires A7 Project Access)

## Problem
- A7 /health P95: 234ms (exceeds 150ms target by 84ms)
- Root cause: Synchronous third-party calls (SendGrid) on hot path
- Every request waits for external API response

## Solution
Adopt 202-Accepted + Worker/Queue pattern with:
1. Immediate response (202 Accepted)
2. Background task processing
3. Idempotency keys for deduplication
4. Circuit breaker for external services
5. Exponential backoff on retries

## Design

### Before (Synchronous)
```
Request → Process → SendGrid API (300ms) → Response
Total: ~300-400ms
```

### After (Async)
```
Request → Validate → Queue Event → Return 202 (10ms)
                      ↓
              Background Worker → SendGrid API
```

## Feature Flag
```python
ASYNC_INGESTION_ENABLED = os.getenv("ASYNC_INGESTION_ENABLED", "false").lower() == "true"
```

## Expected Improvement
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| P95 | 234ms | ≤80ms | -65% |
| P99 | 304ms | ≤120ms | -60% |

## Risk Analysis
- **Medium Risk**: Architectural change
- **Rollback**: Set `ASYNC_INGESTION_ENABLED=false` for sync behavior
- **Data Safety**: Idempotency keys prevent duplicates

## Files to Create/Modify
- `app/routes/ingest.py` (new async endpoint)
- `app/workers/event_processor.py` (background worker)
- `app/utils/circuit_breaker.py` (circuit breaker)
- `app/utils/idempotency.py` (idempotency store)
