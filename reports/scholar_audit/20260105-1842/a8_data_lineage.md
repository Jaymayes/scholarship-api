# A8 Data Lineage
**Audit Date**: 2026-01-05T18:45:00Z

## Event Flow

```
Source Apps (A1-A7)
    │
    ├── Event Created
    │   └── Payload: {event_type, occurred_at, actor_id, payload}
    │
    ├── Headers Added
    │   ├── x-scholar-protocol: v3.5.1
    │   ├── x-app-label: <source_app>
    │   ├── x-event-id: <uuid-v4>
    │   └── authorization: Bearer <A8_KEY>
    │
    └── POST /events → A8
            │
            ├── Validate headers
            ├── Upsert by x-event-id (idempotency)
            ├── Persist to database
            └── Return {accepted: true, persisted: true}
```

## Tile Mapping

| Tile | Event Types | Source Apps |
|------|-------------|-------------|
| Finance | PaymentSuccess, fee_captured, payment_succeeded | A2, A6 |
| B2B Supply | ProviderOnboarded, listing_created, provider_connected | A6 |
| SEO | PageView, lead_captured, sitemap_updated | A7 |
| SLO | KPI_SNAPSHOT, app_heartbeat, SYSTEM_HEALTH | A1-A7 |

## Verified Events

All 4 domain events persisted successfully:

| Event | Tile | event_id | Status |
|-------|------|----------|--------|
| PaymentSuccess | Finance | evt_1767638700738 | ✅ |
| ProviderOnboarded | B2B | evt_1767638701051 | ✅ |
| PageView | SEO | evt_1767638701388 | ✅ |
| KPI_SNAPSHOT | SLO | evt_1767638701692 | ✅ |

## Namespace Tagging

All audit events include:
- `namespace: simulated_audit`
- `simulated: true`

This ensures clean separation from production data.

## Data Lineage Status

**Status**: ✅ VERIFIED - All domains flowing to A8 correctly
