# A8 Telemetry Audit
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030
**Timestamp**: 2026-01-18T18:40:19Z

## Status: BLOCKED

### A8 auto-com-center
- Required: POST /api/events with X-Trace-Id
- Required: GET /api/events/{id} returning checksum
- Required: ≥99% ingestion rate
- Status: External workspace not accessible
- Remediation: manual_intervention_manifest.md

## Verification Protocol
```bash
# POST
curl -X POST "https://<A8_HOST>/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d '{"kind":"verify"}'

# GET (checksum round-trip)
curl "https://<A8_HOST>/api/events/<event_id>"
```

## Verdict: BLOCKED
