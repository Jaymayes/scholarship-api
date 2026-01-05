# A8 Data Lineage Report
**Audit Date**: 2026-01-05T09:19:00Z
**Protocol Version**: v3.5.1

## Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Source Apps (A1-A7)                         │
│  A1:auth  A2:api  A3:agent  A4:sage  A5:pilot  A6:provider  A7:page │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     POST /events             │
              │  Headers:                    │
              │   - x-scholar-protocol: v3.5.1│
              │   - x-app-label: <app>       │
              │   - x-event-id: <uuid>       │
              │   - authorization: Bearer    │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     A8 auto_com_center       │
              │  1. Validate headers         │
              │  2. Upsert by x-event-id     │
              │  3. Persist to DB            │
              │  4. Return persisted:true    │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      Dashboard Tiles         │
              │  - Finance (PaymentSuccess)  │
              │  - B2B (ProviderOnboarded)   │
              │  - SEO (PageView)            │
              │  - SLO (KPI_SNAPSHOT)        │
              └──────────────────────────────┘
```

## Verified Events

| Event Type | Source | Tile | persisted | Evidence |
|------------|--------|------|-----------|----------|
| AUDIT_PROBE | A2 | SLO | ✅ | evt_1767601004190 |
| PaymentSuccess | A2 | Finance | ✅ | 181ms latency |
| KPI_SNAPSHOT | A2 | SLO | ✅ | evt_1767595395245 |

## Namespace Tagging

All audit events tagged with:
- `namespace: simulated_audit`
- `simulated: true`

This ensures test data does not contaminate production analytics.
