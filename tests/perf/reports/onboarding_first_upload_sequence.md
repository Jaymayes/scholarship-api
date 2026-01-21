# Onboarding First-Upload Flow - Sequence Diagram & Documentation

## Overview

The First-Upload onboarding flow orchestrates guest user creation, document upload, and NLP scoring with A8 telemetry integration.

## Flow Sequence Diagram

```
┌─────────┐      ┌─────────────────────┐      ┌─────────────┐      ┌────────────┐
│ Client  │      │OnboardingOrchestrator│     │ DataService │      │ A8 Telemetry│
└────┬────┘      └──────────┬──────────┘      └──────┬──────┘      └─────┬──────┘
     │                      │                        │                   │
     │  POST /start         │                        │                   │
     │─────────────────────>│                        │                   │
     │                      │                        │                   │
     │                      │  Create Guest User     │                   │
     │                      │───────────────────────>│                   │
     │                      │                        │                   │
     │                      │  guest_id              │                   │
     │                      │<───────────────────────│                   │
     │                      │                        │                   │
     │                      │  GuestCreated Event    │                   │
     │                      │────────────────────────────────────────────>│
     │                      │                        │                   │
     │                      │  200 OK                │                   │
     │                      │<────────────────────────────────────────────│
     │                      │                        │                   │
     │  trace_id, guest_id  │                        │                   │
     │<─────────────────────│                        │                   │
     │                      │                        │                   │
     │  POST /upload        │                        │                   │
     │  (trace_id, file)    │                        │                   │
     │─────────────────────>│                        │                   │
     │                      │                        │                   │
     │                      │  Store Document        │                   │
     │                      │───────────────────────>│                   │
     │                      │                        │                   │
     │                      │  document_id           │                   │
     │                      │<───────────────────────│                   │
     │                      │                        │                   │
     │                      │  DocumentUploaded Event│                   │
     │                      │────────────────────────────────────────────>│
     │                      │                        │                   │
     │                      │  200 OK                │                   │
     │                      │<────────────────────────────────────────────│
     │                      │                        │                   │
     │  document_id         │                        │                   │
     │<─────────────────────│                        │                   │
     │                      │                        │                   │
     │  POST /process       │                        │                   │
     │  (trace_id)          │                        │                   │
     │─────────────────────>│                        │                   │
     │                      │                        │                   │
     │                      │  NLP Scoring (stub)    │                   │
     │                      │───────────────────────>│                   │
     │                      │                        │                   │
     │                      │  implicit_fit_score    │                   │
     │                      │<───────────────────────│                   │
     │                      │                        │                   │
     │                      │  Persist Score         │                   │
     │                      │───────────────────────>│                   │
     │                      │                        │                   │
     │                      │  DocumentScored Event  │                   │
     │                      │────────────────────────────────────────────>│
     │                      │                        │                   │
     │  implicit_fit_score  │                        │                   │
     │<─────────────────────│                        │                   │
     │                      │                        │                   │
```

## API Endpoints

### 1. POST /api/v2/onboarding/start

Initiates the onboarding flow by creating a guest user.

**Request:**
```json
{
  "email": "user@example.com",  // optional
  "metadata": {                  // optional
    "source": "landing_page",
    "campaign_id": "summer2025"
  }
}
```

**Response (200 OK):**
```json
{
  "trace_id": "onb-550e8400-e29b-41d4-a716-446655440000",
  "status": "guest_created",
  "guest_id": "guest-123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-01-21T10:30:00.000Z",
  "message": "Onboarding flow initiated successfully. Ready for document upload."
}
```

**Headers:**
- `X-Trace-Id`: (optional) Client-provided trace ID
- `X-Idempotency-Key`: (optional) Idempotency key for retry safety

### 2. POST /api/v2/onboarding/upload

Handles document upload for the active onboarding flow.

**Request (multipart/form-data):**
- `trace_id`: Flow trace ID from /start
- `file`: Document file (PDF, DOC, TXT, max 10MB)

**Response (200 OK):**
```json
{
  "trace_id": "onb-550e8400-e29b-41d4-a716-446655440000",
  "status": "upload_complete",
  "document_id": "doc-789e4567-e89b-12d3-a456-426614174000",
  "filename": "resume.pdf",
  "file_size_bytes": 245760,
  "message": "Document uploaded successfully. Ready for processing."
}
```

