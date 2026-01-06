# A8 Data Lineage Report
**Scholar Ecosystem Telemetry**
**Date**: 2026-01-06

---

## Telemetry Architecture

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│   A5    │    │   A6    │    │   A7    │
│ Student │    │Provider │    │Marketing│
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     │              │              │
     ▼              ▼              ▼
┌─────────────────────────────────────────┐
│                   A2                     │
│           Scholarship API                │
│         (Telemetry Aggregator)           │
│   business_events table + KPI views      │
└─────────────────────┬───────────────────┘
                      │
                      │ v3.5.1 Protocol
                      │ x-scholar-protocol
                      │ x-app-label
                      │ x-event-id
                      ▼
              ┌───────────────┐
              │      A8       │
              │ Command Center│
              │  (Telemetry   │
              │    Sink)      │
              └───────────────┘
```

## Event Flow Verification

### A2 → A8 Event Emission

| Test | Result |
|------|--------|
| Endpoint | `POST /events` |
| Protocol | v3.5.1 |
| HTTP Code | 200 |
| Persisted | true |
| Latency | 91ms |

### Event Schema

Required headers:
- `x-scholar-protocol: v3.5.1`
- `x-app-label: A2`
- `x-event-id: <uuid>`

Required payload fields:
- `event_name`
- `source_app_id`
- `ts` (epoch milliseconds)
- `namespace` (optional, for demo/test data)

### Data Sources in A2

| Source | Table/View | Status |
|--------|------------|--------|
| Business Events | `business_events` | ACTIVE |
| Revenue by Source | `revenue_by_source` view | ACTIVE |
| B2B Funnel | `b2b_funnel` view | ACTIVE |

### A8 Tiles Data

| Tile | Data Source | Status |
|------|-------------|--------|
| Finance | revenue_by_source | $179.99 |
| B2B Supply | b2b_funnel | 15 rows |
| SEO | A4/A7 events | Active |

## Demo Mode Isolation

| Namespace | Purpose | Isolated |
|-----------|---------|----------|
| `simulated_audit` | Audit testing | YES |
| `stripe_mode=test` | Stripe test | YES |
| Production | Live data | YES |

## Verified Event Types

| Event | Source | Status |
|-------|--------|--------|
| `fee_captured` | A2 | ✅ $150.00 |
| `payment_succeeded` | A5 | ✅ $29.99 |
| `provider_connected` | A6 | ✅ |
| `listing_created` | A6 | ✅ |
| `audit_probe` | A2 | ✅ persisted |

---

## Conclusion

Telemetry is flowing correctly from A2 to A8 with v3.5.1 protocol compliance. Revenue data ($179.99) is being tracked and aggregated. Demo mode namespacing is working correctly to isolate test data.
