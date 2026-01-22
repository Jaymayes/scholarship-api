# A8 Telemetry Audit

**Run ID**: CEOSPRINT-20260121-VERIFY-ZT3G-V2S2-028  
**Status**: ⚠️ DEGRADED (A8 404)

---

## Telemetry Flow Status

### Primary Path (A0 ← Apps)
| App | Event Type | Status | Last Seen |
|-----|------------|--------|-----------|
| A1 | app_heartbeat | ✅ Flowing | 04:22:53Z |
| A6 | system_health | ✅ Flowing | 04:23:31Z |
| A9 | app_heartbeat | ✅ Flowing | 04:23:17Z |

### A8 Event Bus Status
- **URL**: https://event-bus-jamarrlmayes.replit.app
- **Health**: 404 Not Found
- **POST+GET Checksum**: Cannot verify

---

## Ingestion Metrics (from logs)

| Metric | Value |
|--------|-------|
| Telemetry batch accepted | 1 |
| Telemetry batch failed | 0 |
| Duplicates | 0 |
| Missing base_url | 0 |

---

## Fallback Mechanism

- Primary: A8 (UNAVAILABLE - 404)
- Fallback: A2 (UNAVAILABLE - 404)
- Local spool: business_events table (ACTIVE)

---

## Verdict

**A8 Telemetry**: ⚠️ DEGRADED

Apps are successfully sending telemetry directly to A0 via `/api/analytics/events`. A8 checksum round-trip cannot be verified due to 404.

**Impact**: Cannot achieve 3-of-3 evidence for apps relying on A8 correlation.
