#!/bin/bash

# Quick WAF Test - Verify key acceptance criteria
echo "🛡️ WAF QUICK VALIDATION TEST"
echo "=========================="

BASE_URL="http://localhost:5000"

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="$3"
    
    local status=$(curl -s -o /dev/null -w '%{http_code}' "$url")
    if [ "$status" = "$expected" ]; then
        echo "✅ $name: $status (expected $expected)"
        return 0
    else
        echo "❌ $name: $status (expected $expected)"
        return 1
    fi
}

# Test public endpoints (should work)
test_endpoint "Health Check" "$BASE_URL/health" "200"
test_endpoint "Root Endpoint" "$BASE_URL/" "200"

# Test protected endpoints (should be blocked)
test_endpoint "Protected Search (No Auth)" "$BASE_URL/api/v1/search" "403"
test_endpoint "Protected Scholarships (No Auth)" "$BASE_URL/api/v1/scholarships" "403"

# Test SQL injection blocking
test_endpoint "SQLi Attack Block" "$BASE_URL/api/v1/search?keyword=test%27%20OR%201=1--" "403"

echo ""
echo "WAF Status: Configuration adjusted for public endpoints"