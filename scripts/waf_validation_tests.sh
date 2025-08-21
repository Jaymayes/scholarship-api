#!/bin/bash

# WAF Validation Test Suite
# Tests edge-level protection for Phase 1 acceptance criteria

BASE_URL="http://localhost:5000"
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

echo "🛡️ WAF PROTECTION VALIDATION TEST SUITE"
echo "========================================"
echo "Testing WAF edge-level blocking capabilities"
echo ""

run_test() {
    local test_name="$1"
    local expected_status="$2" 
    local url="$3"
    local method="${4:-GET}"
    local headers="${5:-}"
    local data="${6:-}"
    
    TEST_COUNT=$((TEST_COUNT + 1))
    echo "[$TEST_COUNT] Testing: $test_name"
    
    # Build curl command
    local curl_cmd="curl -s -o /dev/null -w '%{http_code}' -X $method"
    
    if [ -n "$headers" ]; then
        curl_cmd="$curl_cmd $headers"
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$url'"
    
    # Execute test
    local actual_status=$(eval $curl_cmd)
    
    if [ "$actual_status" = "$expected_status" ]; then
        echo "   ✅ PASS - Expected: $expected_status, Got: $actual_status"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "   ❌ FAIL - Expected: $expected_status, Got: $actual_status"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
}

echo "=== PHASE 1 ACCEPTANCE TESTS ==="
echo ""

# Test 1: SQL Injection Blocking at Edge
echo "🚨 SQL INJECTION EDGE BLOCKING TESTS"
run_test "SQLi Union Select Attack" "403" "$BASE_URL/api/v1/search?keyword=' UNION SELECT * FROM users--"
run_test "SQLi Boolean Logic Attack" "403" "$BASE_URL/api/v1/search?keyword=' OR 1=1--" 
run_test "SQLi Comment Injection" "403" "$BASE_URL/api/v1/search?keyword=test'; DROP TABLE scholarships; --"
run_test "SQLi Information Schema Attack" "403" "$BASE_URL/api/v1/search?keyword=test' AND (SELECT COUNT(*) FROM information_schema.tables)>0--"

# Test 2: Authorization Header Enforcement
echo "🔒 AUTHORIZATION HEADER ENFORCEMENT TESTS"
run_test "Missing Auth Header - Protected Endpoint" "403" "$BASE_URL/api/v1/scholarships"
run_test "Missing Auth Header - Search Endpoint" "403" "$BASE_URL/api/v1/search"
run_test "Missing Auth Header - Eligibility Endpoint" "403" "$BASE_URL/api/v1/eligibility"

# Test 3: Public Endpoint Access (should still work)
echo "🌐 PUBLIC ENDPOINT ACCESS TESTS"
run_test "Health Check - No Auth Required" "200" "$BASE_URL/health"
run_test "Root Endpoint - No Auth Required" "200" "$BASE_URL/"

# Test 4: XSS Protection
echo "🔍 XSS PROTECTION TESTS"  
run_test "XSS Script Tag Injection" "403" "$BASE_URL/api/v1/search?keyword=<script>alert(1)</script>"
run_test "XSS JavaScript Protocol" "403" "$BASE_URL/api/v1/search?keyword=javascript:alert(1)"
run_test "XSS Event Handler" "403" "$BASE_URL/api/v1/search?keyword=<img onerror=alert(1) src=x>"

# Test 5: Command Injection Protection
echo "💻 COMMAND INJECTION PROTECTION TESTS"
run_test "Command Injection - System Commands" "403" "$BASE_URL/api/v1/search?keyword=test; cat /etc/passwd"
run_test "Command Injection - Shell Operators" "403" "$BASE_URL/api/v1/search?keyword=test | ls -la"
run_test "Command Injection - Process Substitution" "403" "$BASE_URL/api/v1/search?keyword=test \$(whoami)"

# Test 6: Path Traversal Protection  
echo "📁 PATH TRAVERSAL PROTECTION TESTS"
run_test "Path Traversal - Directory Up" "403" "$BASE_URL/../../../etc/passwd"
run_test "Path Traversal - URL Encoded" "403" "$BASE_URL/%2e%2e/%2e%2e/%2e%2e/etc/passwd"

echo "========================================="
echo "🏁 WAF VALIDATION TEST RESULTS"
echo "========================================="
echo "Total Tests: $TEST_COUNT"
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL WAF TESTS PASSED - PHASE 1 COMPLETE!"
    echo "✅ Edge-level SQL injection blocking: ACTIVE"
    echo "✅ Authorization header enforcement: ACTIVE" 
    echo "✅ Attack pattern detection: ACTIVE"
    echo "✅ Public endpoint access: PRESERVED"
    echo ""
    echo "🚀 Ready for Phase 2: Code-Level SQL Injection Testing"
    exit 0
else
    echo "⚠️  WAF VALIDATION FAILED - Phase 1 incomplete"
    echo "❌ $FAIL_COUNT test(s) failed"
    echo "🔧 Review WAF configuration and rule patterns"
    exit 1
fi