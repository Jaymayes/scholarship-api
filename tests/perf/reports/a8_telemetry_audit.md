# A8 Telemetry Audit
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-036

## Status: BLOCKED

### A8 auto-com-center: UNVERIFIED
- Required: POST/GET /api/events + /health
- Remediation: manual_intervention_manifest.md

## Verification Commands
```bash
# POST
curl -X POST "https://<A8_HOST>/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d '{"kind":"verify"}'

# GET
curl "https://<A8_HOST>/api/events/<event_id>"
```

## Ingestion Target
- Required: ≥99% success
- Status: UNVERIFIED

## Verdict: BLOCKED
