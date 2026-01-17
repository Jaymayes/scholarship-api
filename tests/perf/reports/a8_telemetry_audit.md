# A8 Telemetry Audit
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-032
**Timestamp**: 2026-01-17T20:45:00Z

## Status: BLOCKED

### A8 auto-com-center (Not Verified)
- Status: BLOCKED
- Reason: External workspace not accessible
- Required: POST/GET /api/events round-trip
- Remediation: See manual_intervention_manifest.md

### Required for Verification
1. `POST /api/events` returns `{"success":true,"event_id":"..."}`
2. `GET /api/events/{event_id}` returns stored event
3. `/health` JSON marker
4. Republish to production

### Verification Commands
```bash
# POST event
EVENT=$(curl -sSL -X POST "https://<A8_HOST>/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-VERIFY-ZT3G-032.a8" \
  -d '{"kind":"verify"}')
echo "$EVENT"

# Extract event_id and GET
EVENT_ID=$(echo "$EVENT" | jq -r '.event_id')
curl -sSL "https://<A8_HOST>/api/events/${EVENT_ID}"
```

### Ingestion Target
- Required: ≥99% success rate
- Status: UNVERIFIED

### Verdict: BLOCKED

Telemetry service requires manual intervention from workspace owner.
