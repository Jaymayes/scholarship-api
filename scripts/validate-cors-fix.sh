#!/bin/bash
# QA FIX Validation Script: CORS Security Hardening
set -e

BASE_URL="http://localhost:5000"
TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
LOG_FILE="cors-validation-${TIMESTAMP}.log"

echo "🔒 CORS Security Validation - QA Fix Verification"
echo "================================================"
echo "Target API: $BASE_URL"
echo "Log file: $LOG_FILE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
    echo "$1"
}

test_cors_policy() {
    log_test "🧪 Testing CORS Policy Implementation"
    
    # Test 1: Malicious origin should be rejected
    log_test "Test 1: Malicious origin preflight request"
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: https://evil.test" \
        -H "Access-Control-Request-Method: GET" \
        2>/dev/null || echo "CURL_FAILED")
    
    if echo "$response" | grep -q "Access-Control-Allow-Origin: https://evil.test"; then
        log_test "❌ FAIL: Malicious origin was allowed"
        echo -e "${RED}❌ CORS Test 1 FAILED: Malicious origin allowed${NC}"
        return 1
    elif echo "$response" | grep -q "Access-Control-Allow-Origin: \*"; then
        log_test "❌ FAIL: Wildcard CORS detected"
        echo -e "${RED}❌ CORS Test 1 FAILED: Wildcard CORS still active${NC}"
        return 1
    else
        log_test "✅ PASS: Malicious origin properly rejected"
        echo -e "${GREEN}✅ CORS Test 1 PASSED: Malicious origin rejected${NC}"
    fi
    
    # Test 2: Legitimate localhost origin should be allowed (dev mode)
    log_test "Test 2: Legitimate localhost origin"
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        2>/dev/null || echo "CURL_FAILED")
    
    if echo "$response" | grep -q "Access-Control-Allow-Origin"; then
        log_test "✅ PASS: Legitimate origin allowed"
        echo -e "${GREEN}✅ CORS Test 2 PASSED: Legitimate origin allowed${NC}"
    else
        log_test "⚠️  WARN: Legitimate origin not explicitly allowed"
        echo -e "${YELLOW}⚠️  CORS Test 2 WARNING: Check origin configuration${NC}"
    fi
    
    # Test 3: Verify no wildcard in any response
    log_test "Test 3: Wildcard detection across endpoints"
    endpoints=("/" "/api/v1/scholarships" "/healthz" "/docs")
    wildcard_found=false
    
    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -i -X GET "$BASE_URL$endpoint" \
            -H "Origin: https://random-test-domain.com" 2>/dev/null || echo "")
        
        if echo "$response" | grep -q "Access-Control-Allow-Origin: \*"; then
            log_test "❌ FAIL: Wildcard found on $endpoint"
            wildcard_found=true
        fi
    done
    
    if [ "$wildcard_found" = true ]; then
        echo -e "${RED}❌ CORS Test 3 FAILED: Wildcard CORS detected on some endpoints${NC}"
        return 1
    else
        log_test "✅ PASS: No wildcard CORS detected"
        echo -e "${GREEN}✅ CORS Test 3 PASSED: No wildcard CORS found${NC}"
    fi
    
    # Test 4: Verify proper headers
    log_test "Test 4: CORS headers validation"
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type,Authorization" \
        2>/dev/null || echo "CURL_FAILED")
    
    if echo "$response" | grep -q "Access-Control-Max-Age:"; then
        log_test "✅ PASS: Max-Age header present"
        echo -e "${GREEN}✅ CORS Test 4a PASSED: Max-Age header configured${NC}"
    else
        log_test "⚠️  WARN: Max-Age header missing"
        echo -e "${YELLOW}⚠️  CORS Test 4a WARNING: Max-Age header not found${NC}"
    fi
    
    if echo "$response" | grep -q "Vary:.*Origin"; then
        log_test "✅ PASS: Vary: Origin header present"
        echo -e "${GREEN}✅ CORS Test 4b PASSED: Vary header configured${NC}"
    else
        log_test "⚠️  INFO: Vary: Origin header not detected (may be handled by framework)"
        echo -e "${YELLOW}ℹ️  CORS Test 4b INFO: Vary header not explicitly set${NC}"
    fi
    
    return 0
}

test_credentials_handling() {
    log_test "🔐 Testing CORS Credentials Handling"
    
    # Test credentials are not enabled by default
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        2>/dev/null || echo "CURL_FAILED")
    
    if echo "$response" | grep -q "Access-Control-Allow-Credentials: true"; then
        log_test "⚠️  WARN: Credentials enabled - ensure this is intentional"
        echo -e "${YELLOW}⚠️  Credentials Test WARNING: CORS credentials enabled${NC}"
    else
        log_test "✅ PASS: Credentials properly disabled by default"
        echo -e "${GREEN}✅ Credentials Test PASSED: No credentials header${NC}"
    fi
}

# Run all tests
echo "Starting CORS validation tests..."
echo ""

overall_result=0

if test_cors_policy; then
    echo -e "${GREEN}CORS Policy Tests: PASSED${NC}"
else
    echo -e "${RED}CORS Policy Tests: FAILED${NC}"
    overall_result=1
fi

echo ""
test_credentials_handling

echo ""
echo "================================================"
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 CORS FIX VALIDATION: ALL TESTS PASSED${NC}"
    log_test "✅ OVERALL RESULT: CORS fix validation successful"
else
    echo -e "${RED}❌ CORS FIX VALIDATION: SOME TESTS FAILED${NC}"
    log_test "❌ OVERALL RESULT: CORS fix validation failed"
fi

echo "Detailed logs saved to: $LOG_FILE"
echo ""

exit $overall_result