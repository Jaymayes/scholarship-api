#!/bin/bash
# POST-REPUBLISH SMOKE TESTS - Gate 0 Validation
# CEO Directive: Execute immediately after Replit republish
# Expected runtime: 30 seconds

set -e  # Exit on any error

BASE_URL="https://scholarship-api-jamarrlmayes.replit.app"
RESULTS_FILE="/tmp/smoke_test_results_$(date +%s).txt"

echo "======================================================================"
echo "SMOKE TESTS - POST-REPUBLISH VALIDATION"
echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "Base URL: $BASE_URL"
echo "======================================================================"
echo ""

# Helper function for test reporting
report_test() {
    local test_num=$1
    local test_name=$2
    local expected=$3
    local actual=$4
    
    echo "TEST $test_num: $test_name"
    echo "Expected: $expected"
    echo "Actual: $actual"
    
    if [[ "$actual" == *"$expected"* ]]; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

FAILED_TESTS=0

# TEST 1: /version endpoint
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 1: /version Endpoint (Gate 0 Requirement)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE
VERSION_RESPONSE=$(curl -s "$BASE_URL/version" 2>&1)
VERSION_HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/version" 2>&1)

echo "HTTP Status: $VERSION_HTTP_CODE" | tee -a $RESULTS_FILE
echo "Response:" | tee -a $RESULTS_FILE
echo "$VERSION_RESPONSE" | jq '.' 2>/dev/null | tee -a $RESULTS_FILE || echo "$VERSION_RESPONSE" | tee -a $RESULTS_FILE

if [ "$VERSION_HTTP_CODE" == "200" ]; then
    echo "✅ PASS: /version endpoint returns 200 OK" | tee -a $RESULTS_FILE
else
    echo "❌ FAIL: Expected 200, got $VERSION_HTTP_CODE" | tee -a $RESULTS_FILE
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a $RESULTS_FILE

# TEST 2: /readyz before JWKS warm
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 2: /readyz JWKS Status (Pre-Warm)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE
READYZ_PRE=$(curl -s "$BASE_URL/readyz" 2>&1)
JWKS_PRE=$(echo "$READYZ_PRE" | jq '.checks.auth_jwks' 2>/dev/null)

echo "JWKS Status (Pre-Warm):" | tee -a $RESULTS_FILE
echo "$JWKS_PRE" | tee -a $RESULTS_FILE

KEYS_LOADED_PRE=$(echo "$JWKS_PRE" | jq -r '.keys_loaded' 2>/dev/null)
echo "Keys Loaded: $KEYS_LOADED_PRE" | tee -a $RESULTS_FILE

if [ "$KEYS_LOADED_PRE" == "0" ]; then
    echo "✅ PASS: JWKS degraded before first protected request (expected)" | tee -a $RESULTS_FILE
else
    echo "⚠️ INFO: JWKS already warm (keys_loaded=$KEYS_LOADED_PRE)" | tee -a $RESULTS_FILE
fi
echo "" | tee -a $RESULTS_FILE

# TEST 3: Protected endpoint - COLD START (triggers lazy init)
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 3: Protected Endpoint - Cold Start (Lazy JWKS Init)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE

START_TIME=$(date +%s%3N)
COLD_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
    -H "Authorization: Bearer fake.invalid.token" \
    "$BASE_URL/api/v1/scholarships/SCH-001" 2>&1)
END_TIME=$(date +%s%3N)

