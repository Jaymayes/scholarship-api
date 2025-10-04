# Auth-Dependent Test Suite - 13 Tests
**For:** QA Lead  
**SLA:** Start immediately after WAF patch; complete within 2 hours  
**Priority:** P0 - Critical Path to Launch  
**Executive Directive:** CEO 24-hour conditional launch plan

---

## Overview

This test suite covers all 13 features that were blocked during initial readiness testing due to the WAF authentication blocker. Once the WAF patch is deployed and auth endpoints are functional, execute these tests to validate 100% pass rate (T+4h gate requirement).

---

## Prerequisites

**Before Running Tests:**
1. ✅ WAF patch deployed (auth endpoints exempt from SQL injection checks)
2. ✅ Auth endpoints return 200/401 (not 403 WAF blocks)
3. ✅ Test credentials available (admin/admin123 or equivalent)
4. ✅ Test environment: Production mode with auth enabled

---

## Test Suite: 13 Auth-Dependent Tests

### Category 1: Authentication System (3 tests)

#### Test 1.1: User Login - Valid Credentials
```bash
# Test successful login
curl -X POST http://localhost:5000/api/v1/auth/login-simple \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Expected Response (200 OK):
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# Validation:
✓ Status code: 200
✓ access_token present (JWT format)
✓ token_type: "bearer"
✓ No WAF_SQLI_001 error
```

#### Test 1.2: User Login - Invalid Credentials
```bash
# Test failed login
curl -X POST http://localhost:5000/api/v1/auth/login-simple \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrong_password"}'

# Expected Response (401 Unauthorized):
{
  "detail": "Incorrect username or password"
}

# Validation:
✓ Status code: 401 (NOT 403 WAF block)
✓ Error message appropriate
✓ No access token provided
```

#### Test 1.3: API Key Creation
```bash
# Create API key for developer tier
curl -X POST http://localhost:5000/api/v1/launch/commercialization/api-keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "developer", "label": "test-prelaunch", "rate_limit_override": 1000}'

# Expected Response (200 OK or requires auth):
{
  "key": "sk_dev_...",
  "tier": "developer",
  "label": "test-prelaunch",
  "rate_limit": 1000
}

# Validation:
✓ API key created successfully OR auth required (not WAF blocked)
✓ Key format correct (sk_dev_...)
✓ Tier and label match request
```

---

### Category 2: Scholarship Search (2 tests)

#### Test 2.1: Search with API Key Authentication
```bash
# First, get API key from Test 1.3
API_KEY="<from test 1.3>"

# Search for engineering scholarships
curl -X GET "http://localhost:5000/api/v1/search?query=engineering&limit=5" \
  -H "X-API-Key: $API_KEY"

# Expected Response (200 OK):
{
  "scholarships": [...],
  "total": 5,
  "query": "engineering"
}

# Validation:
✓ Status code: 200
✓ Scholarships array returned
✓ Results relevant to "engineering"
✓ No rate limit errors
```

#### Test 2.2: Search with Filters (Deadline, Eligibility, Value)
```bash
# Search with multiple filters
curl -X GET "http://localhost:5000/api/v1/search?query=STEM&min_value=5000&max_deadline=2025-12-31&limit=10" \
  -H "X-API-Key: $API_KEY"

# Expected Response (200 OK):
{
  "scholarships": [...],
  "total": <count>,
  "filters_applied": {
    "min_value": 5000,
    "max_deadline": "2025-12-31"
  }
}

# Validation:
✓ Status code: 200
✓ Scholarships meet filter criteria
✓ All results >= $5000 value
✓ All deadlines <= 2025-12-31
```

---

### Category 3: Eligibility Checking (2 tests)

#### Test 3.1: Eligibility Check - High Match
```bash
# Check eligibility for Gates Millennium Scholarship
curl -X POST "http://localhost:5000/api/v1/eligibility/check" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_profile": {
      "gpa": 3.8,
      "major": "Computer Science",
      "year": "junior",
      "ethnicity": "underrepresented_minority"
    },
    "scholarship_id": "gates-millennium"
  }'

# Expected Response (200 OK):
{
  "eligible": true,
  "match_score": 85,
  "reasons": ["Strong GPA", "Relevant major", "Target demographic"],
  "scholarship_id": "gates-millennium"
}

# Validation:
✓ Status code: 200
✓ eligible: true/false (boolean)
✓ match_score: 0-100
✓ reasons array with explanations
```