### 3. POST /api/v2/onboarding/process

Triggers NLP scoring on the uploaded document.

**Request:**
```json
{
  "trace_id": "onb-550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**
```json
{
  "trace_id": "onb-550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "document_id": "doc-789e4567-e89b-12d3-a456-426614174000",
  "implicit_fit_score": 0.8542,
  "message": "Document processed successfully. Implicit fit score: 0.8542"
}
```

### 4. GET /api/v2/onboarding/status/{trace_id}

Returns the current status of an onboarding flow.

**Response (200 OK):**
```json
{
  "trace_id": "onb-550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "guest_id": "guest-123e4567-e89b-12d3-a456-426614174000",
  "document_id": "doc-789e4567-e89b-12d3-a456-426614174000",
  "implicit_fit_score": 0.8542,
  "created_at": "2025-01-21T10:30:00.000Z",
  "updated_at": "2025-01-21T10:31:15.000Z",
  "error_message": null
}
```

## Flow States

| Status | Description |
|--------|-------------|
| `initiated` | Flow created, guest user pending |
| `guest_created` | Guest user created, ready for upload |
| `upload_pending` | Document upload in progress |
| `upload_complete` | Document stored, ready for processing |
| `scoring_in_progress` | NLP scoring running |
| `completed` | All steps completed successfully |
| `failed` | Flow failed (check error_message) |

## A8 Telemetry Events

All events are emitted to A8 with protocol v3.5.1:

### GuestCreated
```json
{
  "app": "onboarding_orchestrator",
  "env": "prod",
  "event_name": "GuestCreated",
  "ts": "2025-01-21T10:30:00.000Z",
  "actor_type": "system",
  "properties": {
    "guest_id": "guest-123...",
    "email_provided": true,
    "metadata": {},
    "flow_trace_id": "onb-550e8400...",
    "created_at": "2025-01-21T10:30:00.000Z"
  }
}
```

### DocumentUploaded
```json
{
  "app": "onboarding_orchestrator",
  "env": "prod",
  "event_name": "DocumentUploaded",
  "ts": "2025-01-21T10:30:30.000Z",
  "actor_type": "user",
  "properties": {
    "document_id": "doc-789...",
    "guest_id": "guest-123...",
    "filename": "resume.pdf",
    "content_type": "application/pdf",
    "file_size_bytes": 245760,
    "flow_trace_id": "onb-550e8400...",
    "uploaded_at": "2025-01-21T10:30:30.000Z"
  }
}
```

### DocumentScored
```json
{
  "app": "onboarding_orchestrator",
  "env": "prod",
  "event_name": "DocumentScored",
  "ts": "2025-01-21T10:31:15.000Z",
  "actor_type": "system",
  "properties": {
    "document_id": "doc-789...",
    "guest_id": "guest-123...",
    "implicit_fit_score": 0.8542,
    "flow_trace_id": "onb-550e8400...",
    "scoring_model": "nlp_stub_v1",
    "scored_at": "2025-01-21T10:31:15.000Z"
  }
}
```

## Retry & Backoff Strategy

Event emission uses exponential backoff:
- Max attempts: 3
- Base backoff: 0.5 seconds
- Backoff formula: `0.5 * 2^attempt` seconds
- Idempotency: Each event has unique `X-Idempotency-Key` header

## Error Handling

| Error Code | Scenario |
|------------|----------|
| 400 | Empty file, invalid trace_id format |
| 404 | Flow not found for trace_id |
| 413 | File exceeds 10MB limit |
| 500 | Event emission failure, internal error |

## Integration Notes

1. **Trace ID Propagation**: The `trace_id` returned from `/start` must be used in all subsequent calls.

2. **Header Requirements**: For A8 protocol v3.5.1 compliance:
   - `x-scholar-protocol: v3.5.1`
   - `x-event-id: <uuid>`
   - `X-Trace-Id: <trace_id>`
   - `X-Idempotency-Key: <unique_key>`

3. **NLP Scoring**: Current implementation uses a stub. See `nlp_scoring_contract.md` for the full NLP service interface.
