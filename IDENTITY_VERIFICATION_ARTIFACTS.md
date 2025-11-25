scholarship_api | https://scholarship-api-jamarrlmayes.replit.app

# Identity Verification Artifacts — Agent3 v3.0 Section B

**Generated**: 2025-11-25T17:56:00Z

---

## 1. GET /healthz

### Headers
```
x-system-identity: scholarship_api
x-app-base-url: https://scholarship-api-jamarrlmayes.replit.app
content-type: application/json
```

### Body
```json
{
  "status": "ok",
  "version": "1.0.0",
  "system_identity": "scholarship_api",
  "base_url": "https://scholarship-api-jamarrlmayes.replit.app",
  "timestamp": "2025-11-25T17:56:34.882439Z"
}
```

---

## 2. GET /version

### Headers
```
x-system-identity: scholarship_api
x-app-base-url: https://scholarship-api-jamarrlmayes.replit.app
content-type: application/json
```

### Body
```json
{
  "service": "scholarship_api",
  "version": "1.0.0",
  "git_sha": "workspace",
  "system_identity": "scholarship_api",
  "base_url": "https://scholarship-api-jamarrlmayes.replit.app",
  "semanticVersion": "1.0.0",
  "environment": "production"
}
```

---

## 3. GET /api/metrics/prometheus (sample)

```prometheus
# HELP app_info Application information
# TYPE app_info gauge
app_info{app_id="scholarship_api",base_url="https://scholarship-api-jamarrlmayes.replit.app",version="1.0.0"} 1.0

# HELP applications_submitted_total Total application submissions (v3.0)
# TYPE applications_submitted_total counter
applications_submitted_total{status="success"} 1.0

# HELP providers_total Total provider registrations
# TYPE providers_total counter
providers_total{status="success"} 1.0

# HELP debit_attempts_total Total credit debit operations (v3.0)
# TYPE debit_attempts_total counter
debit_attempts_total{status="success"} 1.0

# HELP fee_reports_total Total fee report operations
# TYPE fee_reports_total counter
fee_reports_total{status="success"} 1.0
```

---

## 4. POST /api/v1/applications/submit

### Request
```json
{"user_id": "v3_final_test", "scholarship_id": "sch_1"}
```

### Response
```json
{
  "application_id": "app_1764093394.056629_v3_final_test",
  "user_id": "v3_final_test",
  "scholarship_id": "sch_1",
  "status": "submitted",
  "submitted_at": "2025-11-25T17:56:34.195421Z",
  "system_identity": "scholarship_api",
  "base_url": "https://scholarship-api-jamarrlmayes.replit.app"
}
```

---

## 5. POST /api/v1/credits/debit

### Request
```json
{
  "user_id": "v3_test_user",
  "amount": 15,
  "reason": "ai_draft",
  "idempotency_key": "idem_v3_final_005"
}
```

### Response
```json
{
  "receipt_id": "rcpt_1764093394.46495_idem_v3_",
  "user_id": "v3_test_user",
  "amount": 15.0,
  "reason": "ai_draft",
  "idempotency_key": "idem_v3_final_005",
  "balance_before": 100.0,
  "balance_after": 85.0,
  "recorded_at": "2025-11-25T17:56:34.622750Z",
  "system_identity": "scholarship_api",
  "base_url": "https://scholarship-api-jamarrlmayes.replit.app"
}
```

---

## 6. POST /api/v1/fees/report (3% Platform Fee)

### Request
```json
{
  "provider_id": "prov_1",
  "amount": 500.00,
  "transaction_id": "txn_v3_final_test"
}
```

### Response
```json
{
  "fee_id": "fee_1764093394.69766_txn_v3_final_test",
  "provider_id": "prov_1",
  "amount": 500.0,
  "platform_fee": 15.0,
  "transaction_id": "txn_v3_final_test",
  "recorded_at": "2025-11-25T17:56:34.829345Z",
  "system_identity": "scholarship_api",
  "base_url": "https://scholarship-api-jamarrlmayes.replit.app"
}
```

**v3.0 Compliance**: ✅ 3% fee correctly computed ($500 × 0.03 = $15.00)

---

## Cross-App Verification

### scholar_auth OIDC Discovery
```json
{
  "issuer": "https://scholar-auth-jamarrlmayes.replit.app/oidc",
  "jwks_uri": "https://scholar-auth-jamarrlmayes.replit.app/oidc/jwks"
}
```

### scholar_auth JWKS
```json
{
  "keys_count": 1
}
```

**Status**: ✅ Reachable within 5s

---

## Final Status Line

```
scholarship_api | https://scholarship-api-jamarrlmayes.replit.app | Readiness: GO | Revenue-ready: NOW
```
