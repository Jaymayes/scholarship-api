# Canary Cutover Plan: DataService Read Paths

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S2-BUILD-061  
**Protocol**: AGENT3_HANDSHAKE v41 (V2 Sprint-2 + Canary Cutover)  
**Created**: 2026-01-21T10:20:00Z

## Executive Summary

Progressive canary rollout of DataService read paths for A6 Provider Dashboard and A1 lightweight reads. Feature flag controls traffic percentage with automatic rollback on breach.

## Feature Flag Configuration

```python
DATASERVICE_READ_CANARY = os.getenv("DATASERVICE_READ_CANARY", "0")
# Values: 0 (disabled), 5, 25, 50, 100 (%)
```

## Rollout Schedule

| Stage | Traffic % | Duration | Observation Window | Go/No-Go Criteria |
|-------|-----------|----------|-------------------|-------------------|
| Stage 0 | 0% | - | Baseline | All systems nominal |
| Stage 1 | 5% | 10 min | Per-minute sampling | P95 ≤150ms, 5xx ≤0.1% |
| Stage 2 | 25% | 30 min | 5-min aggregates | P95 ≤140ms, 5xx ≤0.2% |
| Stage 3 | 50% | 60 min | 10-min aggregates | P95 ≤130ms, 5xx ≤0.3% |
| Stage 4 | 100% | 24h soak | 15-min aggregates | P95 ≤120ms, 5xx ≤0.5% |

## Services Under Canary

### A6 Provider Dashboard
- **Endpoint**: GET /api/v6/providers/{id}/dashboard
- **Current Path**: Direct Neon query via SQLAlchemy
- **Canary Path**: DataService GET /api/v1/providers/{id}
- **Rollback**: Revert to direct query

### A1 Lightweight Reads (Phase 2)
- **Endpoint**: GET /api/v1/sessions/{id}/basic
- **Current Path**: scholar_auth internal cache
- **Canary Path**: DataService GET /api/v1/users/{id}
- **Rollback**: Revert to cache lookup

## Canary Decision Logic

```python
def should_use_dataservice(request_id: str) -> bool:
    """Deterministic canary bucket based on request hash."""
    canary_pct = int(os.getenv("DATASERVICE_READ_CANARY", "0"))
    if canary_pct == 0:
        return False
    if canary_pct >= 100:
        return True
    # Deterministic bucket: hash(request_id) % 100 < canary_pct
    bucket = hash(request_id) % 100
    return bucket < canary_pct
```

## Hard Rollback Triggers

Any of the following triggers immediate rollback to 0%:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| DataService P95 | >150ms for 5 min | Rollback |
| DataService 5xx | ≥0.5% for 2 min | Rollback |
| Ledger mismatch | Any discrepancy | Rollback |
| A8 acceptance | <99% | Rollback |
| Event loop | ≥300ms twice | Rollback |

## Rollback Procedure

```bash
# Immediate rollback
export DATASERVICE_READ_CANARY=0

# Emit rollback event to A8
curl -X POST $A8_URL/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{"events":[{"app":"scholarship_api","event_name":"canary_rollback","properties":{"from_pct":25,"reason":"p95_breach"}}]}'

# Generate abort report
echo "Canary rollback at $(date)" >> tests/perf/reports/canary_abort.md
```

## Monitoring Dashboard

During canary, monitor:
1. `/metrics` - prometheus endpoint
2. Grafana dashboard: "V2 DataService Canary"
3. A8 telemetry: filter by `app=dataservice`

## Artifacts

- canary_plan.md (this document)
- canary_results.md (populated after rollout)
- canary_abort.md (only if rollback occurs)

---

**Status**: READY FOR STAGE 1  
**Approved By**: Agent (AGENT3_HANDSHAKE v41)