COLD_HTTP_CODE=$(echo "$COLD_RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
COLD_TIME=$(echo "$COLD_RESPONSE" | grep "TIME_TOTAL:" | cut -d':' -f2)
COLD_TIME_MS=$(echo "$COLD_TIME * 1000" | bc)

echo "HTTP Status: $COLD_HTTP_CODE" | tee -a $RESULTS_FILE
echo "Latency: ${COLD_TIME}s (${COLD_TIME_MS}ms)" | tee -a $RESULTS_FILE

# Extract response body (everything before HTTP_CODE line)
COLD_BODY=$(echo "$COLD_RESPONSE" | sed '/HTTP_CODE:/,$d')
echo "Response:" | tee -a $RESULTS_FILE
echo "$COLD_BODY" | jq '.' 2>/dev/null | tee -a $RESULTS_FILE || echo "$COLD_BODY" | tee -a $RESULTS_FILE

if [ "$COLD_HTTP_CODE" == "401" ]; then
    echo "✅ PASS: Protected endpoint returns 401 (JWT validation working)" | tee -a $RESULTS_FILE
else
    echo "⚠️ INFO: Expected 401, got $COLD_HTTP_CODE" | tee -a $RESULTS_FILE
fi

# Check if latency is reasonable for cold start (< 500ms including JWKS fetch)
COLD_TIME_INT=$(printf "%.0f" "$COLD_TIME_MS")
if [ "$COLD_TIME_INT" -lt 500 ]; then
    echo "✅ PASS: Cold start latency ${COLD_TIME_MS}ms < 500ms threshold" | tee -a $RESULTS_FILE
else
    echo "⚠️ WARN: Cold start latency ${COLD_TIME_MS}ms > 500ms (includes JWKS fetch)" | tee -a $RESULTS_FILE
fi
echo "" | tee -a $RESULTS_FILE

# Small delay to ensure JWKS cache is populated
sleep 2

# TEST 4: /readyz after JWKS warm
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 4: /readyz JWKS Status (Post-Warm)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE
READYZ_POST=$(curl -s "$BASE_URL/readyz" 2>&1)
JWKS_POST=$(echo "$READYZ_POST" | jq '.checks.auth_jwks' 2>/dev/null)

echo "JWKS Status (Post-Warm):" | tee -a $RESULTS_FILE
echo "$JWKS_POST" | tee -a $RESULTS_FILE

KEYS_LOADED_POST=$(echo "$JWKS_POST" | jq -r '.keys_loaded' 2>/dev/null)
JWKS_STATUS=$(echo "$JWKS_POST" | jq -r '.status' 2>/dev/null)

echo "Keys Loaded: $KEYS_LOADED_POST" | tee -a $RESULTS_FILE
echo "Status: $JWKS_STATUS" | tee -a $RESULTS_FILE

if [ "$KEYS_LOADED_POST" -ge 1 ] 2>/dev/null; then
    echo "✅ PASS: JWKS cache loaded (keys_loaded >= 1)" | tee -a $RESULTS_FILE
else
    echo "❌ FAIL: JWKS cache not loaded (keys_loaded=$KEYS_LOADED_POST)" | tee -a $RESULTS_FILE
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a $RESULTS_FILE

# TEST 5: Protected endpoint - WARM (cache hit)
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 5: Protected Endpoint - Warm (JWKS Cache Hit)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE

WARM_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
    -H "Authorization: Bearer fake.invalid.token" \
    "$BASE_URL/api/v1/scholarships/SCH-001" 2>&1)

