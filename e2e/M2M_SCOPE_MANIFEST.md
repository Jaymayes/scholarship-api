# Machine-to-Machine (M2M) Scope Manifest
## scholarship_api → scholarship_sage Integration

**APP_NAME**: scholarship_api | **APP_BASE_URL**: https://scholarship-api-jamarrlmayes.replit.app

**Generated**: 2025-11-05  
**CEO Directive**: M2M token issuance for scholarship_sage (2-hour SLA)  
**Rotation Policy**: 90 days

---

## Executive Summary

This document defines the Machine-to-Machine (M2M) authentication and authorization scopes for scholarship_sage to access scholarship_api. Per CEO directive, scholarship_sage requires read-only access to scholarships and anonymized student data for recommendation engine operations.

---

## Architecture Alignment

**Authentication Provider**: `scholar_auth` (centralized OIDC issuer)  
**Resource Server**: `scholarship_api` (validates tokens via JWKS)  
**Client Application**: `scholarship_sage` (M2M consumer)

**Critical**: scholarship_api is NOT an OIDC issuer. All M2M tokens must be issued by `scholar_auth` and validated by scholarship_api via JWKS endpoint.

---

## M2M Client Specification

### Client Identity
```json
{
  "client_id": "scholarship_sage_m2m",
  "client_type": "machine",
  "grant_types": ["client_credentials"],
  "token_endpoint_auth_method": "client_secret_post",
  "application_type": "service"
}
```

### Required Scopes

#### 1. `read:scholarships`
**Purpose**: Access scholarship catalog for recommendation matching  
**Permitted Operations**:
- `GET /api/v1/scholarships` - List all active scholarships
- `GET /api/v1/scholarships/{id}` - Get scholarship details
- `GET /api/v1/search` - Search scholarships (read-only)
- `GET /api/v1/scholarships/{id}/eligibility` - Get eligibility criteria

**Denied Operations**:
- Any `POST`, `PUT`, `PATCH`, `DELETE` operations
- Write access to scholarship data
- Administrative operations

**Data Exposure**:
- Full scholarship metadata (title, description, amount, deadline)
- Eligibility requirements (GPA, major, demographics)
- Provider information (non-sensitive)
- Application status (aggregated, no PII)

#### 2. `read:students_anonymized`
**Purpose**: Access anonymized student profiles for matching algorithms  
**Permitted Operations**:
- `GET /api/v1/students/profiles` - List student profiles (anonymized)
- `GET /api/v1/students/{id}/eligibility` - Get student eligibility factors

**Denied Operations**:
- Access to PII (names, emails, SSN, addresses)
- Write access to student data
- Direct student contact information

**Data Exposure (Anonymized)**:
- Student ID (hashed/pseudonymized)
- Academic profile (GPA, major, year, institution type)
- Demographic categories (aggregated, FERPA-compliant)
- Geographic region (state-level only, no addresses)
- Application history (scholarship IDs only, no essays/documents)

**PII Redaction Enforced**:
- All responses filtered through FERPA/COPPA redaction layer
- No names, emails, phone numbers, or addresses
- No free-text fields containing potential PII
- All student IDs hashed with one-way function

---

## Token Issuance Protocol

### Step 1: Client Registration (scholar_auth)
**Owner**: scholar_auth DRI  
**Action**: Register M2M client with scopes

```bash
POST https://scholar-auth.replit.app/oauth/register
Content-Type: application/json

{
  "client_name": "scholarship_sage_m2m",
  "grant_types": ["client_credentials"],
  "scope": "read:scholarships read:students_anonymized",
  "application_type": "service",
  "token_endpoint_auth_method": "client_secret_post"
}

Response:
{
  "client_id": "scholarship_sage_m2m",
  "client_secret": "[REDACTED - 90-day rotation]",
  "client_id_issued_at": 1730842800,
  "client_secret_expires_at": 1738704800,
  "scopes": ["read:scholarships", "read:students_anonymized"]
}
```

### Step 2: Token Acquisition (scholarship_sage)
**Owner**: scholarship_sage DRI  
**Action**: Obtain access token via client_credentials grant

```bash
POST https://scholar-auth.replit.app/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=scholarship_sage_m2m
&client_secret=[REDACTED]
&scope=read:scholarships read:students_anonymized

Response:
{
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMyJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read:scholarships read:students_anonymized"
}
```

### Step 3: API Access (scholarship_sage → scholarship_api)
**Owner**: scholarship_sage DRI  
**Action**: Call scholarship_api with bearer token

```bash
GET https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMyJ9...

Response: HTTP 200 OK (if scopes valid)
Response: HTTP 403 Forbidden (if scopes insufficient)
```

---

## Token Validation (scholarship_api)

### JWKS Validation Flow
1. Extract Bearer token from `Authorization` header
2. Verify token signature using scholar_auth JWKS endpoint
3. Validate token claims:
   - `iss`: Must match scholar_auth issuer
   - `aud`: Must include scholarship_api
   - `exp`: Must not be expired
   - `scope`: Must contain required scope for endpoint
4. Enforce scope-based access control
5. Return 401 if token invalid, 403 if scope insufficient

### Scope Enforcement Matrix

| Endpoint | Required Scope | Method | Notes |
|----------|---------------|--------|-------|
| `/api/v1/scholarships` | `read:scholarships` | GET | List scholarships |
| `/api/v1/scholarships/{id}` | `read:scholarships` | GET | Get scholarship details |
| `/api/v1/search` | `read:scholarships` | GET | Search scholarships |
| `/api/v1/students/profiles` | `read:students_anonymized` | GET | Anonymized profiles |
| `/api/v1/students/{id}/eligibility` | `read:students_anonymized` | GET | Eligibility factors |

