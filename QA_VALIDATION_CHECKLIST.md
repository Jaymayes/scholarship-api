# QA Validation Checklist - T+8:20 Checkpoint

**Incident**: WAF-BLOCK-20251008  
**Validation Time**: T+8:20 (or immediately after Option B deployment)  
**QA Owners**: [INSERT NAMES]  
**Target**: Verify Option B restoration or Replit fix

---

## PRE-VALIDATION SETUP

- [ ] Synthetic monitoring data collected (5 regions)
- [ ] Baseline metrics documented (current 403 rate)
- [ ] Test endpoints identified and accessible
- [ ] SEO crawler user agents prepared
- [ ] Performance monitoring dashboards open

---

## TEST SUITE 1: STATUS CODE CORRECTNESS

### Test 1.1: External Scholarships Endpoint
```bash
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
```
- [ ] **PASS**: HTTP 200 OK returned
- [ ] **FAIL**: HTTP 403 Forbidden (not resolved)
- **Actual Result**: `___________`

### Test 1.2: External Search Endpoint
```bash
curl -v "https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=computer+science"
```
- [ ] **PASS**: HTTP 200 OK returned
- [ ] **FAIL**: HTTP 403 Forbidden (not resolved)
- **Actual Result**: `___________`

### Test 1.3: Credits Package (Control - Should Always Work)
```bash
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/credits/packages
```
- [ ] **PASS**: HTTP 200 OK returned
- [ ] **FAIL**: Regression detected
- **Actual Result**: `___________`

---

## TEST SUITE 2: SEO CRAWLER VALIDATION

### Test 2.1: Googlebot User Agent
```bash
curl -v -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
```
- [ ] **PASS**: HTTP 200 or 304 returned
- [ ] **FAIL**: HTTP 403 or other error
- **Actual Result**: `___________`

### Test 2.2: Bingbot User Agent
```bash
curl -v -H "User-Agent: Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=engineering
```
- [ ] **PASS**: HTTP 200 or 304 returned
- [ ] **FAIL**: HTTP 403 or other error
- **Actual Result**: `___________`

### Test 2.3: Yahoo Slurp User Agent
```bash
curl -v -H "User-Agent: Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)" \
  https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
```
- [ ] **PASS**: HTTP 200 or 304 returned
- [ ] **FAIL**: HTTP 403 or other error
- **Actual Result**: `___________`

---

## TEST SUITE 3: PERFORMANCE VALIDATION

### Test 3.1: P95 Latency Check
```bash
# Run 20 requests and calculate P95
for i in {1..20}; do
  curl -w "%{time_total}\n" -o /dev/null -s \
    https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships
done | sort -n | awk '{all[NR]=$0} END{print all[int(NR*0.95)]}'
```
- [ ] **PASS**: P95 < 120ms (target met)
- [ ] **FAIL**: P95 >= 120ms (performance degradation)
- **P95 Latency**: `___________ms`

### Test 3.2: Error Rate Check
```bash
# Run 100 requests and calculate error rate
total=100
errors=$(for i in $(seq 1 $total); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=test
done | grep -v "^200$" | wc -l)
error_rate=$(awk "BEGIN {printf \"%.2f\", ($errors/$total)*100}")
echo "Error rate: ${error_rate}%"
```
- [ ] **PASS**: Error rate < 0.1% (target met)
- [ ] **FAIL**: Error rate >= 0.1% (reliability issue)
- **Error Rate**: `___________%`

---

## TEST SUITE 4: SECURITY VALIDATION

### Test 4.1: POST Still Requires Auth (Scholarships)
```bash
curl -X POST https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}'
```
- [ ] **PASS**: HTTP 401 or 403 (auth required)
- [ ] **FAIL**: HTTP 200 (security bypass detected)
- **Actual Result**: `___________`

### Test 4.2: PUT Still Requires Auth
```bash
curl -X PUT https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships/test-id \
  -H "Content-Type: application/json" \
  -d '{"title":"Modified"}'
```
- [ ] **PASS**: HTTP 401 or 403 (auth required)
- [ ] **FAIL**: HTTP 200 (security bypass detected)
- **Actual Result**: `___________`

