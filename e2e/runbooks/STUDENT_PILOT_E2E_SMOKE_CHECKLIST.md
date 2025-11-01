# student_pilot End-to-End Smoke Test Checklist

**Owner:** Frontend DRI  
**Trigger:** After Gate 1 (scholar_auth JWKS) and Gate 2 (scholarship_api /canary) are GREEN  
**Deadline:** T+60 minutes post-trigger  
**Date:** 2025-11-01

---

## 🎯 E2E Smoke Test Acceptance Criteria

### Overall Goals
- Complete user journey: Login → Profile → Recommendations → Search → Application Draft → Logout
- All steps return 200/OK (or appropriate success codes)
- No console errors on critical path
- P95 page transitions ≤120ms
- UX responsive and accessible

### Required Deliverables
1. HAR (HTTP Archive) file or step-by-step curl/HTTP logs
2. Browser console log (must show zero errors on happy path)
3. Performance metrics (TTFB, page load, API P95)
4. Screenshots or video of complete flow (optional but recommended)

---

## 📋 Step-by-Step Smoke Test Procedure

### Prerequisites
- ✅ Gate 1 GREEN: scholar_auth JWKS endpoint returning valid RS256 keys
- ✅ Gate 2 GREEN: scholarship_api /canary returns v2.7 schema with status="ok"
- ✅ Browser: Chrome/Firefox with DevTools open (Network + Console tabs)

---

### Step 1: Login (OIDC Flow via scholar_auth)

**Action:**
1. Navigate to: `https://student-pilot-jamarrlmayes.replit.app`
2. Click "Login" or "Sign In" button
3. Redirected to scholar_auth login page
4. Enter test credentials (non-production user)
5. Submit login form
6. Redirected back to student_pilot with auth callback

**Verification:**
```bash
# After login, session should be established
# Check from browser DevTools or programmatically:

curl -i https://student-pilot-jamarrlmayes.replit.app/api/auth/user \
  -H "Cookie: <session-cookie-from-browser>"
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ JSON contains current user data (id, email, role)
- ✅ Session cookie present (HttpOnly, Secure, SameSite)
- ✅ No console errors during login flow
- ✅ No redirects to error page

**Failure Modes to Check:**
- ❌ 401: JWKS not accessible or token validation failed
- ❌ 500: scholar_auth internal error
- ❌ Redirect loop: CORS or callback URL misconfigured

**Log Requirements:**
- Capture HAR for entire login flow (initial page → auth redirect → callback)
- Screenshot of successful /api/auth/user response

---

### Step 2: Profile Fetch

**Action:**
1. After login, app should auto-fetch user profile
2. Profile page displays user info, saved scholarships, application status

**Verification:**
```bash
# Check profile API endpoint
curl -i https://student-pilot-jamarrlmayes.replit.app/api/profile \
  -H "Cookie: <session-cookie>"
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Profile data loaded (name, email, saved scholarships count)
- ✅ Page renders without layout shift or errors
- ✅ Load time ≤120ms (TTFB target)

**Log Requirements:**
- Network timing for /api/profile request
- Console log (must be error-free)

---

### Step 3: Recommendations (scholarship_sage Integration)

**Action:**
1. Navigate to "Recommendations" or "Matches" section
2. App requests personalized recommendations from scholarship_sage

**Verification:**
```bash
# Check recommendations endpoint (may be proxied through student_pilot)
curl -i https://student-pilot-jamarrlmayes.replit.app/api/recommendations \
  -H "Cookie: <session-cookie>"

# Or direct to scholarship_sage (if exposed):
curl -i https://scholarship-sage-jamarrlmayes.replit.app/api/recommendations \
  -H "Authorization: Bearer <jwt-from-session>"
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Array of recommended scholarships returned (>0 items)
- ✅ Each recommendation includes: id, title, amount, match_score
- ✅ Recommendations render in UI without errors
- ✅ Response time ≤1000ms (scholarship_sage warming: 10s timeout known issue, accept if >10s first time)

**Failure Modes to Check:**
- ❌ 401: Token invalid or JWKS issue
- ❌ 404: scholarship_sage not reachable (ISS-001)
- ❌ Timeout: >10s on first request (warming issue, acceptable for smoke)

**Log Requirements:**
- HAR for recommendations API call
- Screenshot of recommendations rendered in UI

---

### Step 4: Scholarship Search (scholarship_api Integration)

**Action:**
1. Navigate to "Search" or "Browse Scholarships"
2. Enter search query (e.g., "engineering scholarships")
3. Submit search

**Verification:**
```bash
# Check search endpoint (proxied through student_pilot or direct)
curl -i https://student-pilot-jamarrlmayes.replit.app/api/search?q=engineering \
  -H "Cookie: <session-cookie>"

# Or direct to scholarship_api:
curl -i https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=engineering \
  -H "Authorization: Bearer <jwt-from-session>"
```

**Pass Criteria:**
- ✅ HTTP 200 response
- ✅ Search results returned (array of scholarships)
- ✅ Results render in UI with proper formatting
- ✅ No CORS errors in console
- ✅ Response time ≤500ms (scholarship_api target: ≤120ms)

**Log Requirements:**
- Network timing for search API call
- Screenshot of search results page

---

### Step 5: Application Draft (Save/Start Application)

**Action:**
1. Click on a scholarship from search results
2. Click "Apply" or "Save" button
3. App creates draft application or saves scholarship to user profile

**Verification:**
```bash
# Check save/draft endpoint
curl -X POST https://student-pilot-jamarrlmayes.replit.app/api/scholarships/123/save \
  -H "Cookie: <session-cookie>" \
  -H "Content-Type: application/json"
