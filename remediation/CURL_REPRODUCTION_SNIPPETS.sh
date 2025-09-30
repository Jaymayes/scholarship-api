#!/bin/bash
# cURL Reproduction Snippets for Defects
# Use these to validate fixes and reproduce issues

BASE_URL="https://scholarship-api-jamarrlmayes.replit.app"

echo "=========================================="
echo "CURL REPRODUCTION SNIPPETS"
echo "=========================================="

# DEF-002: Debug Endpoint Exposed
echo -e "\n🔴 DEF-002: Debug Endpoint Exposed"
echo "Test if debug endpoint is still accessible:"
curl -i $BASE_URL/_debug/config

echo -e "\n Expected (AFTER FIX): 401/403/404"
echo " Current (BEFORE FIX): 200 OK with config data"

# DEF-003: WAF Over-Blocking Authenticated Requests
echo -e "\n🔴 DEF-003: WAF Blocking Authenticated Requests"
echo "Step 1: Authenticate"
TOKEN=$(curl -s $BASE_URL/api/v1/auth/login \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

echo -e "\nStep 2: Test search endpoint (should work but fails)"
curl -i $BASE_URL/api/v1/search?q=engineering \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n Expected (AFTER FIX): 200 OK with results"
echo " Current (BEFORE FIX): 403 WAF block"

echo -e "\nStep 3: Test scholarships endpoint"
curl -i $BASE_URL/api/v1/scholarships \
  -H "Authorization: Bearer $TOKEN"

echo -e "\nStep 4: Test eligibility check"
curl -i $BASE_URL/api/v1/eligibility/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "gpa": 3.5,
      "major": "Computer Science",
      "year": "Junior"
    },
    "scholarship_id": "sch_001"
  }'

# DEF-003: WAF Attack Protection (Should Still Block)
echo -e "\n✅ DEF-003: Verify WAF Still Blocks Attacks"
echo "SQL Injection attempt (should be blocked):"
curl -i "$BASE_URL/api/v1/search?q=' OR '1'='1"

echo -e "\nXSS attempt (should be blocked):"
curl -i "$BASE_URL/api/v1/search?q=<script>alert('xss')</script>"

# DEF-001: Concurrent Request Test
echo -e "\n🔴 DEF-001: Concurrent Request Handling"
echo "Testing 10 concurrent requests..."

# Function to make single request
make_request() {
  local id=$1
  local start=$(date +%s%3N)
  local status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/search?q=concurrent_test_$id")
  local end=$(date +%s%3N)
  local duration=$((end - start))
  echo "Request $id: Status $status, Duration ${duration}ms"
}

export -f make_request
export TOKEN BASE_URL

# Run 10 concurrent requests
seq 1 10 | xargs -P 10 -I {} bash -c 'make_request {}'

echo -e "\n Expected (AFTER FIX): 9-10 successful (200)"
echo " Current (BEFORE FIX): 0 successful"

# DEF-005: Rate Limiting Test
echo -e "\n🟡 DEF-005: Rate Limiting (Redis)"
echo "Testing rate limit persistence..."

# Hit rate limit
echo "Making 100 requests quickly..."
for i in {1..100}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/search?q=test")
  
  if [ "$STATUS" -eq 429 ]; then
    echo "✅ Rate limited at request $i"
    break
  fi
done

# Check rate limit headers
echo -e "\nChecking rate limit headers:"
curl -i $BASE_URL/api/v1/search?q=test \
  -H "Authorization: Bearer $TOKEN" \
  | grep -i "X-RateLimit\|Retry-After"

# Performance Test
echo -e "\n⚡ Performance Test (P95 Latency)"
echo "Measuring 20 requests..."

LATENCIES=()
for i in {1..20}; do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/search?q=performance_test" | awk '{print $1*1000}')
  LATENCIES+=($LATENCY)
  echo "Request $i: ${LATENCY}ms"
done

# Calculate P95 (19th value when sorted)
P95=$(echo "${LATENCIES[@]}" | tr ' ' '\n' | sort -n | awk 'NR==19')
echo -e "\nP95 Latency: ${P95}ms (Target: ≤120ms)"

# Security Headers Check
echo -e "\n🔒 Security Headers Validation"
curl -I $BASE_URL/health | grep -E "Strict-Transport-Security|X-Content-Type-Options|X-Frame-Options|Content-Security-Policy"

echo -e "\n=========================================="
echo "REPRODUCTION SNIPPETS COMPLETE"
echo "=========================================="