**Denied Without Proper Scopes**:
- All `POST`, `PUT`, `PATCH`, `DELETE` operations require admin scopes (not granted to M2M)
- Write operations return HTTP 403 even with valid token

---

## Security Controls

### 1. Scope Least Privilege
- scholarship_sage receives ONLY read scopes
- No write, delete, or administrative capabilities
- Scopes cannot be escalated client-side

### 2. Token Rotation
**Policy**: 90-day mandatory rotation  
**Process**:
1. scholar_auth issues new `client_secret` at T-7 days before expiration
2. scholarship_sage updates to new secret (parallel operation)
3. Old secret revoked at T+0 (hard cutoff)
4. scholar_auth logs all token issuance events

**Next Rotation**: February 3, 2026 (90 days from Nov 5, 2025)

### 3. PII Redaction
- All `/students/*` endpoints filter responses through FERPA/COPPA layer
- Automatic redaction of names, emails, phones, addresses
- Hashed student IDs (one-way, non-reversible)
- No free-text fields that might contain PII

### 4. Rate Limiting
- M2M tokens subject to same rate limits as user tokens
- scholarship_sage: 300 requests/minute (aligned with 300 RPS SLO)
- Circuit breaker triggers at 80% of rate limit
- DDoS protection via WAF middleware

### 5. Audit Logging
- All M2M token usage logged with:
  - request_id for correlation
  - client_id (scholarship_sage_m2m)
  - endpoint accessed
  - scope used
  - timestamp and response code
- Logs retained 90 days for security audit
- Anomaly detection: alert if unexpected endpoint accessed

---

## Integration Checklist

### scholar_auth DRI (Immediate - T+0 to T+15)
- [ ] Register M2M client `scholarship_sage_m2m`
- [ ] Issue `client_id` and `client_secret`
- [ ] Configure scopes: `read:scholarships`, `read:students_anonymized`
- [ ] Set token TTL: 1 hour (renewable)
- [ ] Set secret expiration: 90 days
- [ ] Post credentials to secrets manager (encrypted)

### scholarship_api DRI (Immediate - T+0 to T+30)
- [ ] Validate JWKS endpoint connectivity to scholar_auth
- [ ] Implement scope enforcement on protected endpoints
- [ ] Add M2M-specific rate limiting (300 req/min)
- [ ] Test scope validation (200 for valid, 403 for invalid)
- [ ] Enable audit logging for M2M token usage
- [ ] Verify PII redaction on `/students/*` endpoints

### scholarship_sage DRI (T+30 to T+60)
- [ ] Retrieve M2M credentials from secrets manager
- [ ] Implement client_credentials token flow
- [ ] Add token refresh logic (renew at 50% TTL)
- [ ] Test authorization (expect 403 on write endpoints)
- [ ] Implement exponential backoff on rate limit errors
- [ ] Schedule 90-day rotation reminder

---

## Evidence and Compliance

### Smoke Test
```bash
# Test 1: Valid scope - should succeed
curl -H "Authorization: Bearer [M2M_TOKEN]" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

Expected: HTTP 200 OK

# Test 2: Valid scope - anonymized students
curl -H "Authorization: Bearer [M2M_TOKEN]" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/students/profiles

Expected: HTTP 200 OK (PII redacted)

# Test 3: Invalid scope - write operation
curl -X POST -H "Authorization: Bearer [M2M_TOKEN]" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

Expected: HTTP 403 Forbidden (scope insufficient)

# Test 4: Expired token
curl -H "Authorization: Bearer [EXPIRED_TOKEN]" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships

Expected: HTTP 401 Unauthorized
```

### FERPA/COPPA Compliance
- ✅ No PII in M2M responses
- ✅ Student data anonymized via hashing
- ✅ Audit trail for all access
- ✅ Least-privilege scopes enforced
- ✅ 90-day credential rotation

---

## Monitoring and Alerts

### Key Metrics
- `m2m_requests_total{client_id="scholarship_sage_m2m"}` - Total requests
- `m2m_requests_unauthorized_total` - Failed auth attempts
- `m2m_requests_forbidden_total` - Scope violations
- `m2m_token_refresh_total` - Token renewals
- `m2m_rate_limit_exceeded_total` - Rate limit breaches

### Alert Thresholds
- **Critical**: `m2m_requests_unauthorized_total` > 10/minute (possible credential leak)
- **Warning**: `m2m_requests_forbidden_total` > 5/minute (scope misconfiguration)
- **Info**: Token expiring in <7 days (rotation reminder)

---

## Rollback Plan

If M2M integration causes issues:

1. **Immediate**: Revoke `client_secret` at scholar_auth (kills all tokens)
2. **T+5 min**: scholarship_sage falls back to cached recommendation data
3. **T+15 min**: Root cause analysis via Sentry traces (request_id correlation)
4. **T+30 min**: Issue new credentials with corrected scopes
5. **T+60 min**: Resume normal operations

---

## Sign-Off

**Document Owner**: scholarship_api DRI  
**Approval**: CEO Directive (2-hour SLA)  
**Effective**: 2025-11-05  
**Next Review**: 2026-02-03 (90-day rotation)

**Status**: ✅ **SCOPE MANIFEST DELIVERED**

---

*This manifest defines the M2M authentication contract between scholarship_api and scholarship_sage. Token issuance is the responsibility of scholar_auth (centralized OIDC provider). Token validation and scope enforcement is the responsibility of scholarship_api (resource server).*