#### Test 3.2: Eligibility Check - Low Match
```bash
# Check eligibility for scholarship with mismatch
curl -X POST "http://localhost:5000/api/v1/eligibility/check" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_profile": {
      "gpa": 2.5,
      "major": "Art History",
      "year": "senior"
    },
    "scholarship_id": "tech-innovators-award"
  }'

# Expected Response (200 OK):
{
  "eligible": false,
  "match_score": 15,
  "reasons": ["GPA below minimum", "Major not tech-related"],
  "scholarship_id": "tech-innovators-award"
}

# Validation:
✓ Status code: 200
✓ eligible: false
✓ match_score reflects low compatibility
✓ reasons explain why not eligible
```

---

### Category 4: Personalized Recommendations (2 tests)

#### Test 4.1: Recommendations for STEM Student
```bash
# Get recommendations for engineering major
curl -X POST "http://localhost:5000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_profile": {
      "gpa": 3.7,
      "major": "Engineering",
      "interests": ["STEM", "Innovation", "Technology"],
      "year": "sophomore"
    }
  }'

# Expected Response (200 OK):
{
  "recommendations": [
    {
      "scholarship_id": "...",
      "title": "...",
      "match_score": 90,
      "reasons": ["..."]
    },
    ...
  ],
  "total": 10
}

# Validation:
✓ Status code: 200
✓ recommendations array with ≥5 scholarships
✓ Each has match_score and reasons
✓ Results sorted by match_score (descending)
✓ STEM-relevant scholarships prioritized
```

#### Test 4.2: Recommendations for Liberal Arts Student
```bash
# Get recommendations for humanities major
curl -X POST "http://localhost:5000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_profile": {
      "gpa": 3.9,
      "major": "English Literature",
      "interests": ["Writing", "Research", "Education"],
      "year": "junior"
    }
  }'

# Expected Response (200 OK):
{
  "recommendations": [...],
  "total": 8
}

# Validation:
✓ Status code: 200
✓ recommendations appropriate for humanities
✓ Different results than Test 4.1 (personalization working)
✓ High GPA reflected in recommendations
```

---

### Category 5: B2B Provider Flows (4 tests)

#### Test 5.1: Provider Registration
```bash
# Register new scholarship provider
curl -X POST "http://localhost:5000/api/v1/partner/register" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Test University Foundation",
    "contact_email": "test@university.edu",
    "contact_name": "Jane Doe",
    "phone": "555-1234"
  }'

# Expected Response (201 Created):
{
  "provider_id": "prov_...",
  "organization_name": "Test University Foundation",
  "status": "pending_verification",
  "message": "Registration successful. Verification email sent."
}

# Validation:
✓ Status code: 201
✓ provider_id assigned
✓ status: "pending_verification"
✓ Confirmation message present
```

#### Test 5.2: Create Scholarship Listing (Provider)
```bash
# Provider creates scholarship listing
# (May require provider authentication - adjust as needed)
curl -X POST "http://localhost:5000/api/v1/provider/scholarships" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <provider_jwt>" \
  -d '{
    "title": "Test Scholarship for Launch Validation",
    "amount": 10000,
    "deadline": "2025-12-31",
    "eligibility": {
      "min_gpa": 3.0,
      "majors": ["Engineering", "Computer Science"],
      "academic_level": ["undergraduate"]
    },
    "description": "Test scholarship for pre-launch validation."
  }'

# Expected Response (201 Created):
{
  "scholarship_id": "sch_...",
  "title": "Test Scholarship for Launch Validation",
  "status": "draft",
  "provider_id": "prov_..."
}

# Validation:
✓ Status code: 201
✓ scholarship_id assigned
✓ status: "draft" (not yet published)
✓ All fields saved correctly
```

#### Test 5.3: Edit Scholarship Listing
```bash
# Update scholarship amount and deadline
curl -X PATCH "http://localhost:5000/api/v1/provider/scholarships/<scholarship_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <provider_jwt>" \
  -d '{
    "amount": 15000,
    "deadline": "2026-01-31"
  }'

# Expected Response (200 OK):
{
  "scholarship_id": "sch_...",
  "amount": 15000,
  "deadline": "2026-01-31",
  "updated_at": "2025-10-04T..."
}

# Validation:
✓ Status code: 200
✓ Changes reflected in response
✓ updated_at timestamp current
✓ Other fields unchanged
```