### Test 4.3: DELETE Still Requires Auth
```bash
curl -X DELETE https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships/test-id
```
- [ ] **PASS**: HTTP 401 or 403 (auth required)
- [ ] **FAIL**: HTTP 200 (security bypass detected)
- **Actual Result**: `___________`

---

## TEST SUITE 5: OPTION B SPECIFIC (If Deployed)

### Test 5.1: Bypass Headers Present
```bash
curl -v https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships 2>&1 | grep -i "x-replit-bypass"
```
- [ ] **PRESENT**: X-Replit-Bypass: active (Option B deployed)
- [ ] **ABSENT**: Not present (Replit fix deployed)
- **Result**: `___________`

### Test 5.2: Audit Logs Recording Bypass
```bash
# Check application logs for bypass entries
grep "REPLIT BYPASS" /tmp/logs/*.log | tail -10
```
- [ ] **PASS**: Bypass entries logged with IP, timestamp
- [ ] **FAIL**: No bypass logs found
- **Sample Log**: `___________`

---

## TEST SUITE 6: REGIONAL VALIDATION

### Test 6.1: Multi-Region Success Rate
Review synthetic monitoring logs for all 5 regions:
```bash
tail -20 synthetic_monitoring.log
```

**Region Success Rates**:
- [ ] **us-east**: `_____%` (target: >99%)
- [ ] **us-west**: `_____%` (target: >99%)
- [ ] **eu-west**: `_____%` (target: >99%)
- [ ] **eu-central**: `_____%` (target: >99%)
- [ ] **apac-southeast**: `_____%` (target: >99%)

---

## TEST SUITE 7: CONVERSION FUNNEL

### Test 7.1: Full User Journey
```bash
# Simulate student browsing flow
# 1. Browse scholarships
curl -s https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships | jq '.scholarships[0].id'

# 2. Search for specific scholarship
curl -s "https://scholarship-api-jamarrlmayes.replit.app/api/v1/search?q=engineering" | jq '.results[0].id'

# 3. View credit packages (should always work)
curl -s https://scholarship-api-jamarrlmayes.replit.app/api/v1/credits/packages | jq '.packages[0].credits'
```
- [ ] **PASS**: All steps return valid JSON data
- [ ] **FAIL**: One or more steps fail
- **Results**: `___________`

---

## SUCCESS CRITERIA SUMMARY

**ALL MUST PASS**:
- [ ] External GET /scholarships returns 200 OK
- [ ] External GET /search returns 200 OK
- [ ] SEO crawlers receive 200/304 responses
- [ ] POST/PUT/PATCH still require auth (401/403)
- [ ] P95 latency < 120ms
- [ ] Error rate < 0.1%
- [ ] Multi-region success rate > 99%

**OVERALL VALIDATION RESULT**: [ ] PASS  [ ] FAIL

---

## FAILURE RESPONSE PLAN

**If validation fails**:

1. **Minor Issues** (1-2 tests fail, non-critical):
   - Document issues
   - Create follow-up tasks
   - Proceed with launch (CEO approval required)

2. **Major Issues** (security fail, high error rate, >5 tests fail):
   - **STOP**: Do not proceed
   - Execute escalation path immediately:
     - Extend NO-GO window (2 hours)
     - Activate emergency edge proxy
     - Executive escalation to Replit
     - Prepare Git off-ramp deployment

---

## POST-VALIDATION ACTIONS

After successful validation:
- [ ] Post results in #incidents-p0
- [ ] Update status page (incident resolved)
- [ ] Resume paid campaigns (Marketing)
- [ ] Continue monitoring for 24 hours
- [ ] Schedule incident postmortem
- [ ] Document lessons learned

---

**QA LEAD SIGN-OFF**

Name: `___________`  
Timestamp: `___________`  
Overall Result: `___________`  
Notes: `___________`
