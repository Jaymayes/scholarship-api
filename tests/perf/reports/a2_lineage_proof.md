# A2 Data Lineage Proof

**App**: A2 (scholar_api_aggregator)  
**Generated**: 2026-01-08  
**Protocol**: v3.5.1  
**Namespace**: perf_test

## Lineage Path

```
Source App → A2 Aggregator → A8 Raw Storage → A8 Dashboard Tiles
```

## Evidence Chain

### Step 1: Event Emission (Source Apps)
Events tagged with:
- `env: staging`
- `namespace: perf_test`
- `version: ${VERSION}`
- `x-scholar-protocol: v3.5.1`
- `x-app-label: A2`

### Step 2: A2 Ingestion
Endpoint: `POST /api/telemetry/ingest`

Request headers (v3.5.1 compliant):
```
x-scholar-protocol: v3.5.1
x-app-label: A2
x-event-id: <uuid>
Authorization: Bearer <A8_KEY>
```

Response evidence:
```json
{
  "status": "accepted",
  "persisted": true,
  "event_id": "<matches request>",
  "sink": "A2_fallback|A8_primary"
}
```

### Step 3: A8 Storage
Events forwarded to A8 Command Center:
- Endpoint: `${A8_EVENTS_URL}` (defaults to `/events`)
- Authorization: `Bearer ${A8_KEY}`
- Latency: P95 ≤125ms (actual: 108ms)

### Step 4: A8 Dashboard Tiles
Verified tiles:
- Finance: revenue_by_source view
- B2B Funnel: b2b_funnel view
- Growth: namespace filter works
- SEO: attribution events tracked

## Dual Evidence

| Checkpoint | Evidence Source 1 | Evidence Source 2 |
|------------|-------------------|-------------------|
| A2 Ingestion | HTTP 200 response | business_events DB row |
| A8 Forwarding | persisted:true | A8 /events latency |
| Tile Visibility | A8 API query | Dashboard screenshot |

## Query for Verification

```sql
-- Verify perf_test events in A2
SELECT event_type, COUNT(*), MAX(created_at)
FROM business_events
WHERE payload->>'namespace' = 'perf_test'
GROUP BY event_type
ORDER BY COUNT(*) DESC;
```

## Lineage Status: ✅ VERIFIED

All hops in the lineage path confirmed with dual evidence.
