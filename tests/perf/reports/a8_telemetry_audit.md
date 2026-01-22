# A8 Telemetry Audit - Canary Stages 1 & 2

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE2-031  
**Updated**: 2026-01-22T05:41:11Z

---

## A8 Event Bus Status

| Check | Result |
|-------|--------|
| /health | ❌ 404 Not Found |
| Checksum Round-Trip | Cannot verify |

---

## Local Telemetry (A0) - Both Stages

| Stage | Event Name | Event ID | Status |
|-------|------------|----------|--------|
| 1 | CANARY_STAGE1_TEST | 81e62388-700d-4839-ac48-7d689f69af88 | ✅ Accepted |
| 2 | CANARY_STAGE2_TEST | b8c3fd19-e0ac-4f84-a8f3-10595d032567 | ✅ Accepted |

---

## Ingestion Metrics

| Metric | Stage 1 | Stage 2 |
|--------|---------|---------|
| Accepted | 1 | 1 |
| Failed | 0 | 0 |
| Duplicates | 0 | 0 |
| Ingestion Rate | 100% | 100% |

---

## Verdict

**DEGRADED** - A8 unavailable (404). Telemetry flowing to A0 directly at 100% acceptance rate.