```

**Pass Criteria:**
- ✅ HTTP 200 or 201 response
- ✅ Confirmation message displayed in UI
- ✅ Saved scholarship appears in profile/dashboard
- ✅ No console errors

**Failure Modes to Check:**
- ❌ 401/403: RBAC issue (protected route not accessible)
- ❌ 500: Database write failure

**Log Requirements:**
- HAR for save/draft API call
- Screenshot of confirmation message

---

### Step 6: Logout

**Action:**
1. Click "Logout" button
2. Session cleared, redirected to login/home page

**Verification:**
```bash
# After logout, session should be invalid
curl -i https://student-pilot-jamarrlmayes.replit.app/api/auth/user \
  -H "Cookie: <old-session-cookie>"
```

**Pass Criteria:**
- ✅ HTTP 401 response (session invalid)
- ✅ Redirected to login/home page
- ✅ Cookie cleared or expired
- ✅ No console errors

**Log Requirements:**
- HAR for logout flow
- Screenshot of post-logout state

---

## 📊 Performance Metrics to Capture

### Page Load Metrics (from browser DevTools Performance tab)
- **First Contentful Paint (FCP):** Target ≤1.8s
- **Largest Contentful Paint (LCP):** Target ≤2.5s
- **Time to Interactive (TTI):** Target ≤3.8s
- **Cumulative Layout Shift (CLS):** Target ≤0.1

### API Performance (from Network tab)
- **TTFB (Time to First Byte):** Target ≤120ms
- **P95 API Response Time:** Target ≤250ms (P95 ≤120ms ideal)
- **Auth success rate:** ≥98% (for multiple test users)

### Resource Loading
- **Total page weight:** Target ≤2MB
- **JavaScript bundle size:** Target ≤500KB
- **Images optimized:** WebP or optimized JPEG/PNG

---

## ♿ Accessibility Spot Checks

### Keyboard Navigation
- ✅ Tab through login form (all inputs reachable)
- ✅ Enter key submits forms
- ✅ Escape key closes modals/dropdowns
- ✅ Focus indicators visible

### Screen Reader Compatibility (Basic)
- ✅ Page title describes current view
- ✅ Form labels present and associated with inputs
- ✅ Buttons have descriptive text or aria-label

### Color Contrast (WCAG AA)
- ✅ Text on background meets 4.5:1 ratio (normal text)
- ✅ Large text meets 3:1 ratio
- ✅ Interactive elements have sufficient contrast

---

## 🚨 Failure Modes and Troubleshooting

### Login Fails (401 or Redirect Loop)
**Root Cause:** JWKS not accessible or CORS misconfigured  
**Fix:** Verify Gate 1 GREEN (scholar_auth JWKS), check CORS headers  
**Escalate to:** Auth DRI

### Recommendations Timeout (>10s)
**Root Cause:** scholarship_sage cold start (ISS-001)  
**Fix:** Retry after warm-up period, implement warming strategy  
**Acceptance:** Known issue, acceptable for smoke if succeeds after retry  
**Escalate to:** Sage DRI

### Search Returns No Results
**Root Cause:** scholarship_api database empty or query issue  
**Fix:** Seed test data, verify search endpoint directly  
**Escalate to:** API DRI

### Save/Draft Returns 401/403
**Root Cause:** RBAC middleware blocking request or JWT invalid  
**Fix:** Verify Gate 2 GREEN, check JWT in request headers  
**Escalate to:** API DRI

### Console Errors on Page Load
**Root Cause:** CORS, CSP, or JavaScript errors  
**Fix:** Check CSP headers allow necessary resources, fix CORS  
**Escalate to:** Frontend DRI

---

## 📋 Final Deliverables Checklist

Submit to CEO within T+60 minutes after trigger:

- [ ] HAR file for complete E2E flow (login → logout)
- [ ] Browser console log (screenshot or text export)
- [ ] Performance metrics table (TTFB, LCP, API P95)
- [ ] Screenshots of each step (6 total: login, profile, recommendations, search, save, logout)
- [ ] Accessibility spot check results
- [ ] List of any failures encountered and resolutions
- [ ] Overall PASS/FAIL verdict with rationale

**Report Template:** `e2e/reports/student_pilot/SECTION_7_FOC_REPORT.md`

---

## ✅ E2E Smoke Test GREEN Criteria

All 6 steps complete successfully:
1. ✅ Login: 200 on /api/auth/user
2. ✅ Profile: 200, data loads
3. ✅ Recommendations: 200, >0 items (accept 10s timeout on first request)
4. ✅ Search: 200, results render
5. ✅ Save/Draft: 200/201, confirmation shown
6. ✅ Logout: 401 on subsequent /api/auth/user

**AND:**
- ✅ Zero console errors on critical path
- ✅ Performance within targets (TTFB ≤250ms acceptable, ≤120ms ideal)
- ✅ Basic accessibility checks pass

**Final Action:** Submit complete E2E report with HAR + metrics to CEO for soft launch authorization.

---

## ⏰ Timeline

- **T+0:** Gates 1 & 2 confirmed GREEN (scholar_auth + scholarship_api)
- **T+15:** Begin E2E smoke test (login → profile)
- **T+30:** Complete recommendations + search steps
- **T+45:** Complete save/draft + logout steps
- **T+60:** Submit complete E2E report with deliverables

---

**READY TO EXECUTE IMMEDIATELY AFTER GATES 1 & 2 ARE GREEN.**