WARM_HTTP_CODE=$(echo "$WARM_RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
WARM_TIME=$(echo "$WARM_RESPONSE" | grep "TIME_TOTAL:" | cut -d':' -f2)
WARM_TIME_MS=$(echo "$WARM_TIME * 1000" | bc)

echo "HTTP Status: $WARM_HTTP_CODE" | tee -a $RESULTS_FILE
echo "Latency: ${WARM_TIME}s (${WARM_TIME_MS}ms)" | tee -a $RESULTS_FILE

# Extract response body
WARM_BODY=$(echo "$WARM_RESPONSE" | sed '/HTTP_CODE:/,$d')
echo "Response:" | tee -a $RESULTS_FILE
echo "$WARM_BODY" | jq '.' 2>/dev/null | tee -a $RESULTS_FILE || echo "$WARM_BODY" | tee -a $RESULTS_FILE

if [ "$WARM_HTTP_CODE" == "401" ]; then
    echo "✅ PASS: Protected endpoint returns 401 (cache hit)" | tee -a $RESULTS_FILE
else
    echo "⚠️ INFO: Expected 401, got $WARM_HTTP_CODE" | tee -a $RESULTS_FILE
fi

# Check P95 SLO compliance (≤120ms)
WARM_TIME_INT=$(printf "%.0f" "$WARM_TIME_MS")
if [ "$WARM_TIME_INT" -le 120 ]; then
    echo "✅ PASS: Warm latency ${WARM_TIME_MS}ms ≤ 120ms (P95 SLO compliant)" | tee -a $RESULTS_FILE
else
    echo "❌ FAIL: Warm latency ${WARM_TIME_MS}ms > 120ms (P95 SLO violation)" | tee -a $RESULTS_FILE
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a $RESULTS_FILE

# TEST 6: Latency comparison
echo "======================================================================" | tee -a $RESULTS_FILE
echo "TEST 6: Latency Delta Analysis (Cold vs Warm)" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE

LATENCY_DELTA=$(echo "$COLD_TIME_MS - $WARM_TIME_MS" | bc)
LATENCY_DELTA_INT=$(printf "%.0f" "$LATENCY_DELTA")

echo "Cold Start: ${COLD_TIME_MS}ms" | tee -a $RESULTS_FILE
echo "Warm Request: ${WARM_TIME_MS}ms" | tee -a $RESULTS_FILE
echo "Delta: ${LATENCY_DELTA}ms (one-time JWKS fetch cost)" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

if [ "$LATENCY_DELTA_INT" -gt 0 ]; then
    echo "✅ PASS: Cold start includes JWKS fetch overhead (expected)" | tee -a $RESULTS_FILE
else
    echo "⚠️ INFO: No significant latency delta (JWKS may have been pre-warm)" | tee -a $RESULTS_FILE
fi
echo "" | tee -a $RESULTS_FILE

# SUMMARY
echo "======================================================================" | tee -a $RESULTS_FILE
echo "SMOKE TEST SUMMARY" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE
echo "Total Tests: 6" | tee -a $RESULTS_FILE
echo "Failed Tests: $FAILED_TESTS" | tee -a $RESULTS_FILE

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - Gate 0 Ready" | tee -a $RESULTS_FILE
    EXIT_CODE=0
else
    echo "❌ $FAILED_TESTS TEST(S) FAILED - Review required" | tee -a $RESULTS_FILE
    EXIT_CODE=1
fi
echo "" | tee -a $RESULTS_FILE

# CEO EVIDENCE REQUIREMENTS
echo "======================================================================" | tee -a $RESULTS_FILE
echo "CEO EVIDENCE DELIVERABLES" | tee -a $RESULTS_FILE
echo "======================================================================" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

echo "1. /version JSON Payload:" | tee -a $RESULTS_FILE
echo "$VERSION_RESPONSE" | jq '.' 2>/dev/null | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

echo "2. /readyz auth_jwks Section (Post-Warm):" | tee -a $RESULTS_FILE
echo "$JWKS_POST" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

echo "3. Cold vs Warm Latency:" | tee -a $RESULTS_FILE
echo "   - Cold Start: ${COLD_TIME_MS}ms (includes JWKS fetch)" | tee -a $RESULTS_FILE
echo "   - Warm Request: ${WARM_TIME_MS}ms (cache hit)" | tee -a $RESULTS_FILE
echo "   - Delta: ${LATENCY_DELTA}ms (one-time cost)" | tee -a $RESULTS_FILE
echo "   - P95 SLO: ≤120ms (Warm state compliant: $([ "$WARM_TIME_INT" -le 120 ] && echo "YES" || echo "NO"))" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

echo "Full results saved to: $RESULTS_FILE" | tee -a $RESULTS_FILE
echo "======================================================================"

exit $EXIT_CODE
