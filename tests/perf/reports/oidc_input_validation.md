# Phase 2 Auth/OIDC Repair: Token Endpoint Input Validation

**Date**: 2026-01-20  
**Component**: scholarship_api (A2)  
**Phase**: Auth/OIDC Repair - Phase 2  
**Status**: ✅ IMPLEMENTED

## Summary

This document captures the implementation of RFC 6749 compliant input validation for OAuth 2.0 token endpoints.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth/token` | POST | OAuth 2.0 token endpoint (primary) |
| `/token` | POST | Token endpoint alias |

## Validation Rules (RFC 6749)

### Required Parameters

| Parameter | Requirement | Error Code |
|-----------|-------------|------------|
| client_id | MUST be present | invalid_request |
| grant_type | MUST be present | invalid_request |

### Allowed Grant Types

```python
ALLOWED_GRANT_TYPES = {
    "password",
    "client_credentials", 
    "authorization_code",
    "refresh_token"
}
```

Grant types NOT in this set return `unsupported_grant_type` error.

### Grant-Specific Validation

| Grant Type | Required Parameters | Error if Missing |
|------------|---------------------|------------------|
| password | username, password | invalid_request |
| client_credentials | client_secret | invalid_request |
| authorization_code | code | invalid_request |
| refresh_token | refresh_token | invalid_request |

## Error Response Format (RFC 6749 Section 5.2)

All errors return HTTP 400 (or 401 for auth failures) with JSON body:

```json
{
  "error": "error_code",
  "error_description": "Human-readable description"
}
```

### Error Codes

| Error Code | HTTP Status | When Used |
|------------|-------------|-----------|
| invalid_request | 400 | Missing required parameter |
| invalid_client | 401 | Client authentication failed |
| invalid_grant | 401 | Invalid credentials or grant |
| unsupported_grant_type | 400 | Grant type not supported |

### Response Headers

All token responses include:

```
Cache-Control: no-store
Pragma: no-cache
```

## Implementation

### File: `routers/oauth_token.py`

New router implementing:

1. `/oauth/token` POST endpoint
2. `/token` POST alias endpoint
3. RFC 6749 error response helper
4. Grant type validation
5. Parameter validation per grant type

### Registration in `main.py`

```python
from routers.oauth_token import router as oauth_token_router
app.include_router(oauth_token_router)
```

## Test Cases

### 1. Missing client_id

```bash
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/oauth/token \
  -d "grant_type=password&username=test&password=test"
```

**Expected Response:**
```json
{
  "error": "invalid_request",
  "error_description": "The 'client_id' parameter is required."
}
```

### 2. Missing grant_type

```bash
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/oauth/token \
  -d "client_id=test_client"
```

**Expected Response:**
```json
{
  "error": "invalid_request",
  "error_description": "The 'grant_type' parameter is required."
}
```

### 3. Invalid grant_type

```bash
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/oauth/token \
  -d "client_id=test_client&grant_type=implicit"
```

**Expected Response:**
```json
{
  "error": "unsupported_grant_type",
  "error_description": "The grant type 'implicit' is not supported. Allowed: authorization_code, client_credentials, password, refresh_token"
}
```

### 4. Valid password grant (missing credentials)

```bash
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/oauth/token \
  -d "client_id=test_client&grant_type=password"
```

**Expected Response:**
```json
{
  "error": "invalid_request",
  "error_description": "The 'username' and 'password' parameters are required for password grant."
}
```

## Metrics

All token requests are tracked via:

```python
metrics_service.record_auth_request("/oauth/token", status, http_code)
```

Status values: `success`, `failure`

## Localhost Probe Removal

### Before (synthetic_monitors.py)

```python
monitoring_service = SyntheticMonitoringService("http://localhost:5000")
```

### After

```python
import os
_monitor_base_url = os.environ.get(
    "HEALTH_URL", 
    "https://scholarship-api-jamarrlmayes.replit.app"
).rstrip("/health").rstrip("/readiness").rstrip("/")

monitoring_service = SyntheticMonitoringService(_monitor_base_url)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| HEALTH_URL | https://scholarship-api-jamarrlmayes.replit.app/health | Health check URL |
| READY_URL | https://scholarship-api-jamarrlmayes.replit.app/readiness | Readiness check URL |

## Compliance

- [x] client_id validation (REQUIRED)
- [x] grant_type validation (REQUIRED)
- [x] RFC 6749 error format with error_description
- [x] 400 status for validation errors
- [x] 401 status for authentication errors
- [x] Cache-Control: no-store header
- [x] Localhost probes removed

## Audit Trail

| Date | Action | Author |
|------|--------|--------|
| 2026-01-20 | Created /oauth/token endpoint | Agent3 |
| 2026-01-20 | Created /token alias endpoint | Agent3 |
| 2026-01-20 | Removed localhost from synthetic monitors | Agent3 |
| 2026-01-20 | Added HEALTH_URL/READY_URL config | Agent3 |

---

**Artifact**: `tests/perf/reports/oidc_input_validation.md`  
**Phase**: 2 - Auth/OIDC Repair  
**Protocol**: v3.5.1