#### Test 5.4: Provider Dashboard - RBAC Validation
```bash
# Provider A attempts to access Provider B's data (should fail)
curl -X GET "http://localhost:5000/api/v1/provider/scholarships" \
  -H "Authorization: Bearer <provider_A_jwt>"

# Expected Response (200 OK with only Provider A's scholarships):
{
  "scholarships": [
    {
      "scholarship_id": "sch_...",
      "provider_id": "prov_A",
      ...
    }
  ],
  "total": 3
}

# Then attempt to access Provider B's specific scholarship
curl -X GET "http://localhost:5000/api/v1/provider/scholarships/<provider_B_scholarship_id>" \
  -H "Authorization: Bearer <provider_A_jwt>"

# Expected Response (403 Forbidden):
{
  "error": "Forbidden",
  "message": "You do not have permission to access this resource"
}

# Validation:
✓ Provider A sees only their own scholarships
✓ Attempt to access Provider B's data returns 403
✓ RBAC correctly isolates provider data
✓ No data leakage across providers
```

---

## Test Execution Plan

### Step 1: Pre-Flight Checks (5 minutes)
```bash
# Verify WAF patch deployed
curl -s http://localhost:5000/api/v1/auth/login-simple \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}' | jq '.error'
# Should return null or auth error (NOT WAF_SQLI_001)

# Verify environment mode
curl -s http://localhost:5000/api | jq '.environment'
# Should return "production"
```

### Step 2: Execute Tests 1.1-1.3 (Authentication) (15 minutes)
- Run all 3 auth tests
- Save JWT token for subsequent tests
- Save API key for search/recommendations tests
- **Gate:** All 3 tests must pass before proceeding

### Step 3: Execute Tests 2.1-2.2 (Search) (15 minutes)
- Use API key from Test 1.3
- Validate search functionality
- Test filters and pagination

### Step 4: Execute Tests 3.1-3.2 (Eligibility) (15 minutes)
- Test high-match and low-match scenarios
- Verify match score calculations
- Validate reasons/explanations

### Step 5: Execute Tests 4.1-4.2 (Recommendations) (15 minutes)
- Test different user profiles
- Validate personalization algorithm
- Confirm results differ by profile

### Step 6: Execute Tests 5.1-5.4 (B2B) (30 minutes)
- Test provider registration flow
- Create and edit test scholarship
- Validate RBAC and data isolation
- **Note:** May require manual intervention for email verification

### Step 7: Evidence Collection (10 minutes)
- Capture all curl commands and responses
- Screenshot key test results
- Document any failures with full error details

### Step 8: Report Generation (10 minutes)
- Summarize pass/fail status for each test
- Calculate overall pass rate (must be 100%)
- Document any issues found
- Provide recommendations for fixes if needed

**Total Execution Time:** ~2 hours (within SLA)

---

## Acceptance Criteria

### ✅ Gate Requirements (T+4h):
1. **100% pass rate** - All 13 tests must pass
2. **No WAF blocks** - Zero WAF_SQLI_001 errors during test execution
3. **Evidence bundle** - Commands, responses, screenshots for all tests
4. **Performance** - All responses within 2 seconds (P95)
5. **Data integrity** - No data corruption or leakage observed

### ⚠️ If Any Test Fails:
1. Document failure with full error details
2. Open P0 ticket with error reproduction steps
3. Re-run test after fix within the 2-hour window
4. Escalate to CEO if cannot achieve 100% pass rate

---

## Test Environment

**Base URL:** `http://localhost:5000` (local) or `https://scholarship-api-jamarrlmayes.replit.app` (production)  
**Environment Mode:** PRODUCTION  
**Mock Users:** Disabled (production security posture)  
**Database:** PostgreSQL with 15 test scholarships loaded  
**Rate Limiting:** In-memory (Redis unavailable, acceptable for testing)

---

## Evidence Bundle Template

For each test, capture:
```
### Test X.Y: <Test Name>

**Command:**
```bash
<full curl command>
```

**Response:**
```json
<full JSON response>
```

**Status:** ✅ PASS / ❌ FAIL  
**Status Code:** <HTTP status>  
**Response Time:** <milliseconds>  
**Notes:** <any observations>
```

---

## Owner and Timeline

**Primary Owner:** QA Lead  
**Supporting Owners:** Backend Engineer (for issue debugging), DevOps (for environment support)  
**Start Time:** Immediately following WAF patch deployment (T+3h)  
**SLA:** Complete within 2 hours (T+5h)  
**Checkpoint:** T+4h status update to CEO  
**Final Report:** T+5h with evidence bundle

---

**Document Status:** READY FOR EXECUTION  
**Dependencies:** WAF patch deployment  
**Blocker Status:** Waiting on Security Lead (WAF fix)  
**Last Updated:** 2025-10-04 - Pre-Launch Sprint
