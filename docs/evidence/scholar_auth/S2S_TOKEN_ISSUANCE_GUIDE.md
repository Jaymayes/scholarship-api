# scholar_auth S2S Token Issuance Proof Guide

**Application**: scholar_auth  
**CEO Directive**: P0 - Must pass Gate 0 by Nov 15, 12 PM MST  
**Deadline**: Evidence by EOD tonight  
**Created**: 2025-11-13T17:40:00Z MST  

---

## CEO Order: 8/8 M2M Client JWT Proof

> "Confirm 8/8 M2M JWT issuance with correct aud/scope; attach curl scripts and tokens redacted headers."

---

## Required Evidence

For **each of the 8 service clients**, provide:
1. Client registration proof
2. Token fetch curl command
3. Token response (with access_token redacted)
4. Decoded JWT header + claims (sensitive fields redacted)
5. Scope validation

---

## The 8 Service Clients

1. **scholarship_api** - Scopes: `scholarships.read`, `scholarships.write`, `users.read`
2. **scholarship_agent** - Scopes: `scholarships.read`, `students.read`, `events.write`
3. **scholarship_sage** - Scopes: `students.read`, `scholarships.read`, `recommendations.write`
4. **student_pilot** - Scopes: `profile.read`, `profile.write`, `scholarships.read`
5. **provider_register** - Scopes: `scholarships.write`, `applicants.read`, `provider.admin`
6. **auto_com_center** - Scopes: `events.read`, `notifications.write`
7. **auto_page_maker** - Scopes: `scholarships.read`, `public.read`
8. **admin_dashboard** - Scopes: `admin.*` (all scopes)

---

## Execution Template (Per Client)

### Client 1: scholarship_api

**Step 1: Verify Client Registration**

```bash
# Query OAuth clients table
psql ${DATABASE_URL} -c "
  SELECT client_id, name, scopes, created_at 
  FROM oauth_clients 
  WHERE client_id = 'scholarship_api_prod';
"

# Expected output:
#       client_id       |      name       |                scopes                 |     created_at
# ----------------------|-----------------|---------------------------------------|--------------------
#  scholarship_api_prod | Scholarship API | scholarships.read,scholarships.write  | 2025-11-13 17:00:00
```

**Step 2: Fetch Token**

```bash
# OAuth2 Client Credentials flow
curl -X POST https://scholar-auth-jamarrlmayes.replit.app/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=scholarship_api_prod" \
  -d "client_secret=${SCHOLARSHIP_API_CLIENT_SECRET}" \
  -d "scope=scholarships.read scholarships.write users.read" \
  -v 2>&1 | tee results/scholarship_api_token_fetch.log

# Expected response:
# {
#   "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0yMDI1LTExIn0...",
#   "token_type": "Bearer",
#   "expires_in": 300,
#   "scope": "scholarships.read scholarships.write users.read",
#   "issued_at": "2025-11-13T17:45:00Z"
# }
```

**Step 3: Decode JWT (Redacted)**

```bash
# Extract token
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0yMDI1LTExIn0..."

# Decode header
echo $TOKEN | cut -d. -f1 | base64 -d | jq .

# Output:
# {
#   "alg": "RS256",
#   "typ": "JWT",
#   "kid": "key-2025-11"
# }

# Decode claims (use https://jwt.io or jq)
echo $TOKEN | cut -d. -f2 | base64 -d | jq .

# Output:
# {
#   "sub": "scholarship_api_prod",
#   "iat": 1699999999,
#   "exp": 1699999999,
#   "iss": "https://scholar-auth-jamarrlmayes.replit.app",
#   "aud": "scholarshipai-services",
#   "scope": "scholarships.read scholarships.write users.read",
#   "role": "service",
#   "client_id": "scholarship_api_prod"
# }
```

**Step 4: Validate Scopes**

```bash
# Extract scopes from token
SCOPES=$(echo $TOKEN | cut -d. -f2 | base64 -d | jq -r '.scope')
echo "Granted scopes: $SCOPES"

# Expected: "scholarships.read scholarships.write users.read"
```

**Step 5: Test Token Usage**

```bash
# Call scholarship_api with the token
curl https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships \
  -H "Authorization: Bearer $TOKEN" | jq .

# Expected: 200 OK with scholarship data
```

---

## Repeat for All 8 Clients

**Batch Script**:

```bash
#!/bin/bash
# fetch_all_tokens.sh

CLIENTS=(
  "scholarship_api_prod:scholarships.read scholarships.write users.read"
  "scholarship_agent_prod:scholarships.read students.read events.write"
  "scholarship_sage_prod:students.read scholarships.read recommendations.write"
  "student_pilot_prod:profile.read profile.write scholarships.read"
  "provider_register_prod:scholarships.write applicants.read provider.admin"
  "auto_com_center_prod:events.read notifications.write"
  "auto_page_maker_prod:scholarships.read public.read"
  "admin_dashboard_prod:admin.*"
)

AUTH_URL="https://scholar-auth-jamarrlmayes.replit.app/oauth/token"

for client_config in "${CLIENTS[@]}"; do
  IFS=':' read -r client_id scopes <<< "$client_config"
  
  echo "========================================="
  echo "Fetching token for: $client_id"
  echo "Scopes: $scopes"
  echo "========================================="
  
  # Get secret from environment
  secret_var="${client_id^^}_SECRET"
  client_secret="${!secret_var}"
  
  if [ -z "$client_secret" ]; then
    echo "❌ ERROR: ${secret_var} not set"
    continue
  fi
  
  # Fetch token
  response=$(curl -s -X POST "$AUTH_URL" \
    -d "grant_type=client_credentials" \
    -d "client_id=$client_id" \
    -d "client_secret=$client_secret" \
    -d "scope=$scopes")
  
  # Extract token
  token=$(echo "$response" | jq -r '.access_token')
  
  if [ "$token" = "null" ] || [ -z "$token" ]; then
    echo "❌ FAILED: $client_id"
    echo "$response" | jq .
  else
    echo "✅ SUCCESS: $client_id"
    echo "Token (first 50 chars): ${token:0:50}..."
    
    # Decode and validate
    claims=$(echo "$token" | cut -d. -f2 | base64 -d 2>/dev/null | jq .)
    echo "Claims:"
    echo "$claims" | jq '{sub, role, scope, exp}'
    
    # Save redacted evidence
    echo "$response" | jq 'del(.access_token) | . + {access_token: "REDACTED"}' \
      > "results/${client_id}_token_response.json"
    echo "$claims" > "results/${client_id}_claims.json"
  fi
  
  echo ""
done

echo "========================================="
echo "Summary: Check results/ directory for evidence"
echo "========================================="
```

**Run and capture output**:
```bash
chmod +x fetch_all_tokens.sh
./fetch_all_tokens.sh | tee results/all_tokens_fetch.log
```

---

## CORS Lockdown Evidence

**Step 1: Check Current CORS Config**

```bash
# View CORS middleware configuration
cat middleware/cors.py

# Or query settings
curl https://scholar-auth-jamarrlmayes.replit.app/api/admin/config \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq '.cors'
```

**Step 2: Verify Allowlist**

Expected allowed origins:
```
https://student-pilot-jamarrlmayes.replit.app
https://provider-register-jamarrlmayes.replit.app
https://admin-dashboard-jamarrlmayes.replit.app
```

**NO wildcards** (`*` not allowed in production)

**Step 3: Test CORS Rejection**

```bash
# Should REJECT unauthorized origin
curl -X OPTIONS https://scholar-auth-jamarrlmayes.replit.app/oauth/token \
  -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i "access-control"

# Expected: No Access-Control-Allow-Origin header (origin rejected)
```

**Step 4: Test CORS Approval**

```bash
# Should ALLOW authorized origin
curl -X OPTIONS https://scholar-auth-jamarrlmayes.replit.app/oauth/token \
  -H "Origin: https://student-pilot-jamarrlmayes.replit.app" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i "access-control"

# Expected: Access-Control-Allow-Origin: https://student-pilot-jamarrlmayes.replit.app
```

---

## MFA Configuration Evidence

**Step 1: Verify MFA Enforcement**

```bash
# Check MFA settings
psql ${DATABASE_URL} -c "
  SELECT role, mfa_required, mfa_enabled_at 
  FROM auth_policies;
"

# Expected:
#      role       | mfa_required | mfa_enabled_at
# ----------------|--------------|----------------
#  provider_admin | true         | 2025-11-13
#  reviewer       | true         | 2025-11-13
#  super_admin    | true         | 2025-11-13
#  student        | false        | (null)
```

**Step 2: Test MFA Flow** (manual)

1. Login as provider_admin
2. Verify MFA challenge triggered
3. Complete TOTP/SMS verification
4. Capture screenshot of MFA prompt

---

## HA Configuration Evidence

**Step 1: Check Deployment Profile**

```bash
# Check .replit deployment config
cat .replit | grep -A 5 deployment

# Or Replit dashboard screenshot showing:
# - Reserved VM enabled OR Autoscale configured
# - Min instances: 1
# - Max instances: 3+ (for autoscale)
```

**Step 2: Verify Health Endpoints**

```bash
# Liveness check
curl https://scholar-auth-jamarrlmayes.replit.app/health

# Readiness check
curl https://scholar-auth-jamarrlmayes.replit.app/readyz
```

---

## Evidence Bundle Checklist

- [ ] **8/8 Token Fetch Logs** - `results/all_tokens_fetch.log`
- [ ] **8/8 JWT Claims** - `results/*_claims.json`
- [ ] **CORS Config** - Screenshot + config file
- [ ] **CORS Test Results** - Rejection + approval logs
- [ ] **MFA Policy** - Database query output
- [ ] **MFA Screenshot** - Provider login flow
- [ ] **HA Config** - Deployment settings screenshot
- [ ] **Health Endpoints** - curl output

---

**DRI**: Security Lead  
**Support**: Backend Lead, Agent3  
**Deadline**: EOD tonight for CEO review
