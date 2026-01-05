# A8 Data Lineage Report
**Audit Date**: 2026-01-05T08:17:00Z

## Telemetry Contract v3.5.1

### Required Headers
| Header | Value | Purpose |
|--------|-------|---------|
| content-type | application/json | Payload format |
| x-scholar-protocol | v3.5.1 | Protocol version |
| x-app-label | <app_name> | Source app identifier |
| x-event-id | <uuid-v4> | Idempotency key |
| authorization | Bearer <A8_KEY> | Authentication |

### Event Flow

```
Source Apps (A1-A7) 
    │
    ├── POST /events
    │   ├── Headers: v3.5.1 + Bearer token
    │   └── Body: { event_type, occurred_at, actor_id, payload }
    │
    ▼
A8 auto_com_center
    │
    ├── Validate headers
    ├── Upsert by x-event-id (idempotency)
    ├── Persist to database
    └── Return { accepted: true, persisted: true }
```

## Verified Events in A8

| Event Type | Source | persisted | Evidence |
|------------|--------|-----------|----------|
| AUDIT_PROBE | A2 | ✅ true | evt_1767601004190_m5ahnqeu3 |
| PaymentSuccess | A2 | ✅ true | evt_1767595279193 |
| KPI_SNAPSHOT | A2 | ✅ true | evt_1767595395245_ggotb5l2j |

## Dashboard Tile Mapping

| Tile | Event Types | Source Apps |
|------|-------------|-------------|
| Finance | PaymentSuccess, fee_captured | A2, A6 |
| B2B Supply | ProviderOnboarded, listing_created | A6 |
| SEO | PageView, lead_captured | A7 |
| SLO | KPI_SNAPSHOT, app_heartbeat | A1-A7 |
| Learning | SageAssist, ScholarshipMatchResult | A3, A4 |

## Data Quality Notes

- All test events tagged with `simulated_audit` namespace
- Events include proper timestamps (ISO-8601)
- Idempotency enforced via x-event-id headers
- No PII leakage detected in test payloads

## Conclusion

A8 telemetry pipeline is **FUNCTIONAL**. Events are being accepted and persisted with correct v3.5.1 headers.
