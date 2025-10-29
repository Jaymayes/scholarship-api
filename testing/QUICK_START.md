# Universal E2E Test Framework - Quick Start

**Operator Guide for v2.1 Compact Prompt**

---

## 🚀 Test Any App in 5 Steps

### **Step 1: Copy the Universal Prompt**

Open: `testing/UNIVERSAL_TEST_PROMPT_CEO_APPROVED.txt`  
Copy the entire "UNIVERSAL READ-ONLY E2E TEST PROMPT" section  
Paste into **Agent3 as the system message**

### **Step 2: Run a Single App Test**

**Example:**
```
Test https://scholarship-api-jamarrlmayes.replit.app
```

### **Step 3: Run Gate Tests**

**Examples:**
```
T+24h gate: Test Scholarship API and Scholarship Agent
T+48h gate: Test Student Pilot and Provider Register
T+72h gate: Test all apps
```

### **Step 4: Review YAML Outputs**

Confirm:
- `readiness_score_0_to_5`
- `rollout_gate_status.meets_gate`
- Skim `evidence` and apply `recommended_actions`

### **Step 5: Fix and Retest**

- Address any app scoring 0–2 **immediately**
- For **T+48h**: ensure Student Pilot and Provider Register each score **5**
- For **T+72h**: ensure all apps ≥4, Auto Page Maker =5, Scholar Auth =5

---

## ✅ Gate Pass Criteria

| Gate | Apps | Requirement |
|------|------|-------------|
| **T+24h** | Scholarship API, Scholarship Agent | each ≥ 4 |
| **T+48h** 🔥 | Student Pilot, Provider Register | each = 5 (revenue-critical) |
| **T+72h** 🎯 | All apps | ≥ 4; Auto Page Maker = 5; Scholar Auth = 5 |

---

## 🎯 Ready-to-Use Commands for Agent3

```
Test https://scholarship-api-jamarrlmayes.replit.app
T+24h gate: Test Scholarship API and Scholarship Agent
T+48h gate: Test Student Pilot and Provider Register
T+72h gate: Test all apps
```

---

## 📊 App Keys and URLs

| app_key | App Name | URL |
|---------|----------|-----|
| `scholarship_api` | Scholarship API | https://scholarship-api-jamarrlmayes.replit.app |
| `scholarship_agent` | Scholarship Agent | https://scholarship-agent-jamarrlmayes.replit.app |
| `student_pilot` | Student Pilot | https://student-pilot-jamarrlmayes.replit.app |
| `provider_register` | Provider Register | https://provider-register-jamarrlmayes.replit.app |
| `auto_page_maker` | Auto Page Maker | https://auto-page-maker-jamarrlmayes.replit.app |
| `scholar_auth` | Scholar Auth | https://scholar-auth-jamarrlmayes.replit.app |
| `auto_com_center` | Auto Com Center | https://auto-com-center-jamarrlmayes.replit.app |
| `scholarship_sage` | Scholarship Sage | https://scholarship-sage-jamarrlmayes.replit.app |

---

## 📊 Scoring Rubric

| Score | Meaning | Action |
|-------|---------|--------|
| **5** | ✅ Production-ready | → Proceed |
| **4** | 🟢 Near-ready | → Proceed |
| **3** | 🟡 Usable with issues | → Proceed with monitoring |
| **2** | 🔴 Critical issues | → HOLD |
| **1** | ❌ Major blockers | → STOP |
| **0** | ❌ Not reachable | → STOP |

---

## 📝 Sample YAML Output (v2.1)

```yaml
app_name: Student Pilot
app_key: student_pilot
url_tested: https://student-pilot-jamarrlmayes.replit.app
readiness_score_0_to_5: 5

rollout_gate_status:
  gate: T+48h
  meets_gate: true
  note: Revenue-ready for B2C credit purchases

evidence:
  dns_tls: resolved/valid
  http:
    status_chain: [200]
    ttfb_ms: 94
  security_headers_present:
    - Strict-Transport-Security
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
  console_errors_count: 0
  seo:
    title: "Student Pilot - Scholarship Application Assistant"
    description_present: true
    canonical_present: true
    robots_txt_accessible: true
    sitemap_xml_accessible: false
  notes:
    - Login page loads cleanly
    - Stripe CSP configured correctly
    - Zero console errors

recommended_actions:
  - Add Permissions-Policy header (optional enhancement)
```

---

## 🛡️ Safety Guarantees

✅ **Methods:** GET/HEAD/OPTIONS only  
❌ **Prohibited:** POST/PUT/PATCH/DELETE, forms, auth, PII  
⏱️ **Rate limit:** ≤1 request/path/10s, ≤20 total/app  
🔒 **Respect:** robots.txt, security controls  

---

## ⚠️ Special Case: Auto Com Center

**Auto Com Center is an admin dashboard.**

✅ **Acceptable responses:**
- `200` on login page
- `302/307` redirect to login

🎯 **Focus:**
- Availability (login page loads)
- Security headers
- No critical console errors

❌ **Blocker:**
- `404` on root (current issue)

---

## 📚 Optional: Quick Probe Alternative

**Without Agent3 (30 seconds):**
```bash
cd testing/reporting
python3 generate_readiness_report.py
cat readiness_report_*.md
```

This gives basic checks but less depth than Agent3.

---

## 🎉 Current Status (October 29, 2025)

| Gate | Status | Details |
|------|--------|---------|
| **T+24h** | ✅ **PASSED** | Both apps at 5/5 |
| **T+48h** | ✅ **PASSED** | Both revenue apps at 5/5 🔥 |
| **T+72h** | ⚠️ **On Track** | 6/8 ready (2 fixes needed) |

**Apps needing fixes:**
- 🔴 Auto Com Center (2/5) - HTTP 404 on root
- ❌ Scholarship Sage (0/5) - Not reachable

---

## 🆕 What's New in v2.1

✅ **app_key standardization** - Each app has a consistent key  
✅ **Explicit URL mapping** - Clear host-to-app routing  
✅ **TTFB benchmarks** - Target ~120ms for fast apps  
✅ **Clearer scoring** - Specific criteria per app module  
✅ **Gate auto-routing** - Automatic expansion of gate phrases  

---

**Version:** 2.1 (CEO-Approved Production-Ready)  
**Output Format:** YAML with app_key  
**Alignment:** 72-hour rollout timeline
