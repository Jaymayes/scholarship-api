# A8 Telemetry Audit - Canary Stage 1

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE1-030  
**Updated**: 2026-01-22T05:07:52Z

---

## A8 Event Bus Status

| Check | Result |
|-------|--------|
| /health | ❌ 404 Not Found |
| Checksum Round-Trip | Cannot verify |

---

## Local Telemetry (A0)

| Check | Result |
|-------|--------|
| POST /api/analytics/events | ✅ 200 |
| Event Accepted | 1 |
| Event Failed | 0 |
| Duplicates | 0 |

---

## Canary Event

```json
{
  "event_id": "81e62388-700d-4839-ac48-7d689f69af88",
  "event_name": "CANARY_STAGE1_TEST",
  "app": "canary_test",
  "env": "prod",
  "stage": "canary_5pct",
  "run_id": "CEOSPRINT-20260121-CANARY-STAGE1-030"
}
```

---

## Verdict

**DEGRADED** - A8 unavailable (404). Telemetry flowing to A0 directly at 100% acceptance rate.
