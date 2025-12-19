#!/bin/bash

echo "=============================================="
echo "A2 AUTH E2E SMOKE TEST"
echo "App: scholarship_api"
echo "Base URL: https://scholarship-api-jamarrlmayes.replit.app"
echo "=============================================="
echo ""

BASE_URL="${1:-http://localhost:5000}"
PASS=0
FAIL=0

test_endpoint() {
    local name="$1"
    local expected="$2"
    local url="$3"
    local method="${4:-GET}"
    shift 4
    local extra_args="$@"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" $extra_args "$url" 2>/dev/null)
    
    if [ "$response" == "$expected" ]; then
        echo "[PASS] $name -> $response"
        ((PASS++))
    else
        echo "[FAIL] $name -> $response (expected $expected)"
        ((FAIL++))
    fi
}

echo "1. HEALTH & PUBLIC ROUTES"
echo "-------------------------"
test_endpoint "Health Check" "200" "$BASE_URL/healthz" "GET"
test_endpoint "Public Scholarships" "200" "$BASE_URL/api/v1/scholarships/public" "GET"
test_endpoint "Privacy Page" "200" "$BASE_URL/privacy" "GET"
test_endpoint "Terms Page" "200" "$BASE_URL/terms" "GET"

echo ""
echo "2. PROTECTED ROUTES (expect 401)"
echo "---------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/scholarships/123/save" -H "Content-Type: application/json" -d '{}' 2>/dev/null)
if [ "$response" == "401" ]; then
    echo "[PASS] Save Scholarship (unauth) -> $response"
    ((PASS++))
else
    echo "[FAIL] Save Scholarship (unauth) -> $response (expected 401)"
    ((FAIL++))
fi

response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/credits/balance" 2>/dev/null)
if [ "$response" == "401" ] || [ "$response" == "404" ] || [ "$response" == "422" ]; then
    echo "[PASS] Credits Balance (unauth) -> $response"
    ((PASS++))
else
    echo "[FAIL] Credits Balance (unauth) -> $response (expected 401/404/422)"
    ((FAIL++))
fi

echo ""
echo "3. CORS PREFLIGHT (A3-A8)"
echo "-------------------------"
for origin in "https://scholarship-agent-jamarrlmayes.replit.app" \
              "https://scholarship-sage-jamarrlmayes.replit.app" \
              "https://student-pilot-jamarrlmayes.replit.app" \
              "https://auto-page-maker-jamarrlmayes.replit.app" \
              "https://auto-com-center-jamarrlmayes.replit.app"; do
    app=$(echo "$origin" | sed 's|https://||' | sed 's|-jamarrlmayes.replit.app||')
    response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "$BASE_URL/api/v1/scholarships/public" \
        -H "Origin: $origin" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Authorization, Content-Type" 2>/dev/null)
    if [ "$response" == "200" ]; then
        echo "[PASS] CORS $app -> $response"
        ((PASS++))
    else
        echo "[FAIL] CORS $app -> $response (expected 200)"
        ((FAIL++))
    fi
done

echo ""
echo "4. TELEMETRY ENDPOINTS"
echo "----------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/telemetry/ingest" \
    -H "Content-Type: application/json" \
    -H "x-scholar-protocol: v3.5.1" \
    -H "x-app-label: smoke_test https://test.example.com" \
    -d '{"event_type":"SMOKE_TEST","data":{}}' 2>/dev/null)
if [ "$response" == "200" ] || [ "$response" == "202" ] || [ "$response" == "400" ]; then
    echo "[PASS] Telemetry Ingest -> $response (endpoint reachable)"
    ((PASS++))
else
    echo "[FAIL] Telemetry Ingest -> $response (expected 200/202/400)"
    ((FAIL++))
fi

response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/stats?window=5m" 2>/dev/null)
if [ "$response" == "200" ]; then
    echo "[PASS] Stats Endpoint -> $response"
    ((PASS++))
else
    echo "[FAIL] Stats Endpoint -> $response (expected 200)"
    ((FAIL++))
fi

echo ""
echo "=============================================="
echo "RESULTS: $PASS passed, $FAIL failed"
echo "=============================================="

if [ $FAIL -eq 0 ]; then
    echo "STATUS: HEALTHY"
    exit 0
else
    echo "STATUS: DEGRADED"
    exit 1
fi
