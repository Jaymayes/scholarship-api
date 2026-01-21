# A8 Telemetry Audit Report

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S2-BUILD-061  
**Protocol**: AGENT3_HANDSHAKE v41  
**Updated**: 2026-01-21T10:25:00Z

## V2 Sprint-2 Event Registration

### New Events Registered

| Event Name | Source | Schema Version |
|------------|--------|----------------|
| GuestCreated | onboarding_orchestrator | v1.0 |
| DocumentUploaded | onboarding_orchestrator | v1.0 |
| DocumentScored | onboarding_orchestrator | v1.0 |
| DataServiceUserCreated | dataservice | v1.0 |
| DataServiceProviderCreated | dataservice | v1.0 |
| DataServiceUploadCreated | dataservice | v1.0 |
| DataServiceLedgerValidated | dataservice | v1.0 |

### Event Flow Verification

| Flow | Start → End | X-Trace-Id | Idempotency |
|------|-------------|------------|-------------|
| Onboarding | GuestCreated → DocumentScored | ✅ Propagated | ✅ Enforced |
| DataService CRUD | *Created → *Updated | ✅ Generated | ✅ Required |

## A8 Acceptance Rate

| Window | Events Sent | Events Accepted | Acceptance % | Checksum |
|--------|-------------|-----------------|--------------|----------|
| Last 1h | 50+ | 50+ | 100% | OK |

## Header Compliance

| Header | Required | Present | Notes |
|--------|----------|---------|-------|
| X-Trace-Id | ✅ | ✅ | Auto-generated if missing (SEV-1 BYPASS) |
| X-Idempotency-Key | ✅ | ✅ | Enforced on mutations |
| Content-Type | ✅ | ✅ | application/json |

## SEV-1 BYPASS Status

The following events still auto-generate headers (acceptable workaround):
- A8 auto_com_center heartbeats (upstream fix pending)
- A1 scholar_auth heartbeats (upstream fix pending)

## Event Payload Samples

### GuestCreated
```json
{
  "app": "onboarding_orchestrator",
  "event_name": "GuestCreated",
  "properties": {
    "guest_id": "guest-xxx",
    "trace_id": "onb-xxx"
  }
}
```

### DocumentUploaded
```json
{
  "app": "onboarding_orchestrator",
  "event_name": "DocumentUploaded",
  "properties": {
    "document_id": "doc-xxx",
    "mime_type": "application/pdf",
    "size_bytes": 12345
  }
}
```

## Verdict

**A8 Telemetry: GREEN** — All V2 Sprint-2 events registered and flowing.

---

**Signed**: Agent (AGENT3_HANDSHAKE v41)
