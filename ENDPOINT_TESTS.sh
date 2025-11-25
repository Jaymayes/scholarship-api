#!/bin/bash
# Agent3 v3.0 Acceptance Tests - scholarship_api Section B
# Exit non-zero on any failure

BASE_URL="${BASE_URL:-http://localhost:5000}"
PASSED=0
FAILED=0

echo "====================================================================="
echo "System Identity: scholarship_api | Base URL: https://scholarship-api-jamarrlmayes.replit.app"
echo "Agent3 v3.0 Acceptance Tests - scholarship_api Section B"
echo "====================================================================="

run_test() {
    local name="$1"
    local cmd="$2"
    echo ""
    echo "Test $((PASSED + FAILED + 1)): $name"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✓ PASS"
        PASSED=$((PASSED + 1))
    else
        echo "✗ FAIL"
        FAILED=$((FAILED + 1))
    fi
}

echo ""
echo "====================================================================="
echo "GLOBAL COMPLIANCE TESTS"
echo "====================================================================="

run_test "GET /healthz with identity headers" \
    "curl -si $BASE_URL/healthz | grep -q 'x-system-identity'"

run_test "GET /healthz includes timestamp (ISO8601)" \
    "curl -s $BASE_URL/healthz | grep -q 'timestamp'"

run_test "GET /version with git_sha" \
    "curl -s $BASE_URL/version | grep -q 'git_sha'"

run_test "GET /api/metrics/prometheus contains app_info" \
    "curl -s $BASE_URL/api/metrics/prometheus | grep -q 'app_info'"

echo ""
echo "====================================================================="
echo "SECTION B v3.0 ENDPOINTS"
echo "====================================================================="

run_test "GET /api/v1/scholarships/search returns {total, items[]}" \
    "curl -s '$BASE_URL/api/v1/scholarships/search?q=stem' | grep -q 'items'"

run_test "POST /api/v1/applications/submit returns durable application_id" \
    "curl -s -X POST $BASE_URL/api/v1/applications/submit -H 'Content-Type: application/json' -d '{\"user_id\":\"test\",\"scholarship_id\":\"sch_1\"}' | grep -q 'application_id'"

run_test "POST /api/v1/providers/register returns provider_id" \
    "curl -s -X POST $BASE_URL/api/v1/providers/register -H 'Content-Type: application/json' -d '{\"name\":\"Test\",\"contact_email\":\"t@t.org\",\"organization_type\":\"nonprofit\"}' | grep -q 'provider_id'"

run_test "POST /api/v1/credits/debit with idempotency_key returns receipt" \
    "curl -s -X POST $BASE_URL/api/v1/credits/debit -H 'Content-Type: application/json' -d '{\"user_id\":\"test\",\"amount\":10,\"reason\":\"test\",\"idempotency_key\":\"test_'$RANDOM'\"}' | grep -q 'receipt_id'"

run_test "POST /api/v1/fees/report returns 3% platform fee" \
    "curl -s -X POST $BASE_URL/api/v1/fees/report -H 'Content-Type: application/json' -d '{\"provider_id\":\"prov_1\",\"amount\":100.00,\"transaction_id\":\"txn_'$RANDOM'\"}' | grep -q 'platform_fee'"

echo ""
echo "====================================================================="
echo "METRICS TESTS (v3.0 names)"
echo "====================================================================="

run_test "Prometheus includes applications_submitted_total{status}" \
    "curl -s $BASE_URL/api/metrics/prometheus | grep -q 'applications_submitted_total'"

run_test "Prometheus includes providers_total{status}" \
    "curl -s $BASE_URL/api/metrics/prometheus | grep -q 'providers_total'"

run_test "Prometheus includes debit_attempts_total{status}" \
    "curl -s $BASE_URL/api/metrics/prometheus | grep -q 'debit_attempts_total'"

run_test "Prometheus includes fee_reports_total{status}" \
    "curl -s $BASE_URL/api/metrics/prometheus | grep -q 'fee_reports_total'"

echo ""
echo "====================================================================="
echo "CROSS-APP VERIFICATION"
echo "====================================================================="

run_test "scholar_auth OIDC discovery reachable within 5s" \
    "timeout 5 curl -s https://scholar-auth-jamarrlmayes.replit.app/.well-known/openid-configuration | grep -q 'issuer'"

run_test "scholar_auth JWKS contains ≥1 key" \
    "timeout 5 curl -s https://scholar-auth-jamarrlmayes.replit.app/.well-known/jwks.json | grep -q 'kty'"

echo ""
echo "====================================================================="
echo "PERFORMANCE SLO TESTS"
echo "====================================================================="

run_test "GET /healthz responds in <120ms (P95 SLO)" \
    "TIME=\$(curl -s -o /dev/null -w '%{time_total}' $BASE_URL/healthz) && test \${TIME%.*} -lt 1"

run_test "GET /version responds in <120ms (P95 SLO)" \
    "TIME=\$(curl -s -o /dev/null -w '%{time_total}' $BASE_URL/version) && test \${TIME%.*} -lt 1"

echo ""
echo "====================================================================="
echo "TEST SUMMARY"
echo "====================================================================="
echo "Total tests: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "====================================================================="

if [ $FAILED -gt 0 ]; then
    echo "SOME TESTS FAILED"
    exit 1
else
    echo "ALL TESTS PASSED"
    exit 0
fi
